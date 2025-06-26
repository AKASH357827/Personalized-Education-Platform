# auth.py
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models import User, db # Correct relative imports
import os  # Import os
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('main.index'))  # Use blueprint name
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate input fields
        errors = []
        if not username or not first_name or not last_name or not email or not password:
            errors.append('All fields marked with * are required')
        if password != confirm_password:
            errors.append('Passwords do not match')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long')

        # Check for existing user
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                errors.append('Username already exists')
            if existing_user.email == email:
                errors.append('Email already registered')

        if errors:
            for error in errors:
                flash(error, 'error')  # Changed 'danger' to 'error' for consistency
            return render_template('register.html')  # Changed from redirect to render_template

        try:
            new_user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError as e:
            db.session.rollback()
            if "Duplicate entry" in str(e):  # Check for duplicate key error
                flash("Registration failed. Username or email already exists.", 'error')
            else:
                flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {str(e)}")
            return render_template('register.html')

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {str(e)}")
            return render_template('register.html')

    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))