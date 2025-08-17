
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, Chat, ChatMember, Message, Notification, BlockedUser
from werkzeug.utils import secure_filename
import os, json

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

ALLOWED_CHAT_MEDIA = {'png','jpg','jpeg','gif','mp4','webm','mp3','wav','pdf','doc','docx','ppt','pptx','xls','xlsx','zip','rar','txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_CHAT_MEDIA

def ensure_member(chat_id, user_id):
    return ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id).first() is not None

@messages_bp.route('/')
@login_required
def index():
    member_chats = ChatMember.query.filter_by(user_id=current_user.id).all()
    chat_ids = [m.chat_id for m in member_chats]
    blocked_by_me = [b.blocked_id for b in BlockedUser.query.filter_by(blocker_id=current_user.id).all()]
    blocked_me = [b.blocker_id for b in BlockedUser.query.filter_by(blocked_id=current_user.id).all()]
    blocked_users = set(blocked_by_me + blocked_me)

    chats = Chat.query.filter(Chat.id.in_(chat_ids)).order_by(Chat.created_at.desc()).all()
    friends = list(set(current_user.friends + current_user.friend_of))
    display = []
    for c in chats:
        info = {'chat': c, 'is_group': c.is_group, 'name': c.name, 'avatar': c.group_avatar}
        if not c.is_group:
            other = None
            for m in c.members:
                if m.user_id != current_user.id:
                    other = m.user; break
            if other:
                if other.id in blocked_users:
                    continue  # Skip chats with blocked users
                info['name'] = other.username
                info['avatar'] = other.avatar_filename
                info['other_id'] = other.id
        display.append(info)
    return render_template('messages.html', chats=display, friends=friends)

@messages_bp.route('/start/<int:user_id>', methods=['GET', 'POST'])
@login_required
def start_dm(user_id):
    is_blocked = BlockedUser.query.filter(
        ((BlockedUser.blocker_id == current_user.id) & (BlockedUser.blocked_id == user_id)) |
        ((BlockedUser.blocker_id == user_id) & (BlockedUser.blocked_id == current_user.id))
    ).first()

    if is_blocked:
        abort(403)

    other = User.query.get_or_404(user_id)
    
    # Check if they are friends
    are_friends = (other in current_user.friends) or (current_user in other.friends)
    
    if request.method == 'POST':
        # If they are not friends, create a message request instead
        if not are_friends:
            # Check if a message request already exists
            existing_request = FriendRequest.query.filter(
                (FriendRequest.from_id == current_user.id) & 
                (FriendRequest.to_id == other.id) & 
                (FriendRequest.status == 'message_request')
            ).first()
            
            if existing_request:
                flash('Message request already sent', 'warning')
                return redirect(url_for('profile.view_profile', username=other.username))
            
            # Create a message request (similar to friend request but with different status)
            msg_request = FriendRequest(from_id=current_user.id, to_id=other.id, status='message_request')
            db.session.add(msg_request)
            db.session.flush()
            
            # Create notification for the message request
            n = Notification(user_id=other.id, type='message_request',
                             data=json.dumps({'from': current_user.id, 'from_username': current_user.username, 'req_id': msg_request.id, 'text': f'@{current_user.username} wants to message you'}))
            db.session.add(n)
            db.session.commit()
            
            flash('Message request sent. You can message once they accept.', 'info')
            return redirect(url_for('profile.view_profile', username=other.username))
    
    # For friends or GET requests, proceed with normal DM creation
    dms = Chat.query.filter_by(is_group=False).all()
    target = None
    for ch in dms:
        mids = [m.user_id for m in ch.members]
        if set(mids) == set([current_user.id, other.id]):
            target = ch; break
    if not target:
        target = Chat(is_group=False, name=None, created_by=current_user.id)
        db.session.add(target); db.session.flush()
        db.session.add_all([ChatMember(chat_id=target.id, user_id=current_user.id), ChatMember(chat_id=target.id, user_id=other.id)])
        db.session.commit()
    return redirect(url_for('messages.chat', chat_id=target.id))

