
import os, json
from flask import Blueprint, render_template, request, current_app, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc
from extensions import db
from models import Post, Like, Comment, Notification, User, Chat, ChatMember, Message

feed_bp = Blueprint('feed', __name__)

ALLOWED_MEDIA = {'png','jpg','jpeg','gif','mp4','webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_MEDIA

@feed_bp.route('/', methods=['GET'])
@login_required
def home():
    friend_ids = {f.id for f in current_user.friends} | {f.id for f in current_user.friend_of}
    visible_ids = list(friend_ids | {current_user.id})
    
    # Limit posts to 20 most recent ones for better performance
    posts = Post.query.filter(Post.user_id.in_(visible_ids), Post.deleted==False).order_by(desc(Post.timestamp)).limit(20).all()
    
    # Fetch recent activities of friends (posts, comments, likes) - limit each type to 2 per friend
    friend_activities = []
    for friend_id in list(friend_ids)[:10]:  # Only check activities for first 10 friends
        friend = User.query.get(friend_id)
        if not friend:
            continue
            
        # Get recent posts (limit to 2)
        recent_posts = Post.query.filter_by(user_id=friend_id, deleted=False).order_by(desc(Post.timestamp)).limit(2).all()
        for post in recent_posts:
            friend_activities.append({
                'user': friend,
                'type': 'post',
                'content': post.content[:100] + '...' if post.content and len(post.content) > 100 else post.content,
                'timestamp': post.timestamp
            })
        
        # Get recent comments (limit to 2)
        recent_comments = Comment.query.filter_by(user_id=friend_id).order_by(desc(Comment.timestamp)).limit(2).all()
        for comment in recent_comments:
            friend_activities.append({
                'user': friend,
                'type': 'comment',
                'content': comment.content[:100] + '...' if comment.content and len(comment.content) > 100 else comment.content,
                'timestamp': comment.timestamp
            })
        
        # Get recent likes (limit to 2)
        recent_likes = Like.query.filter_by(user_id=friend_id).order_by(desc(Like.timestamp)).limit(2).all()
        for like in recent_likes:
            friend_activities.append({
                'user': friend,
                'type': 'like',
                'post': like.post,
                'timestamp': like.timestamp
            })
    
    # Sort activities by timestamp
    friend_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    # Limit to 10 most recent activities
    friend_activities = friend_activities[:10]
    
    return render_template('home.html', posts=posts, friend_activities=friend_activities)

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
        base, ext = os.path.splitext(filename); i=1; unique=filename
        while os.path.exists(os.path.join(media_dir, unique)):
            unique = f"{base}_{i}{ext}"; i+=1
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
        db.session.delete(existing); db.session.commit()
        return jsonify({'ok':True, 'liked':False, 'count': max(0, len(post.likes)-1)})
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post.id))
        if post.user_id != current_user.id:
            n = Notification(user_id=post.user_id, type='like',
                             data=json.dumps({'from': current_user.id, 'from_username': current_user.username,
                                              'post_id': post.id, 'text': f'@{current_user.username} liked your post'}))
            db.session.add(n)
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
        n = Notification(user_id=post.user_id, type='comment',
                         data=json.dumps({'from': current_user.id, 'from_username': current_user.username,
                                          'post_id': post.id, 'text': f'@{current_user.username} commented on your post',
                                          'snippet': content[:120]}))
        db.session.add(n)
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
    post_id = int(request.form.get('post_id',0))
    friend_id = int(request.form.get('friend_id',0))
    post = Post.query.get_or_404(post_id)
    friend = User.query.get_or_404(friend_id)
    if not (friend in current_user.friends or current_user in friend.friends):
        return jsonify({'error':'not_friends'}), 403
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
    m = Message(chat_id=target.id, sender_id=current_user.id, shared_post_id=post.id, content=None)
    db.session.add(m)
    n = Notification(user_id=friend.id, type='share',
                     data=json.dumps({'from': current_user.id, 'from_username': current_user.username,
                                      'post_id': post.id, 'post_author': post.author.username,
                                      'text': f'@{current_user.username} shared a post with you'}))
    db.session.add(n)
    db.session.commit()
    return jsonify({'ok':True})

@feed_bp.get('/friends_list_json')
@login_required
def friends_list_json():
    friends = list(set(current_user.friends + current_user.friend_of))
    return jsonify({'friends': [{'id': u.id, 'username': u.username} for u in friends]})

@feed_bp.get('/post/<int:post_id>/comments_preview')
@login_required
def comments_preview(post_id):
    post = Post.query.get_or_404(post_id)
    comments = post.comments[:3]  # Get first 3 comments
    comment_htmls = [render_template('_comment.html', c=comment) for comment in comments]
    return jsonify({'comments': comment_htmls})
