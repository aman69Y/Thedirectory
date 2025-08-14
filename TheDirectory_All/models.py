from datetime import datetime
from flask_login import UserMixin
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
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = relationship("Post", backref="author", cascade="all, delete-orphan")

    # symmetric friendship through association table
    friends = relationship(
        "User",
        secondary=friendships,
        primaryjoin=id == friendships.c.user_id,
        secondaryjoin=id == friendships.c.friend_id,
        backref="friend_of",
    )

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(16), default="pending")  # pending/accepted/declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[from_id])
    receiver = relationship("User", foreign_keys=[to_id])

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    comments = relationship("Comment", backref="post", cascade="all, delete-orphan")
    likes = relationship("Like", backref="post", cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)

    user = relationship("User")

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_like"),)
