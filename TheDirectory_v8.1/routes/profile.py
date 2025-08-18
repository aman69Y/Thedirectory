
import os, json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Post, Notification, FriendRequest, BlockedUser

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')
ALLOWED_AVATAR = {'png','jpg','jpeg','gif'}

def allowed_avatar(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_AVATAR

@profile_bp.route('/<username>')
@login_required
def view_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id, deleted=False).order_by(desc(Post.timestamp)).all()
    is_self = (user.id == current_user.id)
    friend_count = len(user.friends) + len(user.friend_of)
    are_friends = (user in current_user.friends) or (current_user in user.friends)
    
    # Get blocked users for the current user
    blocked_users = BlockedUser.query.filter_by(blocker_id=current_user.id).all()
    
    return render_template('profile.html', user=user, posts=posts, is_self=is_self, 
                         friend_count=friend_count, are_friends=are_friends, blocked_users=blocked_users)

@profile_bp.route('/<username>/search')
@login_required
def profile_search(username):
    q = request.args.get('q','').strip()
    user = User.query.filter_by(username=username).first_or_404()
    if q:
        posts = Post.query.filter(Post.user_id==user.id, Post.content.ilike(f"%{q}%"), Post.deleted==False).order_by(desc(Post.timestamp)).all()
    else:
        posts = Post.query.filter_by(user_id=user.id, deleted=False).order_by(desc(Post.timestamp)).all()
    friend_count = len(user.friends) + len(user.friend_of)
    are_friends = (user in current_user.friends) or (current_user in user.friends)
    return render_template('profile.html', user=user, posts=posts, is_self=(user.id==current_user.id), friend_count=friend_count, are_friends=are_friends)

@profile_bp.route('/edit', methods=['GET','POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        bio = request.form.get('bio','').strip()
        theme = request.form.get('navbar_theme','light')
        chat_theme = request.form.get('chat_theme', 'green')
        file = request.files.get('avatar')

        if username:
            existing = User.query.filter(User.username==username, User.id!=current_user.id).first()
            if existing:
                flash('Username already taken','warning'); return redirect(url_for('profile.edit_profile'))
            current_user.username = username

        current_user.bio = bio
        current_user.navbar_theme = 'dark' if theme == 'dark' else 'light'
        current_user.chat_theme = 'blue' if chat_theme == 'blue' else 'green'

        if file and allowed_avatar(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            base, ext = os.path.splitext(filename); i=1; unique=filename
            while os.path.exists(os.path.join(upload_dir, unique)):
                unique = f"{base}_{i}{ext}"; i+=1
            file.save(os.path.join(upload_dir, unique))
            current_user.avatar_filename = unique

        db.session.commit(); flash('Profile updated','success'); return redirect(url_for('profile.view_profile', username=current_user.username))
    return render_template('profile_edit.html', user=current_user)

@profile_bp.route('/add_friend/<username>', methods=['POST'])
@login_required
def add_friend(username):
    other = User.query.filter_by(username=username).first_or_404()
    if other.id == current_user.id:
        return jsonify({'error':'self'}),400
    exists = FriendRequest.query.filter((FriendRequest.from_id==current_user.id)&(FriendRequest.to_id==other.id)&(FriendRequest.status=='pending')).first()
    if exists:
        return jsonify({'error':'pending'}),400
    req = FriendRequest(from_id=current_user.id, to_id=other.id, status='pending')
    db.session.add(req); db.session.flush()
    n = Notification(user_id=other.id, type='friend_request',
                     data=json.dumps({'from': current_user.id, 'from_username': current_user.username, 'req_id': req.id, 'text': f'@{current_user.username} sent you a friend request'}))
    db.session.add(n)
    db.session.commit()
    return jsonify({'ok':True})


@profile_bp.route('/blocked')
@login_required
def blocked_users():
    blocks = BlockedUser.query.filter_by(blocker_id=current_user.id).all()
    blocked_user_ids = [b.blocked_id for b in blocks]
    users = User.query.filter(User.id.in_(blocked_user_ids)).all()
    return render_template('blocked_users.html', users=users)


@profile_bp.route('/unblock/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    block = BlockedUser.query.filter_by(
        blocker_id=current_user.id,
        blocked_id=user_id
    ).first()

    if block:
        db.session.delete(block)
        db.session.commit()
    
    # Return JSON response for AJAX requests
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'ok': True})
    return redirect(url_for('profile.blocked_users'))
