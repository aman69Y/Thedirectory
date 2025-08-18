from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from extensions import db, socketio
from models import Message, ChatMember

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)

@socketio.on('connect')
def on_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')

@socketio.on('message_delivered')
def on_message_delivered(data):
    message_id = data.get('message_id')
    message = Message.query.get(message_id)
    if message and message.status == 'sent':
        message.status = 'delivered'
        db.session.commit()
        sender_room = f'user_{message.sender_id}'
        emit('status_update', {'message_id': message.id, 'status': 'delivered'}, room=sender_room)

@socketio.on('messages_seen')
def on_messages_seen(data):
    chat_id = data.get('chat_id')
    if not current_user.is_authenticated:
        return

    messages_to_update = Message.query.filter(
        Message.chat_id == chat_id,
        Message.sender_id != current_user.id,
        Message.status != 'seen'
    ).all()

    if not messages_to_update:
        return

    sender_id = None
    updated_ids = []
    for message in messages_to_update:
        message.status = 'seen'
        if sender_id is None:
            sender_id = message.sender_id
        updated_ids.append(message.id)

    db.session.commit()

    if sender_id:
        sender_room = f'user_{sender_id}'
        emit('status_update', {'message_ids': updated_ids, 'status': 'seen'}, room=sender_room)
