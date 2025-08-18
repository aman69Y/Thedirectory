
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed.home'))
    error = None
    if request.method == 'POST':
        identifier = request.form.get('identifier','').strip()
        password = request.form.get('password','')
        user = User.query.filter((User.email==identifier)|(User.username==identifier)).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('feed.home'))
        else:
            error = 'Invalid email/username or password.'
    return render_template('login.html', error=error)

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed.home'))
    error = None
    if request.method=='POST':
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        confirm = request.form.get('confirm_password','')
        file = request.files.get('profile_pic')
        if not username or not email or not password:
            error = 'All fields are required'
        elif password != confirm:
            error = 'Passwords do not match'
        elif User.query.filter_by(username=username).first():
            error = 'Username already taken'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered'
        else:
            u = User(username=username, email=email); u.set_password(password)
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                os.makedirs(upload_dir, exist_ok=True)
                base, ext = os.path.splitext(filename); i=1; unique=filename
                while os.path.exists(os.path.join(upload_dir, unique)):
                    unique = f"{base}_{i}{ext}"; i+=1
                file.save(os.path.join(upload_dir, unique))
                u.avatar_filename = unique
            db.session.add(u); db.session.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html', error=error)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
