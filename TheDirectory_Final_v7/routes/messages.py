from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, Chat, ChatMember, Message, Notification
from werkzeug.utils import secure_filename
import os
messages_bp = Blueprint('messages', __name__, url_prefix='/messages')
def ensure_member(chat_id, user_id):
    return ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id).first() is not None
@messages_bp.route('/')
@login_required
def index():
    member_chats = ChatMember.query.filter_by(user_id=current_user.id).all()
    chat_ids = [m.chat_id for m in member_chats]
    chats = Chat.query.filter(Chat.id.in_(chat_ids)).order_by(Chat.created_at.desc()).all()
    friends = list(set(current_user.friends + current_user.friend_of))
    display = []
    for c in chats:
        info = {'chat': c, 'is_group': c.is_group, 'name': c.name, 'avatar': c.group_avatar}
        if not c.is_group:
            other = None
            for m in c.members:
                if m.user_id != current_user.id:
                    other = m.user
                    break
            if other:
                info['name'] = other.username
                info['avatar'] = other.avatar_filename
                info['other_id'] = other.id
        display.append(info)
    return render_template('messages.html', chats=display, friends=friends)
@messages_bp.route('/start/<int:user_id>')
@login_required
def start_dm(user_id):
    other = User.query.get_or_404(user_id)
    if other not in current_user.friends and current_user not in other.friends:
        abort(403)
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
        if file:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'groups')
            os.makedirs(upload_dir, exist_ok=True)
            base, ext = os.path.splitext(filename)
            i, unique = 1, filename
            while os.path.exists(os.path.join(upload_dir, unique)):
                unique = f"{base}_{i}{ext}"; i += 1
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
    # only non-deleted messages
    messages = Message.query.filter_by(chat_id=chat_id, deleted=False).order_by(Message.timestamp.asc()).limit(1000).all()
    members = [m.user for m in chat.members]
    return render_template('chat.html', chat=chat, messages=messages, members=members)
@messages_bp.route('/chat/<int:chat_id>/add', methods=['POST'])
@login_required
def add_member(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if not ensure_member(chat_id, current_user.id): abort(403)
    # prevent adding members to private DM chat
    if not chat.is_group:
        abort(403)
    user_id = int(request.form.get('user_id',0))
    if not ensure_member(chat_id, user_id):
        db.session.add(ChatMember(chat_id=chat_id, user_id=user_id))
        db.session.commit()
    return redirect(url_for('messages.chat', chat_id=chat_id))
@messages_bp.route('/chat/<int:chat_id>/avatar', methods=['POST'])
@login_required
def upload_group_avatar(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.created_by != current_user.id:
        abort(403)
    file = request.files.get('group_avatar')
    if file:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'groups')
        os.makedirs(upload_dir, exist_ok=True)
        base, ext = os.path.splitext(filename)
        i, unique = 1, filename
        while os.path.exists(os.path.join(upload_dir, unique)):
            unique = f"{base}_{i}{ext}"; i += 1
        file.save(os.path.join(upload_dir, unique))
        chat.group_avatar = unique
        db.session.commit()
    return redirect(url_for('messages.chat', chat_id=chat_id))
@messages_bp.get('/api/messages')
@login_required
def api_messages():
    chat_id = int(request.args.get('chat_id','0')); after_id = int(request.args.get('after_id','0'))
    if not ensure_member(chat_id, current_user.id): return jsonify({'error':'forbidden'}),403
    q = Message.query.filter_by(chat_id=chat_id, deleted=False)
    if after_id: q = q.filter(Message.id>after_id)
    msgs = q.order_by(Message.id.asc()).limit(500).all()
    data = [{'id': m.id, 'sender_id': m.sender_id, 'sender_name': m.sender.username, 'content': m.content, 'gif_url': m.gif_url, 'timestamp': m.timestamp.isoformat()} for m in msgs]
    return jsonify({'messages': data})
@messages_bp.post('/api/send')
@login_required
def api_send():
    chat_id = int(request.form.get('chat_id','0')); content = request.form.get('content','').strip(); gif = request.form.get('gif','').strip() or None
    if not ensure_member(chat_id, current_user.id): return jsonify({'error':'forbidden'}),403
    if not content and not gif: return jsonify({'error':'empty'}),400
    m = Message(chat_id=chat_id, sender_id=current_user.id, content=content or None, gif_url=gif)
    db.session.add(m)
    members = ChatMember.query.filter_by(chat_id=chat_id).all()
    for mem in members:
        if mem.user_id != current_user.id:
            db.session.add(Notification(user_id=mem.user_id, type='message', data=str(chat_id)))
    db.session.commit(); return jsonify({'ok':True, 'id': m.id})
@messages_bp.post('/api/delete/<int:message_id>')
@login_required
def api_delete(message_id):
    m = Message.query.get_or_404(message_id)
    if m.sender_id != current_user.id: return jsonify({'error':'forbidden'}),403
    # permanently delete message (remove from DB) so no one sees it
    db.session.delete(m); db.session.commit(); return jsonify({'ok':True})
@messages_bp.post('/api/add_member')
@login_required
def api_add_member():
    chat_id = int(request.form.get('chat_id','0')); user_id = int(request.form.get('user_id','0'))
    chat = Chat.query.get_or_404(chat_id)
    if not ensure_member(chat_id, current_user.id): return jsonify({'error':'forbidden'}),403
    if not chat.is_group:
        return jsonify({'error':'cannot_add_to_private'}), 400
    if not ensure_member(chat_id, user_id):
        db.session.add(ChatMember(chat_id=chat_id, user_id=user_id)); db.session.commit()
    return jsonify({'ok':True})
@messages_bp.post('/api/leave/<int:chat_id>')
@login_required
def api_leave(chat_id):
    mem = ChatMember.query.filter_by(chat_id=chat_id, user_id=current_user.id).first_or_404(); db.session.delete(mem); db.session.commit(); return jsonify({'ok':True})
