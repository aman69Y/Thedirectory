import os, requests
import requests
from flask import Flask, render_template, request, redirect, url_for, current_app, jsonify
from flask_login import current_user, login_required
from extensions import db, login_manager, socketio

DEFAULT_AVATAR_URL = "https://i.redd.it/why-are-the-blank-profile-pictures-different-v0-x6pug5d3kose1.jpg?width=225&format=pjpg&auto=webp&s=4d79be6d668557f3469afaf57478b2b7ffb78bcf"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///the_directory.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Configure caching
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year for static files
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['DEFAULT_AVATAR'] = DEFAULT_AVATAR_URL
    app.config['GIPHY_API_KEY'] = os.environ.get('L3jRBc4TvrDcVh1PYQDGOt7O38ewU5dv', 'L3jRBc4TvrDcVh1PYQDGOt7O38ewU5dv')

    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'chat_media'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'groups'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    from models import User, Notification  # noqa
    from routes import sockets
    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_config():
        if current_user.is_authenticated:
            unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        else:
            unread_notifications = 0
        return dict(
            config={'DEFAULT_AVATAR': app.config['DEFAULT_AVATAR']},
            unread_notifications=unread_notifications
        )

    from routes.auth import auth_bp
    from routes.feed import feed_bp
    from routes.profile import profile_bp
    from routes.friends import friends_bp
    from routes.messages import messages_bp
    from routes.search import search_bp
    from routes.notifications import notifications_bp
    from routes import sockets

    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(notifications_bp)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('feed.home'))
        return redirect(url_for('auth.login'))

    @app.after_request
    def after_request(response):
        # Add caching headers for static files
        if request.endpoint == 'static':
            response.cache_control.max_age = 31536000  # 1 year
            response.cache_control.public = True
        return response

    @app.route('/giphy_search')
    @login_required
    def giphy_search():
        q = request.args.get('q', '')
        if not q:
            return jsonify({'data': []})
        
        api_key = current_app.config.get('GIPHY_API_KEY')
        # The public beta key 'dc6zaTOxFJmzC' is no longer active.
        if not api_key or api_key == 'dc6zaTOxFJmzC':
            return jsonify({'error': 'Giphy API key is not configured or is invalid.'}), 500

        url = f"https://api.giphy.com/v1/gifs/search"
        params = {'api_key': api_key, 'q': q, 'limit': 24, 'rating': 'pg'}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            return jsonify({'error': str(e)}), 500

    return app

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)
