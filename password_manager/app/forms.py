from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional
from app.models import User


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    """Form for user registration."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Check if username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')


class PasswordForm(FlaskForm):
    """Form for creating/editing stored passwords."""
    site_name = StringField('Site Name', validators=[
        DataRequired(message='Site name is required'),
        Length(max=128, message='Site name must be less than 128 characters')
    ])
    site_url = StringField('Site URL', validators=[
        Optional(),
        Length(max=256, message='URL must be less than 256 characters')
    ])
    username = StringField('Username/Email', validators=[
        DataRequired(message='Username is required'),
        Length(max=128, message='Username must be less than 128 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    notes = TextAreaField('Notes', validators=[
        Optional()
    ])
    submit = SubmitField('Save')


class EditPasswordForm(FlaskForm):
    """Form for editing stored passwords (password optional)."""
    site_name = StringField('Site Name', validators=[
        DataRequired(message='Site name is required'),
        Length(max=128, message='Site name must be less than 128 characters')
    ])
    site_url = StringField('Site URL', validators=[
        Optional(),
        Length(max=256, message='URL must be less than 256 characters')
    ])
    username = StringField('Username/Email', validators=[
        DataRequired(message='Username is required'),
        Length(max=128, message='Username must be less than 128 characters')
    ])
    password = PasswordField('New Password (leave blank to keep current)', validators=[
        Optional()
    ])
    notes = TextAreaField('Notes', validators=[
        Optional()
    ])
    submit = SubmitField('Update')
