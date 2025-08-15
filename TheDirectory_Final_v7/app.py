from flask import Flask
from config import Config
from extensions import db, login_manager

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from routes.auth import auth_bp
    from routes.feed import feed_bp
    from routes.profile import profile_bp
    from routes.friends import friends_bp
    from routes.messages import messages_bp
    from routes.notifications import notifications_bp
    from routes.giphy import giphy_bp
    from routes.search import search_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(giphy_bp)
    app.register_blueprint(search_bp)

    with app.app_context():
        db.create_all()
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
