from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import desc
from extensions import db
from models import User, Post

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

@profile_bp.route("/<username>")
@login_required
def view_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(desc(Post.timestamp)).all()
    is_self = user.id == current_user.id
    return render_template("profile.html", user=user, posts=posts, edit=False, is_self=is_self)

@profile_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        bio = request.form.get("bio", "").strip()
        if not username:
            flash("Username cannot be empty", "warning")
            return redirect(url_for("profile.edit_profile"))
        # avoid collision with other users
        existing = User.query.filter(User.username==username, User.id!=current_user.id).first()
        if existing:
            flash("Username already taken", "warning")
            return redirect(url_for("profile.edit_profile"))
        current_user.username = username
        current_user.bio = bio
        db.session.commit()
        flash("Profile updated", "success")
        return redirect(url_for("profile.view_profile", username=current_user.username))
    return render_template("profile.html", user=current_user, posts=current_user.posts, edit=True, is_self=True)
