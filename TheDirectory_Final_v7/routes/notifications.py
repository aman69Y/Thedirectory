from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Notification
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')
@notifications_bp.route('/')
@login_required
def page():
    nots = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).limit(100).all()
    return render_template('notifications.html', notifications=nots)
@notifications_bp.get('/count')
@login_required
def count():
    c = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': c})
@notifications_bp.get('/list')
@login_required
def list_notifs():
    nots = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).limit(100).all()
    data = [{'id': n.id, 'type': n.type, 'data': n.data, 'is_read': n.is_read, 'timestamp': n.timestamp.isoformat()} for n in nots]
    return jsonify({'notifications': data})
@notifications_bp.post('/read/<int:not_id>')
@login_required
def mark_read(not_id):
    n = Notification.query.get_or_404(not_id)
    if n.user_id != current_user.id:
        return jsonify({'error':'forbidden'}), 403
    n.is_read = True; db.session.commit(); return jsonify({'ok':True})