@messages_bp.route('/group/create', methods=['GET','POST'])
@login_required
def create_group():
    if request.method=='POST':
        name = request.form.get('name','').strip(); members = request.form.getlist('members')
        file = request.files.get('group_avatar')
        chat = Chat(is_group=True, name=name, created_by=current_user.id)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'groups')
            os.makedirs(upload_dir, exist_ok=True)
            base, ext = os.path.splitext(filename); i=1; unique=filename
            while os.path.exists(os.path.join(upload_dir, unique)):
                unique = f"{base}_{i}{ext}"; i+=1
            file.save(os.path.join(upload_dir, unique))
            chat.group_avatar = unique
        db.session.add(chat); db.session.flush()
        db.session.add(ChatMember(chat_id=chat.id, user_id=current_user.id))
        for uid in members:
            try:
                uid_int = int(uid)
                if uid_int != current_user.id:
                    db.session.add(ChatMember(chat_id=chat.id, user_id=uid_int))
            except: continue
        db.session.commit(); return redirect(url_for('messages.chat', chat_id=chat.id))
    friends = list(set(current_user.friends + current_user.friend_of)); return render_template('group_create.html', friends=friends)

@messages_bp.route('/chat/<int:chat_id>')
@login_required
def chat(chat_id):
    if not ensure_member(chat_id, current_user.id): abort(403)
    chat = Chat.query.get_or_404(chat_id)
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.asc()).all()
    members = [m.user for m in chat.members]
    return render_template('chat.html', chat=chat, messages=messages, members=members, BlockedUser=BlockedUser)

@messages_bp.post('/api/send')
@login_required
def api_send():
    chat_id = int(request.form.get('chat_id','0'))
    content = request.form.get('content','').strip()
    gif = request.form.get('gif','').strip() or None
    if not ensure_member(chat_id, current_user.id): return jsonify({'error':'forbidden'}), 403

    chat = Chat.query.get(chat_id)
    if not chat.is_group:
        other_member = next((m for m in chat.members if m.user_id != current_user.id), None)
        if other_member:
            other_user_id = other_member.user_id
            is_blocked = BlockedUser.query.filter(
                ((BlockedUser.blocker_id == current_user.id) & (BlockedUser.blocked_id == other_user_id)) |
                ((BlockedUser.blocker_id == other_user_id) & (BlockedUser.blocked_id == current_user.id))
            ).first()
            if is_blocked:
                return jsonify({'error': 'user_blocked'}), 403

    file = request.files.get('media')
    media_filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        media_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'chat_media')
        os.makedirs(media_dir, exist_ok=True)
        base, ext = os.path.splitext(filename); i=1; unique=filename
        while os.path.exists(os.path.join(media_dir, unique)):
            unique = f"{base}_{i}{ext}"; i+=1
        file.save(os.path.join(media_dir, unique))
        media_filename = unique

    if not content and not gif and not media_filename:
        return jsonify({'error':'empty'}),400

    m = Message(chat_id=chat_id, sender_id=current_user.id,
                content=(content or None), gif_url=gif, media_filename=media_filename)
    db.session.add(m)
    members = ChatMember.query.filter_by(chat_id=chat_id).all()
    for mem in members:
        if mem.user_id != current_user.id:
            ntext = f"New message from @{current_user.username}"
            n = Notification(user_id=mem.user_id, type='message',
                             data=json.dumps({'from': current_user.id, 'from_username': current_user.username,
                                              'chat_id': chat_id, 'text': ntext}))
            db.session.add(n)
    db.session.commit()
    return jsonify({'ok':True, 'id': m.id})

@messages_bp.post('/api/delete/<int:message_id>')
@login_required
def api_delete(message_id):
    m = Message.query.get_or_404(message_id)
    if m.sender_id != current_user.id: return jsonify({'error':'forbidden'}),403
    db.session.delete(m); db.session.commit(); return jsonify({'ok':True})

