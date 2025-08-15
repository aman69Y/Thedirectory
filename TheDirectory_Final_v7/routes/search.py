from flask import Blueprint, render_template, request
from flask_login import login_required
from models import User, Post
search_bp = Blueprint('search', __name__)
@search_bp.route('/search')
@login_required
def search():
    q = request.args.get('q','').strip()
    users = []
    posts = []
    if q:
        users = User.query.filter(User.username.ilike(f'%{q}%')).limit(50).all()
        posts = Post.query.filter(Post.content.ilike(f'%{q}%'), Post.deleted==False).limit(200).all()
    return render_template('search_results.html', users=users, posts=posts, query=q)
