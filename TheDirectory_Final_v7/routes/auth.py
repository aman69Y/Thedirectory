from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from extensions import db
from models import User
auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed.home'))
    error = None
    if request.method == 'POST':
        identifier = request.form.get('identifier','').strip()
        password = request.form.get('password','')
        user = None
        if identifier:
            user = User.query.filter((User.username==identifier)|(User.email==identifier)).first()
        if user:
            try:
                if user.check_password(password):
                    login_user(user); return redirect(request.args.get('next') or url_for('feed.home'))
                if user.password_hash == password:
                    user.set_password(password); db.session.commit(); login_user(user); return redirect(request.args.get('next') or url_for('feed.home'))
            except Exception as e:
                current_app.logger.exception('Error checking password: %s', e)
        error = 'Invalid email/username or password.'
    return render_template('login.html', error=error)
@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed.home'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        password = request.form.get('password','')
        confirm = request.form.get('confirm_password','')
        if not username or not email or not password:
            error = 'All fields required.'; return render_template('register.html', error=error)
        if password != confirm:
            error = 'Passwords do not match.'; return render_template('register.html', error=error)
        if User.query.filter((User.username==username)|(User.email==email)).first():
            error = 'Username or email already exists.'; return render_template('register.html', error=error)
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user); db.session.commit()
        flash('Account created. Please log in.','success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', error=error)
@auth_bp.route('/logout')
def logout():
    logout_user(); return redirect(url_for('auth.login'))
