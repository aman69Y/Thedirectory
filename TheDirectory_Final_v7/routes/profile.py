import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Post
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
    return render_template('profile.html', user=user, posts=posts, is_self=is_self, friend_count=friend_count)
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
    return render_template('profile.html', user=user, posts=posts, is_self=(user.id==current_user.id), friend_count=friend_count)
@profile_bp.route('/edit', methods=['GET','POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        bio = request.form.get('bio','').strip()
        file = request.files.get('avatar')
        if username:
            existing = User.query.filter(User.username==username, User.id!=current_user.id).first()
            if existing:
                flash('Username already taken','warning'); return redirect(url_for('profile.edit_profile'))
            current_user.username = username
        current_user.bio = bio
        if file and allowed_avatar(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            base, ext = os.path.splitext(filename)
            i, unique = 1, filename
            while os.path.exists(os.path.join(upload_dir, unique)):
                unique = f"{base}_{i}{ext}"; i += 1
            file.save(os.path.join(upload_dir, unique))
            current_user.avatar_filename = unique
        db.session.commit(); flash('Profile updated','success'); return redirect(url_for('profile.view_profile', username=current_user.username))
    return render_template('profile_edit.html', user=current_user)
