from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
import re

auth_bp = Blueprint('auth', __name__)

from models import User

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone', '').strip()
        
        # Validation
        errors = []
        
        if not full_name or len(full_name) < 3:
            errors.append('Full name must be at least 3 characters long.')
        
        if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if phone and not re.match(r'^\+?[\d\s-]{10,15}$', phone):
            errors.append('Please enter a valid phone number.')
        
        # Check if email already exists
        mysql = current_app.mysql
        existing_user = User.get_by_email(mysql, email)
        if existing_user:
            errors.append('Email address already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('signup.html')
        
        # Create user
        try:
            user_id = User.create_user(mysql, full_name, email, password, phone)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred during registration: {str(e)}', 'danger')
            return render_template('signup.html')
    
    return render_template('signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')
        
        mysql = current_app.mysql
        user = User.get_by_email(mysql, email)
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('login.html')
            
            login_user(user, remember=remember)
            session['user_id'] = user.user_id
            session['user_name'] = user.full_name
            session['user_role'] = user.role
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect based on role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_agent():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('tickets.user_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    mysql = current_app.mysql
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        errors = []
        
        # Validate name
        if not full_name or len(full_name) < 3:
            errors.append('Full name must be at least 3 characters long.')
        
        # Validate phone if provided
        if phone and not re.match(r'^\+?[\d\s-]{10,15}$', phone):
            errors.append('Please enter a valid phone number.')
        
        # Password change validation
        if new_password:
            if not current_password:
                errors.append('Please enter your current password to change password.')
            elif not current_user.check_password(current_password):
                errors.append('Current password is incorrect.')
            elif len(new_password) < 6:
                errors.append('New password must be at least 6 characters long.')
            elif new_password != confirm_password:
                errors.append('New passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            try:
                cursor = mysql.connection.cursor()
                
                if new_password:
                    from werkzeug.security import generate_password_hash
                    password_hash = generate_password_hash(new_password)
                    cursor.execute("""
                        UPDATE users 
                        SET full_name = %s, phone = %s, password_hash = %s 
                        WHERE user_id = %s
                    """, (full_name, phone, password_hash, current_user.user_id))
                    flash('Profile and password updated successfully!', 'success')
                else:
                    cursor.execute("""
                        UPDATE users 
                        SET full_name = %s, phone = %s 
                        WHERE user_id = %s
                    """, (full_name, phone, current_user.user_id))
                    flash('Profile updated successfully!', 'success')
                
                mysql.connection.commit()
                cursor.close()
                
                session['user_name'] = full_name
                
            except Exception as e:
                mysql.connection.rollback()
                flash(f'An error occurred: {str(e)}', 'danger')
    
    # Get updated user data
    user = User.get_by_id(mysql, current_user.user_id)
    return render_template('profile.html', user=user)