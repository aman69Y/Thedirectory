from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import User, FriendRequest, Notification
friends_bp = Blueprint('friends', __name__, url_prefix='/friends')
@friends_bp.route('/', methods=['GET'])
@login_required
def list_and_find():
    q = request.args.get('q','').strip()
    if q:
        users = User.query.filter(User.username.ilike(f'%{q}%'), User.id!=current_user.id).all()
    else:
        users = User.query.filter(User.id!=current_user.id).limit(30).all()
    incoming = FriendRequest.query.filter_by(to_id=current_user.id, status='pending').all()
    outgoing = FriendRequest.query.filter_by(from_id=current_user.id, status='pending').all()
    return render_template('friends_find.html', users=users, incoming=incoming, outgoing=outgoing)
@friends_bp.route('/add/<username>')
@login_required
def add_friend(username):
    other = User.query.filter_by(username=username).first_or_404()
    if other.id == current_user.id:
        flash('You cannot add yourself.','warning'); return redirect(url_for('friends.list_and_find'))
    exists = FriendRequest.query.filter(((FriendRequest.from_id==current_user.id)&(FriendRequest.to_id==other.id))|((FriendRequest.from_id==other.id)&(FriendRequest.to_id==current_user.id))).filter(FriendRequest.status=='pending').first()
    if exists:
        flash('Request pending.','info')
    else:
        db.session.add(FriendRequest(from_id=current_user.id, to_id=other.id, status='pending'))
        db.session.add(Notification(user_id=other.id, type='friend_request', data=str(current_user.id)))
        db.session.commit(); flash('Friend request sent.','success')
    return redirect(url_for('friends.list_and_find'))
@friends_bp.route('/accept/<int:req_id>')
@login_required
def accept(req_id):
    fr = FriendRequest.query.get_or_404(req_id)
    if fr.to_id != current_user.id or fr.status != 'pending':
        flash('Not authorized.','danger'); return redirect(url_for('friends.list_and_find'))
    me = current_user; other = fr.sender
    if other not in me.friends: me.friends.append(other)
    if me not in other.friends: other.friends.append(me)
    fr.status = 'accepted'; db.session.add(Notification(user_id=other.id, type='friend_accept', data=str(current_user.id))); db.session.commit(); flash('Friend request accepted.','success')
    return redirect(url_for('friends.list_and_find'))
@friends_bp.route('/decline/<int:req_id>')
@login_required
def decline(req_id):
    fr = FriendRequest.query.get_or_404(req_id)
    if fr.to_id != current_user.id or fr.status != 'pending':
        flash('Not authorized.','danger'); return redirect(url_for('friends.list_and_find'))
    fr.status = 'declined'; db.session.commit(); flash('Friend request declined.','info'); return redirect(url_for('friends.list_and_find'))
@friends_bp.route('/unfriend/<username>')
@login_required
def unfriend(username):
    other = User.query.filter_by(username=username).first_or_404()
    if other in current_user.friends: current_user.friends.remove(other)
    if current_user in other.friends: other.friends.remove(current_user)
    db.session.commit(); flash('Unfriended.','info'); return redirect(url_for('friends.list_and_find'))