@messages_bp.get('/api/messages')
@login_required
def api_messages():
    chat_id = int(request.args.get('chat_id','0')); after_id = int(request.args.get('after_id','0'))
    if not ensure_member(chat_id, current_user.id): return jsonify({'error':'forbidden'}),403
    q = Message.query.filter_by(chat_id=chat_id)
    if after_id: q = q.filter(Message.id>after_id)
    # Limit to 50 most recent messages for better performance
    msgs = q.order_by(Message.id.desc()).limit(50).all()
    # Reverse the order to maintain chronological display
    msgs.reverse()
    data = []
    for m in msgs:
        data.append({
            'id': m.id, 'sender_id': m.sender_id, 'sender_name': m.sender.username,
            'content': m.content, 'gif_url': m.gif_url,
            'media': (m.media_filename or None), 'shared_post_id': m.shared_post_id,
            'timestamp': m.timestamp.isoformat()
        })
    return jsonify({'messages': data})

@messages_bp.route('/group/settings/<int:chat_id>', methods=['GET', 'POST'])
@login_required
def group_settings(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if not chat.is_group or not ensure_member(chat_id, current_user.id):
        abort(403)

    if request.method == 'POST':
        file = request.files.get('group_avatar')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'groups')
            os.makedirs(upload_dir, exist_ok=True)
            base, ext = os.path.splitext(filename)
            i = 1
            unique = filename
            while os.path.exists(os.path.join(upload_dir, unique)):
                unique = f"{base}_{i}{ext}"
                i += 1
            file.save(os.path.join(upload_dir, unique))
            chat.group_avatar = unique
            db.session.commit()
            return redirect(url_for('messages.group_settings', chat_id=chat_id))

    members = [m.user for m in chat.members]
    return render_template('group_settings.html', chat=chat, members=members)

@messages_bp.route('/group/add_members/<int:chat_id>', methods=['GET', 'POST'])
@login_required
def group_add_members(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if not chat.is_group or chat.created_by != current_user.id:
        abort(403)

    if request.method == 'POST':
        members_to_add = request.form.getlist('members')
        for user_id in members_to_add:
            if not ensure_member(chat_id, user_id):
                try:
                    uid_int = int(user_id)
                    if uid_int != current_user.id:
                        db.session.add(ChatMember(chat_id=chat.id, user_id=uid_int))
                except ValueError:
                    continue
        db.session.commit()
        return redirect(url_for('messages.group_settings', chat_id=chat_id))

    current_member_ids = {member.user_id for member in chat.members}
    friends = [friend for friend in list(set(current_user.friends + current_user.friend_of)) if friend.id not in current_member_ids]
    
    return render_template('group_add_members.html', chat=chat, friends=friends)

@messages_bp.route('/group/leave/<int:chat_id>', methods=['POST'])
@login_required
def leave_group(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if not chat.is_group or not ensure_member(chat_id, current_user.id):
        abort(403)

    if chat.created_by == current_user.id:
        db.session.delete(chat)
    else:
        member = ChatMember.query.filter_by(chat_id=chat_id, user_id=current_user.id).first()
        if member:
            db.session.delete(member)
    
    db.session.commit()
    return redirect(url_for('messages.index'))


@messages_bp.route('/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    user_to_block = User.query.get_or_404(user_id)
    if user_to_block.id == current_user.id:
        abort(400)  # Can't block yourself

    existing_block = BlockedUser.query.filter_by(
        blocker_id=current_user.id,
        blocked_id=user_to_block.id
    ).first()

    if existing_block:
        return redirect(request.referrer or url_for('messages.index'))

    new_block = BlockedUser(blocker_id=current_user.id, blocked_id=user_to_block.id)
    db.session.add(new_block)
    db.session.commit()

    return redirect(url_for('messages.index'))
