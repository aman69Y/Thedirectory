
from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import desc
from models import User, Post

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
@login_required
def search():
    q = request.args.get('q','').strip()
    users = []; posts = []
    if q:
        users = User.query.filter(User.username.ilike(f"%{q}%")).all()
        posts = Post.query.filter(Post.deleted==False, Post.content.ilike(f"%{q}%")).order_by(desc(Post.timestamp)).all()
    return render_template('search.html', q=q, users=users, posts=posts)
