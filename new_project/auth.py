from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Create a Blueprint for authentication
auth = Blueprint('auth', __name__)

# Initialize LoginManager
login_manager = LoginManager()

# User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Dummy user store (replace with a database in production)
users = {'user@example.com': {'password': 'password'}}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email]['password'] == password:
            user = User(email)
            login_user(user)
            return redirect(url_for('dashboard'))  # Redirect to your dashboard route
        flash('Invalid credentials')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Here you would typically save the user to a database
        users[email] = {'password': password}  # Dummy registration
        flash('Registration successful! You can now log in.')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

# Initialize login view
login_manager.login_view = 'auth.login' 