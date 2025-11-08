from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from models import User
from flask import current_app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.get_by_email(current_app.mysql, email)
        
        if user and user.check_password(password):
            login_user(user)
            session['user_id'] = user.user_id
            session['user_name'] = user.full_name
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            if user.is_agent():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('tickets.user_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not full_name or not email or not password:
            flash('Full name, email and password are required.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if len(full_name) < 3:
            flash('Full name must be at least 3 characters.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.signup'))
        
        existing_user = User.get_by_email(current_app.mysql, email)
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.signup'))
        
        try:
            mysql = current_app.mysql
            user_id = User.create_user(mysql, full_name, email, password, phone)
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('Error creating account. Please try again.', 'danger')
            return redirect(url_for('auth.signup'))
    
    return render_template('signup.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    mysql = current_app.mysql
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not full_name or len(full_name) < 3:
            flash('Full name must be at least 3 characters.', 'danger')
            return redirect(url_for('auth.profile'))
        
        try:
            cursor = mysql.connection.cursor()
            
            if new_password:
                if not current_user.check_password(current_password):
                    flash('Current password is incorrect.', 'danger')
                    return redirect(url_for('auth.profile'))
                
                if len(new_password) < 6:
                    flash('New password must be at least 6 characters.', 'danger')
                    return redirect(url_for('auth.profile'))
                
                if new_password != confirm_password:
                    flash('Passwords do not match.', 'danger')
                    return redirect(url_for('auth.profile'))
                
                new_hash = generate_password_hash(new_password)
                cursor.execute(
                    "UPDATE users SET full_name = %s, phone = %s, password_hash = %s WHERE user_id = %s",
                    (full_name, phone, new_hash, current_user.user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET full_name = %s, phone = %s WHERE user_id = %s",
                    (full_name, phone, current_user.user_id)
                )
            
            mysql.connection.commit()
            cursor.close()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        
        except Exception as e:
            flash('Error updating profile.', 'danger')
            return redirect(url_for('auth.profile'))
    
    return render_template('profile.html', user=current_user)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))
