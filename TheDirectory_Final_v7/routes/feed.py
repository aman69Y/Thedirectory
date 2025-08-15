import os
from flask import Blueprint, render_template, request, current_app, jsonify, abort, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc
from extensions import db
from models import Post, Like, Comment, Notification, User
feed_bp = Blueprint('feed', __name__)
ALLOWED_MEDIA = {'png','jpg','jpeg','gif','mp4','webm'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_MEDIA
@feed_bp.route('/', methods=['GET'])
@login_required
def home():
    friend_ids = {f.id for f in current_user.friends} | {f.id for f in current_user.friend_of}
    visible_ids = list(friend_ids | {current_user.id})
    posts = Post.query.filter(Post.user_id.in_(visible_ids), Post.deleted==False).order_by(desc(Post.timestamp)).all()
    return render_template('home.html', posts=posts)
@feed_bp.route('/post_ajax', methods=['POST'])
@login_required
def post_ajax():
    content = request.form.get('content','')
    if content:
        content = '\n'.join([line.rstrip() for line in content.strip().split('\n') if line.strip()!=''])
    file = request.files.get('media')
    media_filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        media_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'posts')
        os.makedirs(media_dir, exist_ok=True)
        base, ext = os.path.splitext(filename)
        i, unique = 1, filename
        while os.path.exists(os.path.join(media_dir, unique)):
            unique = f"{base}_{i}{ext}"; i += 1
        file.save(os.path.join(media_dir, unique))
        media_filename = unique
    if not content and not media_filename:
        return jsonify({'error':'empty'}), 400
    p = Post(content=content or None, media_filename=media_filename, user_id=current_user.id)
    db.session.add(p); db.session.commit()
    html = render_template('_post.html', post=p)
    return jsonify({'ok':True, 'html':html, 'post_id':p.id})
@feed_bp.route('/like_ajax/<int:post_id>', methods=['POST'])
@login_required
def like_ajax(post_id):
    post = Post.query.get_or_404(post_id)
    existing = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        db.session.delete(existing); db.session.commit(); return jsonify({'ok':True, 'liked':False, 'count': len(post.likes)-1})
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post.id))
        if post.user_id != current_user.id:
            db.session.add(Notification(user_id=post.user_id, type='like', data=str(post.id)))
        db.session.commit()
        return jsonify({'ok':True, 'liked':True, 'count': len(post.likes)})
@feed_bp.route('/comment_ajax/<int:post_id>', methods=['POST'])
@login_required
def comment_ajax(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('comment','')
    if content:
        content = '\n'.join([line.rstrip() for line in content.strip().split('\n') if line.strip()!=''])
    if not content:
        return jsonify({'error':'empty'}), 400
    c = Comment(content=content, user_id=current_user.id, post_id=post.id)
    db.session.add(c)
    if post.user_id != current_user.id:
        db.session.add(Notification(user_id=post.user_id, type='comment', data=str(post.id)))
    db.session.commit()
    html = render_template('_comment.html', c=c)
    return jsonify({'ok':True, 'html':html})
@feed_bp.route('/delete_post_ajax/<int:post_id>', methods=['POST'])
@login_required
def delete_post_ajax(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id: abort(403)
    post.deleted = True; db.session.commit(); return jsonify({'ok':True})
@feed_bp.route('/delete_comment_ajax/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment_ajax(comment_id):
    c = Comment.query.get_or_404(comment_id)
    if c.user_id != current_user.id: abort(403)
    c.deleted = True; db.session.commit(); return jsonify({'ok':True})

@feed_bp.route('/share_post', methods=['POST'])
@login_required
def share_post():
    # share a post to a friend: create/find DM and add a message linking to post
    post_id = int(request.form.get('post_id',0))
    friend_id = int(request.form.get('friend_id',0))
    post = Post.query.get_or_404(post_id)
    friend = User.query.get_or_404(friend_id)
    # ensure they are friends
    if not (friend in current_user.friends or current_user in friend.friends):
        return jsonify({'error':'not_friends'}), 403
    # find existing DM between two users
    from models import Chat, ChatMember, Message
    dms = Chat.query.filter_by(is_group=False).all()
    target = None
    for ch in dms:
        mids = [m.user_id for m in ch.members]
        if set(mids) == set([current_user.id, friend.id]):
            target = ch; break
    if not target:
        target = Chat(is_group=False, name=None, created_by=current_user.id)
        db.session.add(target); db.session.flush()
        db.session.add_all([ChatMember(chat_id=target.id, user_id=current_user.id), ChatMember(chat_id=target.id, user_id=friend.id)])
        db.session.commit()
    # send message linking to post
    content = f"Shared a post: /profile/{post.author.username}#post-{post.id}"
    m = Message(chat_id=target.id, sender_id=current_user.id, content=content)
    db.session.add(m)
    db.session.add(Notification(user_id=friend.id, type='message', data=str(target.id)))
    db.session.commit()
    return jsonify({'ok':True})

