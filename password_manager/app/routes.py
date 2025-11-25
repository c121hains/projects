from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Password
from app.forms import LoginForm, RegistrationForm, PasswordForm, EditPasswordForm
from app.crypto import encrypt_password, decrypt_password

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Home page - redirects to dashboard if logged in."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('main.login'))
        
        login_user(user)
        next_page = request.args.get('next')
        # Security: only allow relative URLs
        if next_page and not next_page.startswith('/'):
            next_page = None
        return redirect(next_page or url_for('main.dashboard'))
    
    return render_template('login.html', form=form)


@main.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)


@main.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    """Display user's stored passwords."""
    passwords = current_user.passwords.order_by(Password.site_name).all()
    return render_template('dashboard.html', passwords=passwords)


@main.route('/password/new', methods=['GET', 'POST'])
@login_required
def create_password():
    """Create a new stored password."""
    form = PasswordForm()
    if form.validate_on_submit():
        encrypted = encrypt_password(form.password.data)
        password = Password(
            site_name=form.site_name.data,
            site_url=form.site_url.data,
            username=form.username.data,
            encrypted_password=encrypted,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(password)
        db.session.commit()
        flash('Password saved successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('password_form.html', form=form, title='Add New Password')


@main.route('/password/<int:id>')
@login_required
def view_password(id):
    """View a stored password."""
    password = Password.query.get_or_404(id)
    
    # Security: ensure user owns this password
    if password.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    decrypted = decrypt_password(password.encrypted_password)
    return render_template('password_view.html', password=password, decrypted_password=decrypted)


@main.route('/password/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_password(id):
    """Edit a stored password."""
    password = Password.query.get_or_404(id)
    
    # Security: ensure user owns this password
    if password.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = EditPasswordForm()
    
    if form.validate_on_submit():
        password.site_name = form.site_name.data
        password.site_url = form.site_url.data
        password.username = form.username.data
        password.notes = form.notes.data
        
        # Only update password if a new one was provided
        if form.password.data:
            password.encrypted_password = encrypt_password(form.password.data)
        
        db.session.commit()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.site_name.data = password.site_name
        form.site_url.data = password.site_url
        form.username.data = password.username
        form.notes.data = password.notes
    
    return render_template('password_form.html', form=form, title='Edit Password', password=password)


@main.route('/password/<int:id>/delete', methods=['POST'])
@login_required
def delete_password(id):
    """Delete a stored password."""
    password = Password.query.get_or_404(id)
    
    # Security: ensure user owns this password
    if password.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.dashboard'))
    
    db.session.delete(password)
    db.session.commit()
    flash('Password deleted successfully!', 'success')
    return redirect(url_for('main.dashboard'))
