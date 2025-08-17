
import json
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def page():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    processed = []
    for n in notifs:
        try: d = json.loads(n.data or '{}')
        except: d = {'text': n.data or ''}
        processed.append((n, d))
    return render_template('notifications.html', notifications=processed)

@notifications_bp.post('/mark_read/<int:notif_id>')
@login_required
def mark_read(notif_id):
    n = Notification.query.get_or_404(notif_id)
    if n.user_id != current_user.id:
        return jsonify({'error':'forbidden'}),403
    n.is_read = True; db.session.commit(); return jsonify({'ok':True})

@notifications_bp.route('/api/notifications')
@login_required
def api_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).limit(10).all()
    processed = []
    for n in notifs:
        try: d = json.loads(n.data or '{}')
        except: d = {'text': n.data or ''}
        processed.append({
            'id': n.id,
            'type': n.type,
            'timestamp': n.timestamp.isoformat(),
            'is_read': n.is_read,
            'data': d
        })
    return jsonify({'notifications': processed})
