
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

friendships = db.Table(
    "friendships",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("friend_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    UniqueConstraint("user_id", "friend_id", name="uq_friend_pair")
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, default="")
    avatar_filename = db.Column(db.String(255), nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    navbar_theme = db.Column(db.String(10), default="light")
    chat_theme = db.Column(db.String(10), default="green")

    posts = relationship("Post", backref="author", cascade="all, delete-orphan")
    friends = relationship(
        "User",
        secondary=friendships,
        primaryjoin=id == friendships.c.user_id,
        secondaryjoin=id == friendships.c.friend_id,
        backref="friend_of",
    )
    blocked_users = relationship(
        "BlockedUser",
        foreign_keys="BlockedUser.blocker_id",
        backref="blocker",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(16), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender = relationship("User", foreign_keys=[from_id])
    receiver = relationship("User", foreign_keys=[to_id])

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    media_filename = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    deleted = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    comments = relationship("Comment", backref="post", cascade="all, delete-orphan")
    likes = relationship("Like", backref="post", cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    user = relationship("User")

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_like"),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # 'friend_request', 'friend_accept', 'message', 'share', 'like', 'comment'
    data = db.Column(db.Text, nullable=True)         # JSON string
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    is_group = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    group_avatar = db.Column(db.String(255), nullable=True)
    members = relationship("ChatMember", backref="chat", cascade="all, delete-orphan")
    messages = relationship("Message", backref="chat", cascade="all, delete-orphan")

class ChatMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chat.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_chat_member"),)
    user = relationship("User")

class BlockedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blocker_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    blocked_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("blocker_id", "blocked_id", name="uq_blocked_pair"),)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chat.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)
    media_filename = db.Column(db.String(255), nullable=True)  # uploaded file (any type)
    gif_url = db.Column(db.String(500), nullable=True)
    shared_post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=True)  # for rich share
    deleted = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='sent', nullable=False)  # sent, delivered, seen
    reply_to_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    replied_to = db.relationship('Message', remote_side=[id], backref='replies', lazy=True)

    is_forwarded = db.Column(db.Boolean, default=False)
    forwarded_from_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    forwarded_from = db.relationship('User', foreign_keys=[forwarded_from_id], lazy=True)
    sender = db.relationship("User", foreign_keys=[sender_id])
    shared_post = relationship("Post", foreign_keys=[shared_post_id])
