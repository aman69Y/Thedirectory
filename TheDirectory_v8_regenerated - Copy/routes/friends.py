
import json
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, FriendRequest, Notification

friends_bp = Blueprint('friends', __name__, url_prefix='/friends')

@friends_bp.route('/')
@login_required
def list_and_find():
    q = request.args.get('q','').strip()
    users = User.query
    if q:
        users = users.filter((User.username.ilike(f"%{q}%"))|(User.email.ilike(f"%{q}%")))
    users = users.all()
    received = FriendRequest.query.filter(
        (FriendRequest.to_id == current_user.id) & 
        (FriendRequest.status.in_(['pending', 'message_request']))
    ).all()
    sent = FriendRequest.query.filter_by(from_id=current_user.id, status='pending').all()
    message_requests_sent = FriendRequest.query.filter_by(from_id=current_user.id, status='message_request').all()
    return render_template('friends_find.html', users=users, received=received, sent=sent, message_requests_sent=message_requests_sent)

@friends_bp.post('/accept/<int:req_id>')
@login_required
def accept(req_id):
    fr = FriendRequest.query.get_or_404(req_id)
    if fr.to_id != current_user.id: return jsonify({'error':'forbidden'}),403
    
    # Handle both friend requests and message requests
    if fr.status == 'pending':  # Friend request
        fr.status = 'accepted'
        u = fr.sender; v = fr.receiver
        if v not in u.friends: u.friends.append(v)
        if u not in v.friends: v.friends.append(u)
        
        # Create notification for friend accept
        db.session.add(Notification(user_id=fr.from_id, type='friend_accept',
                                    data=json.dumps({'from': current_user.id, 'from_username': current_user.username,
                                                     'text':'accepted your friend request'})))
    elif fr.status == 'message_request':  # Message request
        fr.status = 'accepted'
        
        # Create notification for message request accept
        db.session.add(Notification(user_id=fr.from_id, type='message_request_accept',
                                    data=json.dumps({'from': current_user.id, 'from_username': current_user.username,
                                                     'text':'accepted your message request'})))
    
    # Mark the corresponding notification as read
    notif_type = 'friend_request' if fr.status == 'accepted' else 'message_request'
    notif = Notification.query.filter_by(user_id=current_user.id, type=notif_type).first()
    if notif:
        notif.is_read = True
    
    db.session.commit()
    
    # Return JSON response for AJAX requests
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'ok': True})
    return redirect(url_for('friends.list_and_find'))
    
    # Return JSON response for AJAX requests
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'ok': True})
    return redirect(url_for('friends.list_and_find'))

@friends_bp.post('/decline/<int:req_id>')
@login_required
def decline(req_id):
    fr = FriendRequest.query.get_or_404(req_id)
    if fr.to_id != current_user.id: return jsonify({'error':'forbidden'}),403
    fr.status = 'declined'
    
    # Mark the corresponding notification as read (either friend or message request)
    notif_type = 'friend_request' if fr.status == 'pending' else 'message_request'
    notif = Notification.query.filter_by(user_id=current_user.id, type=notif_type).first()
    if notif:
        notif.is_read = True
    
    db.session.commit()
    
    # Return JSON response for AJAX requests
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'ok': True})
    return redirect(url_for('friends.list_and_find'))

@friends_bp.get('/list_json')
@login_required
def list_json():
    friends = list(set(current_user.friends + current_user.friend_of))
    return jsonify({'friends': [{'id': u.id, 'username': u.username} for u in friends]})
