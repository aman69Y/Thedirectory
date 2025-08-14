from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from sqlalchemy import desc
from extensions import db
from models import Post, Like, Comment

feed_bp = Blueprint("feed", __name__)

@feed_bp.route("/", methods=["GET"])
@login_required
def home():
    # Build feed: your posts + friends (both directions)
    friend_ids = {f.id for f in current_user.friends} | {f.id for f in current_user.friend_of}
    visible_ids = list(friend_ids | {current_user.id})
    posts = Post.query.filter(Post.user_id.in_(visible_ids)).order_by(desc(Post.timestamp)).all()
    return render_template("home.html", posts=posts)

@feed_bp.route("/post", methods=["POST"])
@login_required
def new_post():
    content = request.form.get("content", "").strip()
    if content:
        p = Post(content=content, user_id=current_user.id)
        db.session.add(p)
        db.session.commit()
    return redirect(url_for("feed.home"))

@feed_bp.route("/like/<int:post_id>")
@login_required
def like(post_id):
    existing = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if existing:
        db.session.delete(existing)
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post_id))
    db.session.commit()
    return redirect(request.referrer or url_for("feed.home"))

@feed_bp.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment(post_id):
    content = request.form.get("comment", "").strip()
    if content:
        db.session.add(Comment(content=content, user_id=current_user.id, post_id=post_id))
        db.session.commit()
    return redirect(request.referrer or url_for("feed.home"))
