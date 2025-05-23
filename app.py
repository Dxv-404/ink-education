from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask import send_from_directory
from pymongo import MongoClient 
import firebase_admin
from firebase_admin import credentials, auth
import os
import re
import requests
from bson import ObjectId
from datetime import datetime, timedelta
import uuid
import json
import base64
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string 

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configuration for image uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Add session recovery middleware
@app.before_request
def check_session():
    # Don't run this middleware for static files
    if request.endpoint == 'static':
        return
        
    # Try to restore session from URL parameter if lost
    if 'user_id' not in session and request.args.get('uid'):
        try:
            user_id = request.args.get('uid')
            user = users_collection.find_one({'_id': ObjectId(user_id)})
            if user:
                # Rebuild the session
                session['user_id'] = user_id
                session['email'] = user.get('email')
                session['username'] = user.get('username')
                session['onboarded'] = user.get('onboarded', False)
                session.permanent = True
                print(f"Restored session from URL param: user_id={user_id}")
        except Exception as e:
            print(f"Error restoring session: {str(e)}")

# Firebase Admin Initialization
cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["ink_database"]
users_collection = db["users"]
widgets_collection = db["widgets"]
calendar_events_collection = db["calendar_events"]
todos_collection = db["todos"]
pet_data_collection = db["pets"]
alarms_collection = db["alarms"]
pomodoro_settings_collection = db["pomodoro_settings"]
dashboard_settings_collection = db["dashboard_settings"]
images_collection = db["images"]

# Create a unique index on username field if it doesn't exist
if 'username_1' not in users_collection.index_information():
    users_collection.create_index([("username", 1)], unique=True)

# GitHub OAuth Settings
GITHUB_CLIENT_ID = 'Ov23lia7qa6NQ5JMCnni'
GITHUB_CLIENT_SECRET = '5911513c3094044079f96adadbf0f4ab04f70448'
GITHUB_REDIRECT_URI = 'http://localhost:5000/github-callback'

# Spotify API Settings
SPOTIFY_CLIENT_ID = 'a4e7a4e363a2452f89d0508972a8de20'
SPOTIFY_CLIENT_SECRET = '1cad1fccf34a44029c38744b3a06acc9'
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5000/spotify'

# Firebase API Key
FIREBASE_API_KEY = "AIzaSyDEN8QcSiao1sTFX1-8uyViDZOiCkNGyo8"

# Utility - Email Validation
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# Utility - Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Placeholder images for marketplace listings without custom images
def get_placeholder_image(listing_type=None):
    """Return a placeholder image based on listing type"""
    
    # Simple mapping of types to single placeholder images
    placeholders = {
        'notes': '/static/marketplace/placeholders/notes.jpg',
        'template': '/static/marketplace/placeholders/template.jpg',
        'study guide': '/static/marketplace/placeholders/study_guide.jpg',
        'practice tests': '/static/marketplace/placeholders/practice_tests.jpg',
        'service': '/static/marketplace/placeholders/service.jpg',
        'research paper': '/static/marketplace/placeholders/research_paper.jpg'
    }
    
    # Return type-specific placeholder if available, otherwise generic
    if listing_type and listing_type in placeholders:
        return placeholders[listing_type]
    
    return '/static/marketplace/placeholders/generic.jpg'

# In-memory storage for verification codes
verification_codes = {}

def generate_verification_code():
    """Generate a random 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Send verification email with code using Gmail SMTP"""
    print(f"Attempting to send verification email to {email} with code {code}")
    
    # Gmail account credentials
    GMAIL_USER = "no.reply.ink.education@gmail.com"
    GMAIL_APP_PASSWORD = "lahc ehwa wxkk yidm"  # This might be expired or incorrect
    
    # Email content
    subject = "INK - Verify Your Login"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #F7F7F7; padding: 20px; border-radius: 10px;">
            <h2 style="color: #333; text-align: center;">Welcome to INK!</h2>
            <p style="font-size: 16px;">Please use the verification code below to complete your login:</p>
            <div style="background-color: #000; color: #fff; font-size: 24px; font-weight: bold; padding: 15px; text-align: center; margin: 20px 0; letter-spacing: 5px; border-radius: 5px;">
                {code}
            </div>
            <p style="font-size: 14px; color: #666;">This code will expire in 10 minutes.</p>
            <p style="font-size: 14px; color: #666;">If you didn't request this verification, you can ignore this email.</p>
        </div>
    </body>
    </html>
    """
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = email
    msg['Subject'] = subject
    
    # Attach HTML content
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        print("Setting up SMTP connection...")
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)  # Add debugging information
        server.starttls()  # Enable TLS encryption
        
        try:
            print(f"Attempting to login with user: {GMAIL_USER}")
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            print("SMTP login successful")
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"SMTP Authentication Error: {auth_error}")
            return False
        
        # Send email
        print(f"Sending email to {email}...")
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Add these distance calculation helper functions with your other utility functions 
# (near functions like is_valid_email, allowed_file, etc.)

def getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    import math
    
    R = 6371  # Radius of the earth in km
    dLat = deg2rad(lat2 - lat1)
    dLon = deg2rad(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c  # Distance in km
    return d

def deg2rad(deg):
    """Convert degrees to radians"""
    import math
    return deg * (math.pi/180)

@app.route('/')
def home():
    return render_template('loading.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/landing')
def landing():
    return render_template('landing.html')

# Loading to Dashboard route
@app.route('/loading')
def loading_to_dashboard():
    """Show loading screen before redirecting to dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    # Pass redirection information to the template
    return render_template('loading.html', redirect_to='dashboard')

# AJAX Signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    username = data['username']
    password = data['password']
    confirm_password = data['confirm_password']

    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Invalid email format.'})

    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match.'})
    
    # Check if username is already taken
    if users_collection.find_one({'username': username}):
        return jsonify({'success': False, 'message': 'Username already taken.'})

    try:
        # Check if email exists in Firebase
        try:
            auth.get_user_by_email(email)
            return jsonify({'success': False, 'message': 'Email already in use.'})
        except:
            # Email not found, proceed with creating user
            pass
            
        user = auth.create_user(email=email, password=password)

        if not users_collection.find_one({'email': email}):
            # ENSURE email_verified is explicitly set to False for new users
            user_doc = {
                'firebase_uid': user.uid,
                'username': username,
                'email': email,
                'auth_method': 'email_password',
                'onboarded': False,
                'email_verified': False,  # Explicitly set to False
                'coins_balance': 500,
                'created_at': datetime.now()
            }
            inserted = users_collection.insert_one(user_doc)
            
            # Print debug info
            print(f"New user created: {username}, email_verified set to False")
            
            session['user_id'] = str(inserted.inserted_id)
            session['email'] = email
            session['username'] = username
            session.permanent = True  # Make session permanent

        return jsonify({'success': True, 'message': 'Signup successful! Please complete your profile.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# AJAX Login with proper password verification
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data['email']
    password = data['password']

    try:
        # First, determine if input is email or username
        is_email = is_valid_email(username_or_email)
        
        if is_email:
            # Handle email login
            db_user = users_collection.find_one({'email': username_or_email})
            login_email = username_or_email
        else:
            # Handle username login
            db_user = users_collection.find_one({'username': username_or_email})
            if not db_user:
                return jsonify({'success': False, 'message': 'User not found.'})
            login_email = db_user['email']
        
        if not db_user:
            return jsonify({'success': False, 'message': 'User not found in database.'})
            
        # Print user details for debugging
        print(f"User found: {db_user.get('username')}")
        print(f"Auth method: {db_user.get('auth_method', 'not set')}")
        print(f"Email verified: {db_user.get('email_verified')}")

        # Verify credentials with Firebase
        try:
            # Verify password with Firebase REST API
            auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            auth_payload = {
                "email": login_email,
                "password": password,
                "returnSecureToken": True
            }
            
            auth_response = requests.post(auth_url, json=auth_payload)
            if auth_response.status_code != 200:
                auth_error = auth_response.json()
                error_message = auth_error.get('error', {}).get('message', 'Invalid credentials')
                return jsonify({'success': False, 'message': f'Authentication failed: {error_message}'})
                
        except Exception as auth_error:
            print(f"Authentication error: {auth_error}")
            return jsonify({'success': False, 'message': 'Invalid credentials.'})

        # Fix for non-existent email_verified field
        # If email_verified doesn't exist in the document, the get will return None
        # We need to explicitly check for True, treating both None and False as "not verified"
        email_verified = db_user.get('email_verified')
        auth_method = db_user.get('auth_method', 'email_password')
        
        # If email_verified field doesn't exist or is explicitly False
        needs_verification = auth_method == 'email_password' and email_verified is not True
        
        print(f"Needs verification: {needs_verification}")
        
        if needs_verification:
            print("User needs verification - generating code")
            
            # Update user document to ensure email_verified field exists
            users_collection.update_one(
                {'_id': db_user['_id']},
                {'$set': {'email_verified': False}}
            )
            
            # Generate and store verification code
            code = generate_verification_code()
            verification_codes[db_user['email']] = {
                'code': code,
                'expires': datetime.now() + timedelta(minutes=10)
            }
            
            print(f"Generated verification code {code} for {db_user['email']}")
            
            # Send verification email
            email_sent = send_verification_email(db_user['email'], code)
            print(f"Email sending result: {email_sent}")
            
            if email_sent:
                # Store pending login info in session
                session['pending_login'] = {
                    'email': db_user['email'],
                    'username': db_user['username'],
                    'user_id': str(db_user['_id'])
                }
                
                # Clear any existing full login session
                for key in ['email', 'username', 'user_id', 'verify_email']:
                    if key in session:
                        del session[key]
                
                return jsonify({
                    'success': True, 
                    'verify_required': True,
                    'email': db_user['email'],
                    'message': 'Please check your email for verification code'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to send verification email. Please try again.'
                })
                
        # For users already verified or using other auth methods, proceed with login
        print("User verified or using alternate auth method - proceeding with login")
        
        # Authentication successful, set up session
        session['email'] = db_user['email']
        session['username'] = db_user['username']
        session['user_id'] = str(db_user['_id'])
        session.permanent = True  # Make session permanent

        # Record login for streak tracking
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Look for existing login tracking
        login_tracking = db.login_tracking.find_one({'user_id': session['user_id']})
        
        if not login_tracking:
            # First login ever
            db.login_tracking.insert_one({
                'user_id': session['user_id'],
                'current_streak': 1,
                'longest_streak': 1,
                'last_login': today,
                'login_days': [today]
            })
        else:
            # Check if already logged in today
            if login_tracking.get('last_login').date() != today.date():
                # Not logged in today yet
                yesterday = today - timedelta(days=1)
                
                if login_tracking.get('last_login').date() == yesterday.date():
                    # Consecutive day - increment streak
                    new_streak = login_tracking.get('current_streak', 0) + 1
                    db.login_tracking.update_one(
                        {'user_id': session['user_id']},
                        {
                            '$set': {
                                'current_streak': new_streak,
                                'last_login': today,
                                'longest_streak': max(new_streak, login_tracking.get('longest_streak', 0))
                            },
                            '$push': {'login_days': today}
                        }
                    )
                else:
                    # Streak broken - reset to 1
                    db.login_tracking.update_one(
                        {'user_id': session['user_id']},
                        {
                            '$set': {
                                'current_streak': 1,
                                'last_login': today
                            },
                            '$push': {'login_days': today}
                        }
                    )

        # Check if user needs onboarding
        if not db_user.get('onboarded', False):
            return jsonify({'success': True, 'message': 'Login successful!', 'redirect': '/onboarding'})
        else:
            return jsonify({'success': True, 'message': 'Login successful!', 'redirect': '/success'})
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Login failed: {str(e)}'})
    
@app.route('/admin/fix-email-verified', methods=['GET'])
def fix_email_verified():
    """Admin route to fix email_verified field for all users"""
    # This should ideally be protected by admin authentication
    
    # For all email/password users without email_verified field, set it to False
    result = users_collection.update_many(
        {'auth_method': 'email_password', 'email_verified': {'$exists': False}},
        {'$set': {'email_verified': False}}
    )
    
    # For all OAuth users without email_verified field, set it to True
    result2 = users_collection.update_many(
        {'auth_method': {'$ne': 'email_password'}, 'email_verified': {'$exists': False}},
        {'$set': {'email_verified': True}}
    )
    
    return jsonify({
        'success': True,
        'message': f'Fixed {result.modified_count} email/password users and {result2.modified_count} OAuth users'
    })
    
@app.route('/verify-login', methods=['POST'])
def verify_login():
    """Verify login with email code"""
    data = request.get_json()
    email = data.get('email', '')
    code = data.get('code', '')
    
    print(f"Verifying code '{code}' for email '{email}'")
    print(f"Stored verification codes: {verification_codes}")
    
    # Check if verification data exists
    if email not in verification_codes:
        return jsonify({
            'success': False,
            'message': 'Verification expired. Please login again.'
        })
    
    # Check if code matches and is not expired
    verification = verification_codes[email]
    if verification['expires'] < datetime.now():
        # Clean up expired code
        del verification_codes[email]
        return jsonify({
            'success': False,
            'message': 'Verification code expired. Please login again.'
        })
    
    if verification['code'] != code:
        return jsonify({
            'success': False,
            'message': 'Invalid verification code'
        })
    
    # Code is valid, complete login
    pending = session.get('pending_login', {})
    session['email'] = pending.get('email')
    session['username'] = pending.get('username')
    session['user_id'] = pending.get('user_id')
    session['verify_email'] = True  # Remember verification for this session
    session.permanent = True
    
    # Update user's email_verified status in database
    if session['user_id']:
        users_collection.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {'email_verified': True}}
        )
        print(f"Updated email_verified status for user {session['user_id']}")
    
    # Clean up
    del verification_codes[email]
    if 'pending_login' in session:
        del session['pending_login']
    
    # Check if user needs onboarding
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user or not user.get('onboarded', False):
        return jsonify({
            'success': True,
            'message': 'Login verified successfully!',
            'redirect': '/onboarding'
        })
    else:
        return jsonify({
            'success': True,
            'message': 'Login verified successfully!',
            'redirect': '/success'
        })

# Google Login with proper redirection
@app.route('/auth/firebase-login', methods=['POST'])
def firebase_login():
    data = request.get_json()
    id_token = data.get('idToken')
    display_name = data.get('displayName')
    email = data.get('email')

    if not id_token:
        return jsonify({'success': False, 'message': 'No ID token provided'}), 400

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email_verified = decoded_token.get('email_verified', False)

        if not email_verified:
            return jsonify({'success': False, 'message': 'Email not verified.'})

        username = display_name if display_name else email.split('@')[0]
        user_in_db = users_collection.find_one({'email': email})
        is_new_user = False

        if not user_in_db:
            # New user - will need onboarding
            is_new_user = True
            
            # Check if username already exists
            if users_collection.find_one({'username': username}):
                # If username exists, append a number to make it unique
                base_username = username
                counter = 1
                while users_collection.find_one({'username': username}):
                    username = f"{base_username}{counter}"
                    counter += 1
                
            user_doc = {
                'firebase_uid': uid,
                'username': username,
                'email': email,
                'auth_method': 'google',
                'onboarded': False,
                'coins_balance': 500,
                'created_at': datetime.now()
                
            }
            inserted = users_collection.insert_one(user_doc)
            session['user_id'] = str(inserted.inserted_id)
            user_in_db = user_doc  # Set for later onboarding check
        else:
            session['user_id'] = str(user_in_db['_id'])

        session['email'] = email
        session['username'] = username
        # Make session permanent right after login
        session.permanent = True

        # Record login for streak (same as in regular login)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        login_tracking = db.login_tracking.find_one({'user_id': session['user_id']})
        
        if not login_tracking:
            db.login_tracking.insert_one({
                'user_id': session['user_id'],
                'current_streak': 1,
                'longest_streak': 1,
                'last_login': today,
                'login_days': [today]
            })
        else:
            if login_tracking.get('last_login').date() != today.date():
                yesterday = today - timedelta(days=1)
                
                if login_tracking.get('last_login').date() == yesterday.date():
                    new_streak = login_tracking.get('current_streak', 0) + 1
                    db.login_tracking.update_one(
                        {'user_id': session['user_id']},
                        {
                            '$set': {
                                'current_streak': new_streak,
                                'last_login': today,
                                'longest_streak': max(new_streak, login_tracking.get('longest_streak', 0))
                            },
                            '$push': {'login_days': today}
                        }
                    )
                else:
                    db.login_tracking.update_one(
                        {'user_id': session['user_id']},
                        {
                            '$set': {
                                'current_streak': 1,
                                'last_login': today
                            },
                            '$push': {'login_days': today}
                        }
                    )

        # Check if user needs onboarding
        if is_new_user or not user_in_db.get('onboarded', False):
            return jsonify({'success': True, 'message': 'Authentication successful!', 'redirect': '/onboarding'})
        else:
            return jsonify({'success': True, 'message': 'Authentication successful!', 'redirect': '/success'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Dashboard Route with onboarding check
@app.route('/dashboard')
def dashboard():
    # Check multiple sources for user authentication
    user_id = session.get('user_id') or request.args.get('uid') or request.cookies.get('user_id')
    
    if not user_id:
        print("No user ID found in session, URL, or cookies")
        return redirect(url_for('login_page'))
    
    # Log all information to diagnose the issue
    print(f"Session data: {dict(session)}")
    print(f"UID from request args: {request.args.get('uid')}")
    print(f"Cookies: {request.cookies}")
    
    
    # If user_id is in URL but not session, restore session
    if 'user_id' not in session and user_id:
        try:
            user = users_collection.find_one({'_id': ObjectId(user_id)})
            if user:
                session['user_id'] = user_id
                session['email'] = user.get('email')
                session['username'] = user.get('username')
                session['onboarded'] = user.get('onboarded', True)
                session.permanent = True
                print(f"Restored session in dashboard: user_id={user_id}")
        except Exception as e:
            print(f"Error restoring session in dashboard: {str(e)}")
            return redirect(url_for('login_page'))

    # Now get the user using the user_id that should be in session
    try:
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return redirect(url_for('login_page'))
            
        # Handle missing onboarded status
        if not user.get('onboarded', False):
            # If user has GitHub username, they have completed onboarding but flag wasn't set
            if user.get('github_username'):
                users_collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': {'onboarded': True}}
                )
                user['onboarded'] = True
            else:
                print(f"User {user['username']} needs onboarding, redirecting...")
                return redirect(url_for('onboarding'))
            
        # User is authenticated and onboarded, proceed to dashboard
        user['_id'] = str(user['_id'])  # Convert ObjectId to string for JSON serialization
        
        # Get dashboard settings if they exist
        # Get dashboard settings if they exist
        dashboard_settings = dashboard_settings_collection.find_one({'user_id': user_id})
        if dashboard_settings:
            # Create a new dictionary with string conversion for ObjectId
            dashboard_settings_dict = {}
            for key, value in dashboard_settings.items():
                if isinstance(value, ObjectId):
                    dashboard_settings_dict[key] = str(value)
                else:
                    dashboard_settings_dict[key] = value
            user['dashboard_settings'] = dashboard_settings_dict
            
        print(f"Rendering dashboard for user: {user['username']}")
        return render_template('dashboard.html', user=user)
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return redirect(url_for('login_page'))

# View another user's profile
@app.route('/profile/<username>')
def view_profile(username):
    # Check if the requested username exists
    profile_user = users_collection.find_one({'username': username})
    if not profile_user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard'))
    
    # Convert ObjectId to string for JSON serialization
    profile_user['_id'] = str(profile_user['_id'])
    
    # Determine if current user is viewing their own profile
    is_own_profile = False
    if 'user_id' in session:
        current_user_id = session.get('user_id')
        if current_user_id == profile_user['_id']:
            is_own_profile = True
    
    # Get public widgets for this user
    public_widgets = list(widgets_collection.find({
        'user_id': profile_user['_id'], 
        'is_public': True
    }))
    
    # Convert ObjectId to string in widgets
    for widget in public_widgets:
        widget['_id'] = str(widget['_id'])
    
    # Get dashboard settings if they exist
    dashboard_settings = dashboard_settings_collection.find_one({'user_id': profile_user['_id']})
    if dashboard_settings:
        profile_user['dashboard_settings'] = dashboard_settings
    
    return render_template(
        'profile.html', 
        profile_user=profile_user, 
        widgets=public_widgets, 
        is_own_profile=is_own_profile
    )

# Onboarding Route
@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if 'email' not in session or 'user_id' not in session:
        return redirect(url_for('login_page'))

    # Make session permanent EARLY to prevent expiration during OAuth flow
    session.permanent = True
    print(f"Onboarding for user_id={session.get('user_id')}, making session permanent")
    # Check if email is verified
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    
    # For users using email/password auth, require verification
    if user and user.get('auth_method') == 'email_password' and not user.get('email_verified', False):
        flash('Please verify your email before continuing to onboarding.', 'error')
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        university = request.form.get('university')
        department = request.form.get('department')
        year = request.form.get('year')
        skills = request.form.get('skills', '')
        interests = request.form.get('interests', '')
        
        # Process skills and interests into arrays
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        interests_list = [interest.strip() for interest in interests.split(',') if interest.strip()]
        
        # Get user_id from session (primary) or form (backup)
        user_id = session.get('user_id') or request.form.get('user_id')
        if not user_id:
            flash('User identification failed. Please try again.', 'error')
            return redirect(url_for('login_page'))
            
        # Ensure user_id is in session for GitHub redirect
        session['user_id'] = user_id

        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'university': university,
                    'department': department,
                    'year': year,
                    'skills': skills_list,
                    'interests': interests_list,
                    # Don't set onboarded=True yet, we'll do that after GitHub
                }
            }
        )
        
        # Store user data in session to better survive redirects
        session['profile_data'] = {
            'university': university,
            'department': department,
            'year': year
        }
        
        # Redirect to GitHub login directly from server-side
        return redirect(url_for('github_login'))

    return render_template('onboarding.html')

# GitHub OAuth Integration
@app.route('/github-login')
def github_login():
    # Make session permanent
    session.permanent = True
    
    if 'user_id' not in session:
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login_page'))
    
    # Generate state parameter for security
    state = str(uuid.uuid4())
    session['github_oauth_state'] = state
    
    # Store user_id in a dedicated session key for GitHub flow
    user_id = session['user_id']
    session['github_user_id'] = user_id
    print(f"GitHub login for user_id={user_id}, state={state}")
    
    # This function should ONLY redirect to GitHub's OAuth page
    # Pass user_id as state AND as a separate parameter for redundancy
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&scope=read:user&state={state}_{user_id}"
    )
    print(f"Redirecting to GitHub: {github_auth_url}")
    return redirect(github_auth_url)

@app.route('/github-callback')
def github_callback():
    from requests import post, get

    code = request.args.get('code')
    state = request.args.get('state', '')
    
    if not code:
        flash('GitHub authorization failed.', 'error')
        return redirect(url_for('login_page'))

    # Extract user_id from state parameter (format: "uuid_user_id")
    user_id = None
    if '_' in state:
        state_parts = state.split('_', 1)
        auth_state = state_parts[0]
        user_id = state_parts[1]
        print(f"Extracted from state: auth_state={auth_state}, user_id={user_id}")
    
    # Try multiple session recovery methods
    if 'user_id' not in session:
        # First, try to get user_id from the state parameter
        if user_id:
            try:
                user = users_collection.find_one({'_id': ObjectId(user_id)})
                if user:
                    session['user_id'] = user_id
                    session['email'] = user.get('email')
                    session['username'] = user.get('username')
                    session.permanent = True
                    print(f"Restored session from state parameter: user_id={user_id}")
            except Exception as e:
                print(f"Error restoring session from state: {str(e)}")
        
        # If still no session, try from github_user_id in session
        if 'user_id' not in session and 'github_user_id' in session:
            session['user_id'] = session['github_user_id']
            print(f"Restored user_id from github_user_id: {session['github_user_id']}")
    
    # If we still don't have a user_id, redirect to login
    if 'user_id' not in session:
        flash('Session expired. Please log in again to complete GitHub connection.', 'error')
        return redirect(url_for('login_page'))

    # Step 1: Exchange code for access token
    token_response = post('https://github.com/login/oauth/access_token', data={
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code
    }, headers={'Accept': 'application/json'})

    if token_response.status_code != 200:
        flash('Failed to get access token from GitHub.', 'error')
        return redirect(url_for('login_page'))

    access_token = token_response.json().get('access_token')

    # Step 2: Fetch GitHub profile
    user_response = get('https://api.github.com/user', headers={
        'Authorization': f'token {access_token}',
        'Accept': 'application/json'
    })

    if user_response.status_code != 200:
        flash('Failed to fetch GitHub profile.', 'error')
        return redirect(url_for('login_page'))

    github_data = user_response.json()
    github_username = github_data.get('login')
    github_url = github_data.get('html_url')

    if not github_username:
        flash('GitHub login failed.', 'error')
        return redirect(url_for('login_page'))

    # Make the session permanent to prevent it from expiring
    session.permanent = True
    user_id = session['user_id']
    print(f"GitHub callback processing for user_id={user_id}")
    
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login_page'))

    # Update database
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {
            'github_username': github_username,
            'github_url': github_url,
            'onboarded': True
        }}
    )

    # Explicitly set these session variables
    session['onboarded'] = True
    session['github_username'] = github_username
    
    flash('GitHub connected successfully!', 'success')

    # Redirect to success page with user_id in URL parameter
    return redirect(url_for('success', uid=user_id))

# Spotify OAuth Integration
@app.route('/spotify-login')
def spotify_login():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    # Make session permanent to help prevent loss during OAuth redirect
    session.permanent = True
    
    # Include user_id parameter to help recover if session is lost
    user_id_param = f"&state={session['user_id']}" if 'user_id' in session else ""
    
    spotify_auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={SPOTIFY_CLIENT_ID}&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        f"&scope=user-read-private%20user-read-email%20user-read-playback-state"
        f"%20user-modify-playback-state%20user-read-currently-playing"
        f"{user_id_param}"
    )
    return redirect(spotify_auth_url)

@app.route('/spotify')
def spotify_callback():
    code = request.args.get('code')
    state = request.args.get('state')  # This will contain the user_id if we set it
    
    # Try to recover session from state parameter if needed
    if 'user_id' not in session and state:
        try:
            user = users_collection.find_one({'_id': ObjectId(state)})
            if user:
                session['user_id'] = state
                session['email'] = user.get('email')
                session['username'] = user.get('username')
                session['onboarded'] = user.get('onboarded', False)
                session.permanent = True
                print(f"Restored session in Spotify callback: user_id={state}")
        except Exception as e:
            print(f"Error restoring session in Spotify callback: {str(e)}")
    
    if 'user_id' not in session:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login_page'))
    
    if not code:
        flash('Spotify authorization failed.', 'error')
        return redirect(url_for('dashboard'))
    
    # Exchange code for access token
    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    
    token_response = requests.post(token_url, data=token_data)
    
    if token_response.status_code != 200:
        flash('Failed to get access token from Spotify.', 'error')
        return redirect(url_for('dashboard'))
    
    token_info = token_response.json()
    access_token = token_info.get('access_token')
    refresh_token = token_info.get('refresh_token')
    expires_in = token_info.get('expires_in')
    
    # Save token information to user profile
    users_collection.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {
            'spotify_token': access_token,
            'spotify_refresh_token': refresh_token,
            'spotify_token_expiry': datetime.now().timestamp() + expires_in
        }}
    )
    
    flash('Spotify connected successfully!', 'success')
    return redirect(url_for('dashboard'))

# User Profile Management
@app.route('/update-profile', methods=['POST'])
def update_profile():
    """Update user profile information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    user_id = session['user_id']
    
    # Validate data
    if not data.get('username'):
        return jsonify({'success': False, 'message': 'Username is required'})
    
    # Check if new username is already taken by another user
    existing_user = users_collection.find_one({
        'username': data.get('username'), 
        '_id': {'$ne': ObjectId(user_id)}
    })
    
    if existing_user:
        return jsonify({'success': False, 'message': 'Username already taken'})
    
    # Update user data
    update_data = {
        'username': data.get('username'),
        'university': data.get('university'),
        'department': data.get('department'),
        'year': data.get('year'),
        'skills': data.get('skills', []),
        'skill_ratings': data.get('skill_ratings', {})
    }
    
    try:
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        
        # Update session username
        session['username'] = data.get('username')
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Login Streak Management
@app.route('/get-login-streak', methods=['GET'])
def get_login_streak():
    """Get user login streak data"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Check if login tracking exists
    login_tracking = db.login_tracking.find_one({'user_id': user_id})
    
    if not login_tracking:
        # No login tracking yet
        return jsonify({
            'success': True,
            'currentStreak': 0,
            'longestStreak': 0,
            'lastWeek': [False, False, False, False, False, False, False]
        })
    
    # Generate last week's login pattern
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_pattern = [False] * 7  # Initialize with 7 days, all False
    
    # Get last 7 days
    for i in range(7):
        check_date = (today - timedelta(days=6-i)).date()
        
        # Check if user logged in on that day
        for login_date in login_tracking.get('login_days', []):
            if login_date.date() == check_date:
                week_pattern[i] = True
                break
    
    return jsonify({
        'success': True,
        'currentStreak': login_tracking.get('current_streak', 0),
        'longestStreak': login_tracking.get('longest_streak', 0),
        'lastWeek': week_pattern
    })

# Widget Management Routes
@app.route('/get-widgets', methods=['GET'])
def get_widgets():
    """Retrieve user's widget configurations"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user_widgets = widgets_collection.find({'user_id': user_id})
    
    widgets = []
    for widget in user_widgets:
        widget['_id'] = str(widget['_id'])  # Convert ObjectId to string
        
        # Ensure content dictionary exists
        if 'content' not in widget:
            widget['content'] = {}
            
        # Special handling for widgets with extended content
        if widget['widget_type'] == 'calendar':
            # Get calendar events
            calendar_data = calendar_events_collection.find_one({'user_id': user_id})
            if calendar_data and 'events' in calendar_data:
                events = calendar_data['events']
                # Convert dates back to ISO format for JS
                for event in events:
                    if isinstance(event.get('date'), datetime):
                        event['date'] = event['date'].isoformat()
                widget['content']['events'] = events
                
        elif widget['widget_type'] == 'todo':
            # Get todos
            todo_data = todos_collection.find_one({'user_id': user_id})
            if todo_data and 'items' in todo_data:
                widget['content']['todos'] = todo_data['items']
                
        elif widget['widget_type'] == 'pet':
            # Get pet data
            pet = pet_data_collection.find_one({'user_id': user_id})
            if pet:
                widget['content']['petType'] = pet.get('type', 'cat')
                widget['content']['petName'] = pet.get('name', 'Pet')
                widget['content']['petHunger'] = pet.get('hunger', 100)
                widget['content']['petHappiness'] = pet.get('happiness', 100)
                widget['content']['petEnergy'] = pet.get('energy', 100)
                
        elif widget['widget_type'] == 'alarm':
            # Get alarms
            alarm_data = alarms_collection.find_one({'user_id': user_id})
            if alarm_data and 'items' in alarm_data:
                widget['content']['alarms'] = alarm_data['items']
                
        elif widget['widget_type'] == 'pomodoro':
            # Get pomodoro settings
            pomodoro_data = pomodoro_settings_collection.find_one({'user_id': user_id})
            if pomodoro_data:
                widget['content']['workTime'] = pomodoro_data.get('workTime', 25)
                widget['content']['breakTime'] = pomodoro_data.get('breakTime', 5)
                widget['content']['longBreakTime'] = pomodoro_data.get('longBreakTime', 15)
                
        elif widget['widget_type'] == 'image':
            # Get image data
            image_id = widget.get('image_id')
            if image_id:
                try:
                    image_data = images_collection.find_one({'_id': ObjectId(image_id)})
                    if image_data and 'filename' in image_data:
                        widget['content']['image_url'] = f"/uploads/{image_data.get('filename')}"
                        widget['content']['image_id'] = str(image_id)
                except Exception as e:
                    print(f"Error retrieving image for widget {widget.get('_id')}: {str(e)}")
                    
        elif widget['widget_type'] == 'bounty':
            # Get bounty data
            try:
                # Get recent bounties
                recent_bounties = list(db.bounties.find(
                    {'creator_id': user_id}
                ).sort('created_at', -1).limit(3))
                
                formatted_bounties = []
                for bounty in recent_bounties:
                    formatted_bounties.append({
                        '_id': str(bounty['_id']),
                        'title': bounty['title'],
                        'status': bounty['status'],
                        'reward': bounty['reward'],
                        'created_at': bounty['created_at'].isoformat() if isinstance(bounty['created_at'], datetime) else bounty['created_at']
                    })
                
                widget['content']['recentBounties'] = formatted_bounties
                
                # Get solved bounties count
                user_responses = list(db.bounty_responses.find({'responder_id': user_id}))
                solved_count = 0
                for response in user_responses:
                    if db.bounties.find_one({'_id': ObjectId(response['bounty_id']), 'status': 'closed'}):
                        solved_count += 1
                
                widget['content']['solvedCount'] = solved_count
                widget['content']['createdCount'] = db.bounties.count_documents({'creator_id': user_id})
            except Exception as e:
                print(f"Error retrieving bounty data: {str(e)}")
                
        elif widget['widget_type'] == 'marketplace':
            # Get marketplace data
            try:
                # Get user's listings
                user_listings = list(db.marketplace_listings.find(
                    {'seller_id': user_id}
                ).sort('created_at', -1).limit(3))
                
                formatted_listings = []
                for listing in user_listings:
                    formatted_listings.append({
                        '_id': str(listing['_id']),
                        'title': listing['title'],
                        'price': listing['price'],
                        'downloads': listing.get('downloads', 0),
                        'created_at': listing['created_at'].isoformat() if isinstance(listing['created_at'], datetime) else listing['created_at']
                    })
                
                widget['content']['userListings'] = formatted_listings
                
                # Get sales data
                transactions = list(db.marketplace_transactions.find({'seller_id': user_id}))
                total_sales = sum(t['price'] for t in transactions)
                
                widget['content']['totalSales'] = total_sales
                widget['content']['salesCount'] = len(transactions)
            except Exception as e:
                print(f"Error retrieving marketplace data: {str(e)}")
                
        elif widget['widget_type'] == 'studyspot':
            # Get study spot data
            try:
                # Get nearby spots
                study_spots = list(db.study_spots.find().limit(3))
                
                formatted_spots = []
                for spot in study_spots:
                    # Get latest occupancy
                    latest_occupancy = db.occupancy_reports.find_one(
                        {'spot_id': str(spot['_id'])},
                        sort=[('reported_at', -1)]
                    )
                    
                    occupancy_level = 'low'
                    if latest_occupancy:
                        occupancy_level = latest_occupancy.get('occupancy_level', 'low')
                    
                    formatted_spots.append({
                        '_id': str(spot['_id']),
                        'name': spot['name'],
                        'occupancy': occupancy_level,
                        'address': spot.get('address', '')
                    })
                
                widget['content']['nearbySpots'] = formatted_spots
            except Exception as e:
                print(f"Error retrieving study spot data: {str(e)}")
        
        # Add the widget to the list
        widgets.append(widget)
    
    return jsonify({'success': True, 'widgets': widgets})

@app.route('/save-widget', methods=['POST'])
def save_widget():
    """Save or update a widget configuration"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    user_id = session['user_id']
    
    # Debug logging to understand incoming data
    print(f"Saving widget for user {user_id}, widget type: {data.get('widget_type')}, widget id: {data.get('widget_id')}")
    
    widget_data = {
        'user_id': user_id,
        'widget_type': data.get('widget_type'),
        'position': data.get('position'),
        'size': data.get('size'),
        'bg_color': data.get('bg_color', '#ffffff'),
        'text_color': data.get('text_color', '#000000'),
        'content': data.get('content', {}),
        'is_public': data.get('is_public', False),  # Default to private
        'last_updated': datetime.now()
    }
    
    # Handle special widget data
    if data.get('widget_type') == 'calendar' and 'events' in data.get('content', {}):
        # Save calendar events to dedicated collection
        events = data['content']['events']
        # Process date objects from JS to Python datetime
        for event in events:
            if isinstance(event['date'], str):
                try:
                    event['date'] = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
                except:
                    # Fall back to keeping it as a string if we can't parse
                    pass
        
        # Update or insert calendar events
        calendar_events_collection.update_one(
            {'user_id': user_id},
            {'$set': {'events': events}},
            upsert=True
        )
    
    elif data.get('widget_type') == 'todo' and 'todos' in data.get('content', {}):
        # Save todos to dedicated collection
        todos = data['content']['todos']
        todos_collection.update_one(
            {'user_id': user_id},
            {'$set': {'items': todos}},
            upsert=True
        )
    
    elif data.get('widget_type') == 'pet' and 'petType' in data.get('content', {}):
        # Save pet data to dedicated collection
        pet_data = {
            'type': data['content'].get('petType', 'cat'),
            'name': data['content'].get('petName', 'Pet'),
            'hunger': data['content'].get('petHunger', 100),
            'happiness': data['content'].get('petHappiness', 100),
            'energy': data['content'].get('petEnergy', 100),
            'last_interaction': datetime.now()
        }
        pet_data_collection.update_one(
            {'user_id': user_id},
            {'$set': pet_data},
            upsert=True
        )
    
    elif data.get('widget_type') == 'alarm' and 'alarms' in data.get('content', {}):
        # Save alarms to dedicated collection
        alarms = data['content']['alarms']
        alarms_collection.update_one(
            {'user_id': user_id},
            {'$set': {'items': alarms}},
            upsert=True
        )
        
    elif data.get('widget_type') == 'pomodoro':
        # Save pomodoro settings to dedicated collection
        if 'workTime' in data.get('content', {}):
            pomodoro_settings = {
                'workTime': data['content'].get('workTime', 25),
                'breakTime': data['content'].get('breakTime', 5),
                'longBreakTime': data['content'].get('longBreakTime', 15)
            }
            pomodoro_settings_collection.update_one(
                {'user_id': user_id},
                {'$set': pomodoro_settings},
                upsert=True
            )
    
    # Save image ID if this is an image widget
    if data.get('widget_type') == 'image' and data.get('image_id'):
        widget_data['image_id'] = data.get('image_id')
    
    # Determine how to find the existing widget (if it exists)
    existing_widget = None
    
    # If a widget_id is provided, use that as the primary identifier
    if data.get('widget_id'):
        try:
            existing_widget = widgets_collection.find_one({
                'user_id': user_id,
                '_id': ObjectId(data.get('widget_id'))
            })
            if existing_widget:
                print(f"Found existing widget by ID: {data.get('widget_id')}")
        except Exception as e:
            print(f"Error looking up widget by ID: {str(e)}")
    
    # If no widget found by ID and it's a standard widget type, try finding by type
    if not existing_widget and data.get('widget_type') not in ['notes', 'image']:
        existing_widget = widgets_collection.find_one({
            'user_id': user_id,
            'widget_type': data.get('widget_type')
        })
        if existing_widget:
            print(f"Found existing widget by type: {data.get('widget_type')}")
    
    if existing_widget:
        # Update existing widget
        try:
            print(f"Updating widget: {existing_widget['_id']}, Type: {data.get('widget_type')}")
            widgets_collection.update_one(
                {'_id': existing_widget['_id']},
                {'$set': widget_data}
            )
            widget_id = str(existing_widget['_id'])
        except Exception as e:
            print(f"Error updating widget: {str(e)}")
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'})
    else:
        # Create new widget
        try:
            print(f"Creating new widget, Type: {data.get('widget_type')}")
            result = widgets_collection.insert_one(widget_data)
            widget_id = str(result.inserted_id)
            print(f"Created widget with ID: {widget_id}")
        except Exception as e:
            print(f"Error creating widget: {str(e)}")
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'})
    
    return jsonify({
        'success': True, 
        'message': 'Widget saved successfully',
        'widget_id': widget_id  # Always return the widget ID
    })

@app.route('/delete-widget', methods=['POST'])
def delete_widget():
    """Delete a widget"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    user_id = session['user_id']
    widget_type = data.get('widget_type')
    widget_id = data.get('widget_id')
    
    # For widgets that can have multiple instances, use widget_id if provided
    if widget_id:
        # Delete specific widget by ID
        widgets_collection.delete_one({
            'user_id': user_id,
            '_id': ObjectId(widget_id)
        })
    else:
        # Delete widget by type
        widgets_collection.delete_one({
            'user_id': user_id,
            'widget_type': widget_type
        })
    
    # Clean up any related data
    if widget_type == 'calendar':
        calendar_events_collection.delete_one({'user_id': user_id})
    elif widget_type == 'todo':
        todos_collection.delete_one({'user_id': user_id})
    elif widget_type == 'pet':
        pet_data_collection.delete_one({'user_id': user_id})
    elif widget_type == 'alarm':
        alarms_collection.delete_one({'user_id': user_id})
    elif widget_type == 'pomodoro':
        pomodoro_settings_collection.delete_one({'user_id': user_id})
    elif widget_type == 'image' and widget_id:
        # Get image ID to delete from images collection
        widget = widgets_collection.find_one({'_id': ObjectId(widget_id)})
        if widget and 'image_id' in widget:
            # Delete the image file if it exists
            image_doc = images_collection.find_one({'_id': ObjectId(widget['image_id'])})
            if image_doc and 'filename' in image_doc:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_doc['filename'])
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error removing image file: {str(e)}")
            
            # Delete the image record
            images_collection.delete_one({'_id': ObjectId(widget['image_id'])})
    
    return jsonify({'success': True, 'message': 'Widget deleted successfully'})

# Add these route to your existing app.py file

@app.route('/marketplace')
def marketplace_page():
    """Render the marketplace page"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    try:
        # Explicitly check database connection
        user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
        if not user:
            # If we can't find the user, redirect to login
            session.clear()
            return redirect(url_for('login_page'))
            
        # Check if marketplace_listings collection exists
        if 'marketplace_listings' not in db.list_collection_names():
            print("WARNING: marketplace_listings collection does not exist")
        
        # Test a simple query to verify database access
        test_count = db.marketplace_listings.count_documents({})
        print(f"Found {test_count} marketplace listings in database")
        
        return render_template('marketplace.html', user=user)
    except Exception as e:
        print(f"Database error in marketplace route: {str(e)}")
        flash('Error connecting to database. Please try again later.', 'error')
        return redirect(url_for('dashboard'))

# API route to get marketplace listings
# API route to get marketplace listings
@app.route('/api/marketplace_listings')
def get_marketplace_listings():
    """Get marketplace listings with filtering and pagination"""
    if 'user_id' not in session:
        print("User not authenticated")
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        print("Fetching marketplace listings for user:", session['user_id'])
        
        # Get query parameters
        category = request.args.get('category')
        type_filter = request.args.get('type')
        search = request.args.get('search', '')
        sort = request.args.get('sort', 'newest')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 12))
        
        print(f"Query params: category={category}, type={type_filter}, search={search}, sort={sort}, page={page}")
        
        # Build query
        query = {}
        
        if category and category != 'all':
            query['category'] = category
        
        if type_filter and type_filter != 'all':
            query['type'] = type_filter
        
        if search:
            query['$or'] = [
                {'title': {'$regex': search, '$options': 'i'}},
                {'description': {'$regex': search, '$options': 'i'}},
                {'subject': {'$regex': search, '$options': 'i'}}
            ]
        
        print("MongoDB query:", query)
        
        # Check if we can access the collection at all
        try:
            # Get a simple count of all documents first
            total_docs = db.marketplace_listings.count_documents({})
            print(f"Total listings in database: {total_docs}")
            
            # Now get the filtered count
            total = db.marketplace_listings.count_documents(query)
            print(f"Filtered listings count: {total}")
        except Exception as count_error:
            print(f"Error counting documents: {str(count_error)}")
            return jsonify({
                'success': False, 
                'message': f'Database access error: {str(count_error)}',
                'listings': []
            })
        
        # Calculate total pages
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        # Adjust page if out of bounds
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Set up sort
        sort_options = {
            'newest': [('created_at', -1)],
            'price_low': [('price', 1)],
            'price_high': [('price', -1)],
            'popular': [('downloads', -1)],
            'relevant': [('downloads', -1), ('created_at', -1)]
        }
        
        sort_option = sort_options.get(sort, [('created_at', -1)])
        
        # Get listings with debugging info
        print(f"Executing find() with sort={sort_option}, skip={skip}, limit={limit}")
        listings_cursor = db.marketplace_listings.find(query).sort(sort_option).skip(skip).limit(limit)
        
        # Format listings for response
        listings = []
        for listing in listings_cursor:
            try:
                # Convert ObjectId to string for JSON
                listing_id = str(listing.get('_id', ''))
                
                # Handle seller info
                seller_data = {'username': 'Unknown User', 'avatar_id': 'default'}
                seller_id = listing.get('seller_id')
                if seller_id:
                    try:
                        if isinstance(seller_id, str):
                            seller = users_collection.find_one({'_id': ObjectId(seller_id)})
                        else:
                            seller = users_collection.find_one({'_id': seller_id})
                        
                        if seller:
                            seller_data = {
                                '_id': str(seller.get('_id')),
                                'username': seller.get('username', 'Unknown User'),
                                'avatar_id': seller.get('avatar_id', 'default')
                            }
                    except Exception as seller_error:
                        print(f"Error getting seller for listing {listing_id}: {str(seller_error)}")
                
                # Format date
                created_at = datetime.now().isoformat()
                if listing.get('created_at'):
                    try:
                        if isinstance(listing['created_at'], datetime):
                            created_at = listing['created_at'].isoformat()
                        elif isinstance(listing['created_at'], str):
                            created_at = listing['created_at']
                    except Exception as date_error:
                        print(f"Error formatting date: {str(date_error)}")
                
                # Create listing data with all required fields 
                # Get preview path or placeholder if none exists
                # Get preview path or placeholder if none exists
                preview_path = listing.get('preview_path')
                if not preview_path or preview_path == "":
                    # Use a placeholder image based on the listing type
                    preview_path = get_placeholder_image(listing.get('type'))

                # Prepare listing data
                listing_data = {
                    '_id': str(listing['_id']),
                    'title': listing.get('title', 'Untitled'),
                    'description': listing.get('description', 'No description'),
                    'category': listing.get('category', 'General'),
                    'type': listing.get('type', 'notes'),
                    'subject': listing.get('subject', ''),
                    'price': listing.get('price', 0),
                    'downloads': listing.get('downloads', 0),
                    'created_at': created_at,
                    'preview_path': preview_path,
                    'file_path': listing.get('file_path'),
                    'seller': {
                        '_id': str(seller['_id']),
                        'username': seller.get('username', 'Unknown User'),
                        'avatar_id': seller.get('avatar_id', 'default')
                    }
                }
                
                listings.append(listing_data)
            except Exception as listing_error:
                print(f"Error processing listing: {str(listing_error)}")
        
        print(f"Returning {len(listings)} listings")
        return jsonify({
            'success': True,
            'listings': listings,
            'total': total,
            'page': page,
            'pages': total_pages
        })
        
    except Exception as e:
        print(f"Error in get_marketplace_listings: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Error retrieving listings: {str(e)}',
            'listings': []
        })

# API route to get single listing
@app.route('/api/marketplace_listings/<listing_id>')
def get_marketplace_listing(listing_id):
    """Get a single marketplace listing by ID"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        listing = db.marketplace_listings.find_one({'_id': ObjectId(listing_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid listing ID'})
    
    if not listing:
        return jsonify({'success': False, 'message': 'Listing not found'})
    
    # Get seller info
    seller = users_collection.find_one({'_id': ObjectId(listing['seller_id'])})
    if not seller:
        seller = {
            '_id': 'deleted',
            'username': 'Unknown User',
            'avatar_id': 'default'
        }
    
    # Format dates
    created_at = listing.get('created_at').isoformat() if isinstance(listing.get('created_at'), datetime) else listing.get('created_at')
    
    # Prepare listing data
    listing_data = {
        '_id': str(listing['_id']),
        'title': listing.get('title', 'Untitled'),
        'description': listing.get('description', 'No description'),
        'category': listing.get('category', 'General'),
        'type': listing.get('type', 'notes'),
        'subject': listing.get('subject', ''),
        'price': listing.get('price', 0),
        'downloads': listing.get('downloads', 0),
        'created_at': created_at,
        'preview_path': listing.get('preview_path'),
        'file_path': listing.get('file_path'),
        'seller': {
            '_id': str(seller['_id']),
            'username': seller.get('username', 'Unknown User'),
            'avatar_id': seller.get('avatar_id', 'default')
        }
    }
    
    return jsonify({
        'success': True,
        'listing': listing_data
    })

# API route to create a listing
@app.route('/api/marketplace_listings', methods=['POST'])
def create_marketplace_listing():
    """Create a new marketplace listing"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Get form data
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    type_value = request.form.get('type')
    subject = request.form.get('subject')
    price = request.form.get('price')
    
    # Validate required fields
    if not title or not description or not category or not type_value or not subject or not price:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    # Convert price to integer
    try:
        price = int(price)
    except:
        return jsonify({'success': False, 'message': 'Invalid price'})
    
    # Get tags
    tags = []
    for key in request.form:
        if key.startswith('tags['):
            tags.append(request.form[key])
    
    # Handle file upload
    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            # Generate secure filename
            filename = secure_filename(file.filename)
            
            # Add timestamp for uniqueness
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Save file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Use relative path for database
            file_path = f"/uploads/{filename}"
    
    # Handle preview image upload
    preview_path = None
    if 'image' in request.files:
        image = request.files['image']
        if image and image.filename and allowed_file(image.filename):
            # Generate secure filename
            filename = secure_filename(image.filename)
            
            # Add timestamp for uniqueness
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"preview_{timestamp}_{filename}"
            
            # Save image
            preview_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(preview_path)
            
            # Use relative path for database
            preview_path = f"/uploads/{filename}"
    
    # Create listing document
    listing = {
        'seller_id': session['user_id'],
        'title': title,
        'description': description,
        'category': category,
        'type': type_value,
        'subject': subject,
        'price': price,
        'tags': tags,
        'file_path': file_path,
        'preview_path': preview_path,
        'downloads': 0,
        'created_at': datetime.now()
    }
    
    # Insert into database
    result = db.marketplace_listings.insert_one(listing)
    
    return jsonify({
        'success': True,
        'message': 'Listing created successfully',
        'listing_id': str(result.inserted_id)
    })

# API route to create a transaction (purchase)
@app.route('/api/marketplace_transactions', methods=['POST'])
def create_marketplace_transaction():
    """Create a new marketplace transaction (purchase a listing)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    listing_id = data.get('listing_id')
    
    if not listing_id:
        return jsonify({'success': False, 'message': 'Listing ID is required'})
    
    # Get user
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Get listing
    try:
        listing = db.marketplace_listings.find_one({'_id': ObjectId(listing_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid listing ID'})
    
    if not listing:
        return jsonify({'success': False, 'message': 'Listing not found'})
    
    # Check if user has enough coins
    if user.get('coins_balance', 0) < listing['price']:
        return jsonify({'success': False, 'message': f'Not enough coins. You need {listing["price"]} coins to purchase this item.'})
    
    # Check if user is trying to buy their own listing
    if listing['seller_id'] == session['user_id']:
        return jsonify({'success': False, 'message': 'You cannot purchase your own listing'})
    
    # Check if user has already purchased this listing
    existing_transaction = db.marketplace_transactions.find_one({
        'listing_id': listing_id,
        'buyer_id': session['user_id']
    })
    
    if existing_transaction:
        return jsonify({'success': False, 'message': 'You have already purchased this item'})
    
    # Create transaction
    transaction = {
        'listing_id': listing_id,
        'buyer_id': session['user_id'],
        'seller_id': listing['seller_id'],
        'price': listing['price'],
        'transaction_date': datetime.now()
    }
    
    # Update buyer's coin balance
    users_collection.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$inc': {'coins_balance': -listing['price']}}
    )
    
    # Update seller's coin balance
    users_collection.update_one(
        {'_id': ObjectId(listing['seller_id'])},
        {'$inc': {'coins_balance': listing['price']}}
    )
    
    # Increment download count
    db.marketplace_listings.update_one(
        {'_id': ObjectId(listing_id)},
        {'$inc': {'downloads': 1}}
    )
    
    # Record transaction
    result = db.marketplace_transactions.insert_one(transaction)
    
    # Record coin transactions
    buyer_transaction = {
        'user_id': session['user_id'],
        'amount': -listing['price'],
        'transaction_type': 'marketplace_purchase',
        'reference_id': str(result.inserted_id),
        'description': f'Purchased: {listing["title"]}',
        'created_at': datetime.now()
    }
    
    seller_transaction = {
        'user_id': listing['seller_id'],
        'amount': listing['price'],
        'transaction_type': 'marketplace_sale',
        'reference_id': str(result.inserted_id),
        'description': f'Sold: {listing["title"]}',
        'created_at': datetime.now()
    }
    
    db.coin_transactions.insert_one(buyer_transaction)
    db.coin_transactions.insert_one(seller_transaction)
    
    return jsonify({
        'success': True,
        'message': 'Purchase successful',
        'transaction_id': str(result.inserted_id)
    })

# Image upload endpoint
@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image part'})
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'File type not allowed'})
    
    try:
        # Generate a secure filename
        filename = secure_filename(file.filename)
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Save file to disk
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Record in database
        image_id = images_collection.insert_one({
            'user_id': session['user_id'],
            'filename': filename,
            'uploaded_at': datetime.now(),
            'original_name': file.filename
        }).inserted_id
        
        # Return success with image ID and URL
        return jsonify({
            'success': True, 
            'message': 'Image uploaded successfully',
            'image_id': str(image_id),
            'image_url': f"/uploads/{filename}"
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error uploading image: {str(e)}'})

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Dashboard Settings Management
@app.route('/save-dashboard-settings', methods=['POST'])
def save_dashboard_settings():
    """Save dashboard background settings"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    user_id = session['user_id']
    
    # Prepare settings object
    settings = {
        'background_type': data.get('background_type', 'color'),  # 'color' or 'image'
        'background_value': data.get('background_value', '#000000'),  # color value or image URL
        'updated_at': datetime.now()
    }
    
    try:
        # Update or insert settings
        dashboard_settings_collection.update_one(
            {'user_id': user_id},
            {'$set': settings},
            upsert=True
        )
        
        return jsonify({'success': True, 'message': 'Dashboard settings saved'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Update widgets visibility
@app.route('/update-widgets-visibility', methods=['POST'])
def update_widgets_visibility():
    """Update visibility (public/private) for widgets"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    user_id = session['user_id']
    is_public = data.get('is_public', False)
    widget_ids = data.get('widget_ids', [])
    
    if not widget_ids:
        return jsonify({'success': False, 'message': 'No widgets specified'})
    
    try:
        # Convert string IDs to ObjectId
        object_ids = [ObjectId(widget_id) for widget_id in widget_ids]
        
        # Update visibility for specified widgets
        result = widgets_collection.update_many(
            {
                'user_id': user_id,
                '_id': {'$in': object_ids}
            },
            {'$set': {'is_public': is_public}}
        )
        
        return jsonify({
            'success': True, 
            'message': f"Updated {result.modified_count} widgets",
            'modified_count': result.modified_count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Update all widgets' color
@app.route('/update-all-widgets-color', methods=['POST'])
def update_all_widgets_color():
    """Update background and text color for all widgets"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    user_id = session['user_id']
    bg_color = data.get('bg_color')
    text_color = data.get('text_color')
    
    update_fields = {}
    if bg_color:
        update_fields['bg_color'] = bg_color
    if text_color:
        update_fields['text_color'] = text_color
    
    if not update_fields:
        return jsonify({'success': False, 'message': 'No colors specified'})
    
    try:
        # Update all widgets for this user
        result = widgets_collection.update_many(
            {'user_id': user_id},
            {'$set': update_fields}
        )
        
        return jsonify({
            'success': True, 
            'message': f"Updated {result.modified_count} widgets",
            'modified_count': result.modified_count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# GitHub API Routes
@app.route('/get-github-repos', methods=['GET'])
def get_github_repos():
    """Fetch GitHub repositories for a user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user or 'github_username' not in user:
        return jsonify({'success': False, 'message': 'No GitHub account connected'})
    
    github_username = user['github_username']
    
    try:
        response = requests.get(f'https://api.github.com/users/{github_username}/repos')
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to fetch GitHub repositories'})
        
        repos = response.json()
        simplified_repos = []
        
        for repo in repos:
            simplified_repos.append({
                'name': repo['name'],
                'description': repo['description'],
                'url': repo['html_url'],
                'stars': repo['stargazers_count'],
                'forks': repo['forks_count'],
                'language': repo['language']
            })
        
        return jsonify({'success': True, 'repos': simplified_repos})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Bounty Statistics API
@app.route('/get-bounty-stats', methods=['GET'])
def get_bounty_stats():
    """Get user's bounty statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    try:
        # Count bounties created by user
        created_bounties = db.bounties.count_documents({'creator_id': user_id})
        
        # Count bounties solved by user (where user's response is accepted)
        user_responses = list(db.bounty_responses.find({'responder_id': user_id}))
        solved_bounties = 0
        for response in user_responses:
            if db.bounties.find_one({'_id': response['bounty_id'], 'status': 'closed'}):
                solved_bounties += 1
        
        # Calculate fairness score (based on upvotes ratio)
        upvotes = db.bounty_votes.count_documents({'user_id': user_id, 'vote_type': 'up'})
        total_votes = db.bounty_votes.count_documents({'user_id': user_id})
        fairness_score = int(upvotes / total_votes * 100) if total_votes > 0 else 0
        
        # Get recent bounties
        recent_bounties = list(db.bounties.find({'creator_id': user_id}).sort('created_at', -1).limit(3))
        for bounty in recent_bounties:
            bounty['_id'] = str(bounty['_id'])  # Convert ObjectId to string
        
        # Create category distribution
        user_bounties = list(db.bounties.find({'creator_id': user_id}))
        category_counts = {}
        for bounty in user_bounties:
            category = bounty.get('category', 'Other')
            if category in category_counts:
                category_counts[category] += 1
            else:
                category_counts[category] = 1
        
        return jsonify({
            'success': True,
            'stats': {
                'created': created_bounties,
                'solved': solved_bounties,
                'fairnessScore': fairness_score
            },
            'recentBounties': recent_bounties,
            'categoryDistribution': category_counts
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Knowledge Forum Routes
@app.route('/knowledge-forum')
def knowledge_forum():
    """Render the knowledge forum page"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return redirect(url_for('login_page'))
        
    return render_template('Knowledge Nexus Forum.html', user=user)

# API route to get questions
@app.route('/api/questions')
def get_questions():
    """Get questions with filtering and pagination"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Get query parameters
    category = request.args.get('category', 'all')
    status = request.args.get('status', 'all')
    complexity = request.args.getlist('complexity[]')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 12))
    
    # Build query
    query = {}
    
    # Filter by category
    if category != 'all':
        query['category'] = category
    
    # Filter by status
    if status == 'answered':
        query['is_answered'] = True
    elif status == 'unanswered':
        query['is_answered'] = False
    elif status == 'featured':
        query['is_featured'] = True
    elif status == 'trending':
        query['is_trending'] = True
    
    # Filter by complexity
    if complexity:
        complexity_levels = [int(c) for c in complexity]
        query['complexity'] = {'$in': complexity_levels}
    
    # Filter by search
    if search:
        query['$or'] = [
            {'title': {'$regex': search, '$options': 'i'}},
            {'content': {'$regex': search, '$options': 'i'}}
        ]
    
    # Count total matching questions
    total = db.questions.count_documents(query)
    
    # Set up sort
    sort_options = {
        'newest': [('created_at', -1)],
        'oldest': [('created_at', 1)],
        'votes': [('upvotes', -1)],
        'answers': [('answer_count', -1)],
        'trending': [('view_count', -1)]
    }
    
    sort_option = sort_options.get(sort, [('created_at', -1)])
    
    # Apply pagination
    skip = (page - 1) * limit
    questions_cursor = db.questions.find(query).sort(sort_option).skip(skip).limit(limit)
    
    # Format questions
    questions = []
    for question in questions_cursor:
        # Get author info
        author = users_collection.find_one({'_id': ObjectId(question['creator_id'])})
        if not author:
            author = {
                '_id': 'deleted',
                'username': 'Deleted User',
                'avatar_id': 'default'
            }
        
        # Format dates
        created_at = question['created_at'].isoformat() if isinstance(question['created_at'], datetime) else question['created_at']
        
        # Format question for response
        formatted_question = {
            '_id': str(question['_id']),
            'title': question['title'],
            'content': question['content'],
            'category': question['category'],
            'tags': question['tags'],
            'complexity': question['complexity'],
            'upvotes': question.get('upvotes', 0),
            'answer_count': question.get('answer_count', 0),
            'view_count': question.get('view_count', 0),
            'is_answered': question.get('is_answered', False),
            'is_featured': question.get('is_featured', False),
            'is_trending': question.get('is_trending', False),
            'created_at': created_at,
            'author': {
                '_id': str(author['_id']),
                'username': author['username'],
                'avatar_id': author.get('avatar_id', 'default'),
                'level': author.get('level', 1)
            }
        }
        
        questions.append(formatted_question)
    
    # Calculate total pages
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return jsonify({
        'success': True,
        'questions': questions,
        'total': total,
        'page': page,
        'pages': total_pages
    })

# API route to get categories
@app.route('/api/categories')
def get_forum_categories():
    """Get question categories"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Find unique categories from questions
    pipeline = [
        {"$group": {"_id": "$category"}},
        {"$sort": {"_id": 1}}
    ]
    
    categories = list(db.questions.aggregate(pipeline))
    
    # Default icons for categories
    category_icons = {
        'Computer Science': 'fa-laptop-code',
        'Data Science': 'fa-database',
        'Artificial Intelligence': 'fa-brain',
        'Business Administration': 'fa-chart-line',
        'Economics': 'fa-chart-area',
        'Finance': 'fa-dollar-sign',
        'Marketing': 'fa-ad',
        'Psychology': 'fa-brain',
        'English Literature': 'fa-book',
        'History': 'fa-history',
        'Political Science': 'fa-landmark',
        'Law': 'fa-balance-scale',
        'Mass Communication': 'fa-comments',
        'Hotel Management': 'fa-hotel',
        'Fashion Design': 'fa-tshirt'
    }
    
    # Format categories
    formatted_categories = []
    for category in categories:
        cat_name = category['_id']
        formatted_categories.append({
            'name': cat_name,
            'icon': category_icons.get(cat_name, 'fa-tag')
        })
    
    return jsonify({
        'success': True,
        'categories': formatted_categories
    })

# API route to create a question
@app.route('/api/questions', methods=['POST'])
def create_question():
    """Create a new question"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    user_id = session['user_id']
    
    # Validate required fields
    required_fields = ['title', 'content', 'category', 'complexity', 'tags']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'})
    
    # Validate complexity
    complexity = data['complexity']
    if complexity < 1 or complexity > 5:
        return jsonify({'success': False, 'message': 'Complexity must be between 1 and 5'})
    
    # Create question document
    question = {
        'creator_id': user_id,
        'title': data['title'],
        'content': data['content'],
        'category': data['category'],
        'tags': data['tags'],
        'complexity': complexity,
        'upvotes': 0,
        'downvotes': 0,
        'view_count': 0,
        'answer_count': 0,
        'is_answered': False,
        'is_featured': False,
        'is_trending': False,
        'created_at': datetime.now()
    }
    
    # Insert into database
    result = db.questions.insert_one(question)
    
    # Award experience points for asking a question
    update_experience(user_id, 5, 'Asked a question')
    
    return jsonify({
        'success': True,
        'message': 'Question created successfully',
        'question_id': str(result.inserted_id)
    })

# API route to get a single question
@app.route('/api/questions/<question_id>')
def get_question(question_id):
    """Get a single question by ID"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Increment view count
        db.questions.update_one(
            {'_id': ObjectId(question_id)},
            {'$inc': {'view_count': 1}}
        )
        
        # Find question
        question = db.questions.find_one({'_id': ObjectId(question_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid question ID'})
    
    if not question:
        return jsonify({'success': False, 'message': 'Question not found'})
    
    # Get author info
    author = users_collection.find_one({'_id': ObjectId(question['creator_id'])})
    if not author:
        author = {
            '_id': 'deleted',
            'username': 'Deleted User',
            'avatar_id': 'default'
        }
    
    # Format dates
    created_at = question['created_at'].isoformat() if isinstance(question['created_at'], datetime) else question['created_at']
    
    # Format question for response
    formatted_question = {
        '_id': str(question['_id']),
        'title': question['title'],
        'content': question['content'],
        'category': question['category'],
        'tags': question['tags'],
        'complexity': question['complexity'],
        'upvotes': question.get('upvotes', 0),
        'downvotes': question.get('downvotes', 0),
        'answer_count': question.get('answer_count', 0),
        'view_count': question.get('view_count', 0),
        'is_answered': question.get('is_answered', False),
        'is_featured': question.get('is_featured', False),
        'is_trending': question.get('is_trending', False),
        'created_at': created_at,
        'author': {
            '_id': str(author['_id']),
            'username': author['username'],
            'avatar_id': author.get('avatar_id', 'default'),
            'level': author.get('level', 1)
        }
    }
    
    return jsonify({
        'success': True,
        'question': formatted_question
    })

# API route to get answers for a question
@app.route('/api/questions/<question_id>/answers')
def get_answers(question_id):
    """Get answers for a question"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    try:
        # Find answers
        answers_cursor = db.answers.find({'question_id': question_id}).sort('created_at', 1)
    except:
        return jsonify({'success': False, 'message': 'Invalid question ID'})
    
    # Format answers
    answers = []
    for answer in answers_cursor:
        # Get author info
        author = users_collection.find_one({'_id': ObjectId(answer['author_id'])})
        if not author:
            author = {
                '_id': 'deleted',
                'username': 'Deleted User',
                'avatar_id': 'default'
            }
        
        # Check if user has voted on this answer
        user_vote = db.answer_votes.find_one({
            'answer_id': str(answer['_id']),
            'user_id': user_id
        })
        
        vote_type = user_vote['vote_type'] if user_vote else None
        
        # Get comments for this answer
        comments_cursor = db.answer_comments.find({'answer_id': str(answer['_id'])}).sort('created_at', 1)
        comments = []
        
        for comment in comments_cursor:
            comment_author = users_collection.find_one({'_id': ObjectId(comment['author_id'])})
            if not comment_author:
                comment_author = {
                    '_id': 'deleted',
                    'username': 'Deleted User'
                }
            
            comments.append({
                '_id': str(comment['_id']),
                'content': comment['content'],
                'created_at': comment['created_at'].isoformat() if isinstance(comment['created_at'], datetime) else comment['created_at'],
                'author': {
                    '_id': str(comment_author['_id']),
                    'username': comment_author['username']
                }
            })
        
        # Format answer
        formatted_answer = {
            '_id': str(answer['_id']),
            'content': answer['content'],
            'created_at': answer['created_at'].isoformat() if isinstance(answer['created_at'], datetime) else answer['created_at'],
            'upvotes': answer.get('upvotes', 0),
            'downvotes': answer.get('downvotes', 0),
            'is_accepted': answer.get('is_accepted', False),
            'user_vote': vote_type,
            'comments': comments,
            'author': {
                '_id': str(author['_id']),
                'username': author['username'],
                'avatar_id': author.get('avatar_id', 'default'),
                'expertise': author.get('expertise'),
                'level': author.get('level', 1)
            }
        }
        
        answers.append(formatted_answer)
    
    return jsonify({
        'success': True,
        'answers': answers
    })

# API route to create an answer
@app.route('/api/questions/<question_id>/answers', methods=['POST'])
def create_answer(question_id):
    """Create a new answer for a question"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    data = request.get_json()
    
    # Validate content
    if 'content' not in data or not data['content']:
        return jsonify({'success': False, 'message': 'Answer content is required'})
    
    try:
        # Find question
        question = db.questions.find_one({'_id': ObjectId(question_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid question ID'})
    
    if not question:
        return jsonify({'success': False, 'message': 'Question not found'})
    
    # Create answer document
    answer = {
        'question_id': question_id,
        'author_id': user_id,
        'content': data['content'],
        'upvotes': 0,
        'downvotes': 0,
        'is_accepted': False,
        'created_at': datetime.now()
    }
    
    # Insert into database
    result = db.answers.insert_one(answer)
    
    # Update answer count on question
    db.questions.update_one(
        {'_id': ObjectId(question_id)},
        {'$inc': {'answer_count': 1}}
    )
    
    # Award experience points for answering
    update_experience(user_id, 10, 'Answered a question')
    
    return jsonify({
        'success': True,
        'message': 'Answer created successfully',
        'answer_id': str(result.inserted_id)
    })

# API route to vote on a question
@app.route('/api/questions/<question_id>/vote', methods=['POST'])
def vote_question(question_id):
    """Vote on a question"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    data = request.get_json()
    
    vote_type = data.get('vote_type')
    if vote_type not in ['up', 'down']:
        return jsonify({'success': False, 'message': 'Invalid vote type'})
    
    try:
        # Find question
        question = db.questions.find_one({'_id': ObjectId(question_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid question ID'})
    
    if not question:
        return jsonify({'success': False, 'message': 'Question not found'})
    
    # Check if creator is voting on their own question
    if question['creator_id'] == user_id:
        return jsonify({'success': False, 'message': 'You cannot vote on your own question'})
    
    # Check if user has already voted
    existing_vote = db.question_votes.find_one({
        'question_id': question_id,
        'user_id': user_id
    })
    
    if existing_vote:
        if existing_vote['vote_type'] == vote_type:
            # Remove vote
            db.question_votes.delete_one({'_id': existing_vote['_id']})
            
            # Update question vote count
            if vote_type == 'up':
                db.questions.update_one(
                    {'_id': ObjectId(question_id)},
                    {'$inc': {'upvotes': -1}}
                )
            else:
                db.questions.update_one(
                    {'_id': ObjectId(question_id)},
                    {'$inc': {'downvotes': -1}}
                )
            
            return jsonify({
                'success': True,
                'message': 'Vote removed successfully'
            })
        else:
            # Change vote type
            db.question_votes.update_one(
                {'_id': existing_vote['_id']},
                {'$set': {'vote_type': vote_type}}
            )
            
            # Update question vote count
            if vote_type == 'up':
                db.questions.update_one(
                    {'_id': ObjectId(question_id)},
                    {'$inc': {'upvotes': 1, 'downvotes': -1}}
                )
            else:
                db.questions.update_one(
                    {'_id': ObjectId(question_id)},
                    {'$inc': {'upvotes': -1, 'downvotes': 1}}
                )
            
            return jsonify({
                'success': True,
                'message': 'Vote changed successfully'
            })
    else:
        # Create new vote
        vote = {
            'question_id': question_id,
            'user_id': user_id,
            'vote_type': vote_type,
            'created_at': datetime.now()
        }
        
        
# Marketplace Statistics API
@app.route('/get-marketplace-stats', methods=['GET'])
def get_marketplace_stats():
    """Get marketplace statistics and listings"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Get popular listings (most downloaded)
        popular_listings = list(db.marketplace_listings.find().sort('downloads', -1).limit(5))
        
        # Format listings for front-end
        formatted_listings = []
        for listing in popular_listings:
            formatted_listings.append({
                'title': listing['title'],
                'price': listing['price'],
                'type': listing['type'],
                'seller_id': listing['seller_id'],
                'category': listing.get('category', 'General')
            })
        
        return jsonify({
            'success': True,
            'listings': formatted_listings
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Study Spot Finder API
@app.route('/get-studyspot-stats', methods=['GET'])
def get_studyspot_stats():
    """Get study spot information"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Get study spots with current occupancy
        study_spots = list(db.study_spots.find().limit(5))
        
        # Get latest occupancy for each spot
        formatted_spots = []
        for spot in study_spots:
            spot_id = spot['_id']
            latest_occupancy = db.occupancy_reports.find_one(
                {'spot_id': spot_id},
                sort=[('reported_at', -1)]
            )
            
            occupancy_level = 'low'
            if latest_occupancy:
                occupancy_level = latest_occupancy.get('occupancy_level', 'low')
            
            formatted_spots.append({
                'name': spot['name'],
                'occupancy': occupancy_level,
                'hours': '24/7'  # You would get this from the actual spot data
            })
        
        return jsonify({
            'success': True,
            'spots': formatted_spots
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Spotify API Routes
@app.route('/spotify-current-track', methods=['GET'])
def spotify_current_track():
    """Get current Spotify track"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user or 'spotify_token' not in user:
        return jsonify({'success': False, 'message': 'No Spotify account connected'})
    
    access_token = user['spotify_token']
    
    # Check if token is expired and refresh if needed
    if user.get('spotify_token_expiry', 0) < datetime.now().timestamp():
        access_token = refresh_spotify_token(user['spotify_refresh_token'])
    
    try:
        response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', 
                               headers={'Authorization': f'Bearer {access_token}'})
        
        if response.status_code == 204:
            return jsonify({'success': True, 'playing': False, 'message': 'No track currently playing'})
        
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Failed to fetch current track'})
        
        track_data = response.json()
        track_info = {
            'playing': track_data['is_playing'],
            'track_name': track_data['item']['name'],
            'artist': track_data['item']['artists'][0]['name'],
            'album': track_data['item']['album']['name'],
            'image': track_data['item']['album']['images'][0]['url'] if track_data['item']['album']['images'] else None,
            'progress_ms': track_data['progress_ms'],
            'duration_ms': track_data['item']['duration_ms']
        }
        
        return jsonify({'success': True, 'track': track_info})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def refresh_spotify_token(refresh_token):
    """Refresh Spotify access token"""
    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        
        if token_response.status_code != 200:
            return None
        
        token_info = token_response.json()
        access_token = token_info.get('access_token')
        expires_in = token_info.get('expires_in')
        
        # Update token in database
        users_collection.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': {
                'spotify_token': access_token,
                'spotify_token_expiry': datetime.now().timestamp() + expires_in
            }}
        )
        
        return access_token
    except Exception:
        return None
    

# Add these routes to your existing app.py file

@app.route('/studyspots')
def studyspots_page():
    """Render the study spots page"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return redirect(url_for('login_page'))
        
    return render_template('studyspot.html', user=user)

# API route to get study spots
@app.route('/api/studyspots')
def get_studyspots():
    """Get study spots with filtering and pagination"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Get query parameters
    campus = request.args.get('campus', 'all')
    distance = request.args.get('distance', 'any')
    occupancy = request.args.get('occupancy', 'any')
    activity = request.args.get('activity')
    sort = request.args.get('sort', 'distance')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 9))
    
    # Get user's coordinates if provided
    user_lat = request.args.get('user_lat')
    user_lng = request.args.get('user_lng')
    
    # Build query
    query = {}
    
    # Filter by campus
    if campus != 'all':
        query['campus'] = campus
    
    # Filter by occupancy
    if occupancy != 'any':
        query['occupancy_level'] = occupancy
    
    # Filter by activity
    if activity:
        if activity == 'favorites':
            # Get user's favorited spots
            favorites = list(db.favorite_spots.find({'user_id': user_id}))
            spot_ids = [ObjectId(fav['spot_id']) for fav in favorites]
            if spot_ids:
                query['_id'] = {'$in': spot_ids}
            else:
                # No favorites, return empty array
                return jsonify({
                    'success': True,
                    'spots': [],
                    'total': 0,
                    'page': page,
                    'pages': 0
                })
        elif activity == 'checked-in':
            # Get spots where user has checked in
            checkins = list(db.check_ins.find({'user_id': user_id}))
            spot_ids = [ObjectId(checkin['spot_id']) for checkin in checkins]
            if spot_ids:
                query['_id'] = {'$in': spot_ids}
            else:
                # No check-ins, return empty array
                return jsonify({
                    'success': True,
                    'spots': [],
                    'total': 0,
                    'page': page,
                    'pages': 0
                })
        elif activity == 'added':
            # Get spots added by the user
            query['created_by'] = user_id
    
    # Filter by amenities
    amenities = request.args.getlist('amenities[]')
    if amenities:
        for amenity in amenities:
            query[f'amenities.{amenity}'] = True
    
    # Filter by search term
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}},
            {'address': {'$regex': search, '$options': 'i'}}
        ]
    
    # Filter by distance if user coordinates and distance are provided
    if user_lat and user_lng and distance != 'any':
        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
            
            # Define campus coordinates
            CAMPUS_COORDINATES = {
                "main": {"lat": 12.9344, "lng": 77.6069},      # Christ University Main Campus
                "kengeri": {"lat": 12.9102, "lng": 77.4826},   # Kengeri Campus
                "bgr": {"lat": 12.8687, "lng": 77.5957},       # BGR Campus
                "yeshwanthpur": {"lat": 13.0243, "lng": 77.5538},  # Yeshwanthpur Campus
                "lavasa": {"lat": 73.5043, "lng": 18.4088},    # Lavasa Campus
                "delhi": {"lat": 28.5355, "lng": 77.2410},     # Delhi NCR Campus
                "school_of_law": {"lat": 12.9218, "lng": 77.4963}  # School of Law
            }
            
            # Convert distance string to meters
            distance_meters = None
            if distance == '500m':
                distance_meters = 500
            elif distance == '1km':
                distance_meters = 1000
            elif distance == '3km':
                distance_meters = 3000
            elif distance == '5km':
                distance_meters = 5000
                
            # If we have coordinates in the database, use them for precise filtering
            spots_with_coordinates = list(db.study_spots.find({"location.coordinates": {"$exists": True}}))
            spot_ids_within_distance = []
            
            for spot in spots_with_coordinates:
                if spot.get("location") and spot.get("location").get("coordinates"):
                    spot_lng, spot_lat = spot["location"]["coordinates"]
                    dist = getDistanceFromLatLonInKm(user_lat, user_lng, spot_lat, spot_lng) * 1000  # convert to meters
                    if dist <= distance_meters:
                        spot_ids_within_distance.append(spot["_id"])
            
            # For spots without coordinates, use campus-based approximation
            spots_without_coordinates = list(db.study_spots.find({"location.coordinates": {"$exists": False}}))
            
            for spot in spots_without_coordinates:
                campus = spot.get("campus", "").lower()
                if campus in CAMPUS_COORDINATES:
                    campus_lat = CAMPUS_COORDINATES[campus]["lat"]
                    campus_lng = CAMPUS_COORDINATES[campus]["lng"]
                    
                    # Calculate distance between user and campus
                    campus_dist = getDistanceFromLatLonInKm(user_lat, user_lng, campus_lat, campus_lng) * 1000
                    
                    # For "Near" locations, use a wider radius
                    if "Near" in spot.get("address", ""):
                        # If campus is within distance + 300m, include the spot
                        if campus_dist <= (distance_meters + 300):
                            spot_ids_within_distance.append(spot["_id"])
                    else:
                        # For specific locations, use a tighter radius
                        if campus_dist <= distance_meters:
                            spot_ids_within_distance.append(spot["_id"])
            
            # Add filter for spots within distance
            if spot_ids_within_distance:
                query["_id"] = {"$in": spot_ids_within_distance}
            else:
                # No spots within distance, return empty array
                return jsonify({
                    'success': True,
                    'spots': [],
                    'total': 0,
                    'page': page,
                    'pages': 0
                })
        except ValueError:
            # Invalid coordinates, ignore distance filter
            pass
    
    # Count total spots matching the query
    total = db.study_spots.count_documents(query)
    
    # Calculate total pages
    total_pages = (total + limit - 1) // limit
    
    # Adjust page number if out of bounds
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Calculate skip
    skip = (page - 1) * limit
    
    # Set up sort
    sort_option = []
    if sort == 'distance' and user_lat and user_lng:
        # Use geospatial sorting
        # Note: This requires a geospatial index on the 'location' field
        # db.study_spots.create_index([("location", "2dsphere")])
        pass  # The $near operator in the query already sorts by distance
    elif sort == 'rating':
        sort_option = [('rating', -1)]
    elif sort == 'popular':
        sort_option = [('check_ins', -1)]
    elif sort == 'occupancy':
        # Sort by occupancy (low to high)
        # This uses a custom sort order for the occupancy_level field
        pipeline = [
            {'$match': query},
            {'$addFields': {
                'occupancy_order': {
                    '$switch': {
                        'branches': [
                            {'case': {'$eq': ['$occupancy_level', 'low']}, 'then': 1},
                            {'case': {'$eq': ['$occupancy_level', 'medium']}, 'then': 2},
                            {'case': {'$eq': ['$occupancy_level', 'high']}, 'then': 3}
                        ],
                        'default': 4
                    }
                }
            }},
            {'$sort': {'occupancy_order': 1}},
            {'$skip': skip},
            {'$limit': limit}
        ]
        spots_cursor = db.study_spots.aggregate(pipeline)
        spots = list(spots_cursor)
        
        # Format spots for response
        formatted_spots = []
        for spot in spots:
            # Format each spot
            spot['_id'] = str(spot['_id'])
            
            # Get latest occupancy report
            latest_report = db.occupancy_reports.find_one(
                {'spot_id': spot['_id']},
                sort=[('reported_at', -1)]
            )
            
            if latest_report:
                spot['occupancy_level'] = latest_report['occupancy_level']
            
            # Get creator info
            if 'created_by' in spot:
                creator = users_collection.find_one({'_id': ObjectId(spot['created_by'])})
                if creator:
                    spot['creator'] = {
                        'username': creator['username'],
                        'avatar_id': creator.get('avatar_id', 'default')
                    }
            
            # Count check-ins
            check_ins_count = db.check_ins.count_documents({'spot_id': spot['_id']})
            spot['check_ins'] = check_ins_count
            
            formatted_spots.append(spot)
        
        return jsonify({
            'success': True,
            'spots': formatted_spots,
            'total': total,
            'page': page,
            'pages': total_pages
        })
    else:
        # Default sort by creation date (newest first)
        sort_option = [('created_at', -1)]
    
    # Fetch spots
    if sort_option:
        spots_cursor = db.study_spots.find(query).sort(sort_option).skip(skip).limit(limit)
    else:
        spots_cursor = db.study_spots.find(query).skip(skip).limit(limit)
    
    # Convert to list and format for frontend
    spots = []
    for spot in spots_cursor:
        # Format spot
        spot['_id'] = str(spot['_id'])
        
        # Get latest occupancy report
        latest_report = db.occupancy_reports.find_one(
            {'spot_id': spot['_id']},
            sort=[('reported_at', -1)]
        )
        
        if latest_report:
            spot['occupancy_level'] = latest_report['occupancy_level']
        
        # Get creator info
        if 'created_by' in spot:
            creator = users_collection.find_one({'_id': ObjectId(spot['created_by'])})
            if creator:
                spot['creator'] = {
                    'username': creator['username'],
                    'avatar_id': creator.get('avatar_id', 'default')
                }
        
        # Count check-ins
        check_ins_count = db.check_ins.count_documents({'spot_id': spot['_id']})
        spot['check_ins'] = check_ins_count
        
        spots.append(spot)
    
    return jsonify({
        'success': True,
        'spots': spots,
        'total': total,
        'page': page,
        'pages': total_pages
    })

# API route to get a single study spot
@app.route('/api/studyspots/<spot_id>')
def get_studyspot(spot_id):
    """Get a single study spot by ID"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Find spot
    try:
        spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid spot ID'})
    
    if not spot:
        return jsonify({'success': False, 'message': 'Study spot not found'})
    
    # Format spot
    spot['_id'] = str(spot['_id'])
    
    # Get latest occupancy report
    latest_report = db.occupancy_reports.find_one(
        {'spot_id': spot['_id']},
        sort=[('reported_at', -1)]
    )
    
    if latest_report:
        spot['occupancy_level'] = latest_report['occupancy_level']
    
    # Get creator info
    if 'created_by' in spot:
        creator = users_collection.find_one({'_id': ObjectId(spot['created_by'])})
        if creator:
            spot['creator'] = {
                'username': creator['username'],
                'avatar_id': creator.get('avatar_id', 'default')
            }
    
    # Count check-ins
    check_ins_count = db.check_ins.count_documents({'spot_id': spot['_id']})
    spot['check_ins'] = check_ins_count
    
    # Get reviews
    reviews_cursor = db.spot_reviews.find({'spot_id': spot['_id']}).sort('created_at', -1).limit(5)
    reviews = []
    
    for review in reviews_cursor:
        # Get author info
        author = users_collection.find_one({'_id': ObjectId(review['user_id'])})
        
        if author:
            author_info = {
                'username': author['username'],
                'avatar_id': author.get('avatar_id', 'default')
            }
        else:
            author_info = {
                'username': 'Deleted User',
                'avatar_id': 'default'
            }
        
        # Format review
        formatted_review = {
            '_id': str(review['_id']),
            'content': review['content'],
            'rating': review['rating'],
            'created_at': review['created_at'].isoformat(),
            'author': author_info
        }
        
        reviews.append(formatted_review)
    
    # Add reviews to spot data
    spot['reviews'] = reviews
    
    # Check if user has favorited this spot
    user_favorite = db.favorite_spots.find_one({
        'spot_id': spot['_id'],
        'user_id': session['user_id']
    })
    
    spot['is_favorited'] = bool(user_favorite)
    
    return jsonify({
        'success': True,
        'spot': spot
    })

# API route to create a new study spot
@app.route('/api/studyspots', methods=['POST'])
def create_studyspot():
    """Create a new study spot"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Get request data
    data = request.form  # Using form data for file upload
    
    # Validate required fields
    required_fields = ['name', 'address', 'description', 'campus']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'Missing required field: {field}'})
    
    # Process amenities JSON
    amenities = {}
    try:
        amenities_json = data.get('amenities', '{}')
        amenities = json.loads(amenities_json)
    except:
        # Default empty amenities
        amenities = {}
    
    # Ensure all amenity fields exist
    amenity_fields = ['wifi', 'outlets', 'quiet', 'group_friendly', 'food_allowed', 
                      'computers', 'printing', 'whiteboard', 'natural_light']
    
    for field in amenity_fields:
        if field not in amenities:
            amenities[field] = False
    
    # Process coordinates
    coordinates = None
    if data.get('latitude') and data.get('longitude'):
        try:
            lat = float(data.get('latitude'))
            lng = float(data.get('longitude'))
            coordinates = [lng, lat]  # GeoJSON format: [longitude, latitude]
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid coordinates'})
    
    # Handle photo uploads
    photos = []
    if 'photos' in request.files:
        photo_files = request.files.getlist('photos')
        
        for photo in photo_files:
            if photo and photo.filename and allowed_file(photo.filename):
                # Generate secure filename
                filename = secure_filename(photo.filename)
                
                # Add timestamp for uniqueness
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"studyspot_{timestamp}_{filename}"
                
                # Save file
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(file_path)
                
                # Add to photos list
                photos.append(f"/uploads/{filename}")
    
    # Create study spot
    study_spot = {
        'name': data.get('name'),
        'address': data.get('address'),
        'description': data.get('description'),
        'campus': data.get('campus'),
        'amenities': amenities,
        'photos': photos,
        'occupancy_level': 'low',  # Default occupancy
        'verified': False,  # New spots are unverified until reviewed
        'created_by': user_id,
        'created_at': datetime.now()
    }
    
    # Add location data if coordinates are available
    if coordinates:
        study_spot['location'] = {
            'type': 'Point',
            'coordinates': coordinates
        }
    
    # Insert study spot
    result = db.study_spots.insert_one(study_spot)
    spot_id = result.inserted_id
    
    # Award coins for contributing a new study spot
    award_amount = 50
    new_balance = user.get('coins_balance', 0) + award_amount
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'coins_balance': new_balance}}
    )
    
    # Record coin transaction
    transaction = {
        'user_id': user_id,
        'amount': award_amount,
        'transaction_type': 'spot_contribution',
        'reference_id': str(spot_id),
        'description': f'Added study spot: {data.get("name")}',
        'created_at': datetime.now()
    }
    db.coin_transactions.insert_one(transaction)
    
    return jsonify({
        'success': True,
        'message': f'Study spot added successfully! You earned {award_amount} coins.',
        'spot_id': str(spot_id),
        'new_balance': new_balance
    })

# API route for checking in to a study spot
@app.route('/api/studyspots/checkin', methods=['POST'])
def checkin_studyspot():
    """Check in to a study spot"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    data = request.get_json()
    spot_id = data.get('spot_id')
    duration = data.get('duration', 1)  # Default 1 hour
    occupancy_level = data.get('occupancy_level')
    
    # Validate data
    if not spot_id:
        return jsonify({'success': False, 'message': 'Study spot ID is required'})
    
    if occupancy_level not in ['low', 'medium', 'high']:
        return jsonify({'success': False, 'message': 'Invalid occupancy level'})
    
    # Find spot
    try:
        spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid spot ID'})
    
    if not spot:
        return jsonify({'success': False, 'message': 'Study spot not found'})
    
    # Check if user already has an active check-in
    now = datetime.now()
    active_checkin = db.check_ins.find_one({
        'user_id': user_id,
        'spot_id': spot_id,
        'check_out_time': {'$gt': now}
    })
    
    if active_checkin:
        return jsonify({'success': False, 'message': 'You are already checked in to this spot'})
    
    # Create check-in
    check_in_time = now
    check_out_time = now + timedelta(hours=duration)
    
    check_in = {
        'user_id': user_id,
        'spot_id': spot_id,
        'check_in_time': check_in_time,
        'check_out_time': check_out_time,
        'reported_occupancy': occupancy_level,
        'created_at': now
    }
    
    # Insert check-in
    db.check_ins.insert_one(check_in)
    
    # Report occupancy
    occupancy_report = {
        'user_id': user_id,
        'spot_id': spot_id,
        'occupancy_level': occupancy_level,
        'reported_at': now
    }
    
    db.occupancy_reports.insert_one(occupancy_report)
    
    # Award coins for checking in
    award_amount = 5
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$inc': {'coins_balance': award_amount}}
    )
    
    # Record coin transaction
    transaction = {
        'user_id': user_id,
        'amount': award_amount,
        'transaction_type': 'spot_checkin',
        'reference_id': spot_id,
        'description': f'Checked in at: {spot["name"]}',
        'created_at': now
    }
    db.coin_transactions.insert_one(transaction)
    
    # Get updated spot with new occupancy level
    updated_spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    updated_spot['_id'] = str(updated_spot['_id'])
    updated_spot['occupancy_level'] = occupancy_level
    
    # Get creator info
    if 'created_by' in updated_spot:
        creator = users_collection.find_one({'_id': ObjectId(updated_spot['created_by'])})
        if creator:
            updated_spot['creator'] = {
                'username': creator['username'],
                'avatar_id': creator.get('avatar_id', 'default')
            }
    
    # Count check-ins
    check_ins_count = db.check_ins.count_documents({'spot_id': spot_id})
    updated_spot['check_ins'] = check_ins_count
    
    return jsonify({
        'success': True,
        'message': f'Checked in successfully! You earned {award_amount} coins.',
        'spot': updated_spot
    })

# API route for reporting occupancy
@app.route('/api/studyspots/occupancy', methods=['POST'])
def report_occupancy():
    """Report occupancy for a study spot"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    data = request.get_json()
    spot_id = data.get('spot_id')
    occupancy_level = data.get('occupancy_level')
    
    # Validate data
    if not spot_id:
        return jsonify({'success': False, 'message': 'Study spot ID is required'})
    
    if occupancy_level not in ['low', 'medium', 'high']:
        return jsonify({'success': False, 'message': 'Invalid occupancy level'})
    
    # Find spot
    try:
        spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid spot ID'})
    
    if not spot:
        return jsonify({'success': False, 'message': 'Study spot not found'})
    
    # Check if user has reported occupancy recently (in the last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_report = db.occupancy_reports.find_one({
        'user_id': user_id,
        'spot_id': spot_id,
        'reported_at': {'$gt': one_hour_ago}
    })
    
    if recent_report:
        return jsonify({
            'success': False, 
            'message': 'You have already reported occupancy for this spot recently. Please wait before reporting again.'
        })
    
    # Create occupancy report
    occupancy_report = {
        'user_id': user_id,
        'spot_id': spot_id,
        'occupancy_level': occupancy_level,
        'reported_at': datetime.now()
    }
    
    # Insert occupancy report
    db.occupancy_reports.insert_one(occupancy_report)
    
    # Award coins for reporting occupancy
    award_amount = 2
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$inc': {'coins_balance': award_amount}}
    )
    
    # Record coin transaction
    transaction = {
        'user_id': user_id,
        'amount': award_amount,
        'transaction_type': 'spot_occupancy_report',
        'reference_id': spot_id,
        'description': f'Reported occupancy at: {spot["name"]}',
        'created_at': datetime.now()
    }
    db.coin_transactions.insert_one(transaction)
    
    # Get updated spot with new occupancy level
    updated_spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    updated_spot['_id'] = str(updated_spot['_id'])
    updated_spot['occupancy_level'] = occupancy_level
    
    # Get creator info
    if 'created_by' in updated_spot:
        creator = users_collection.find_one({'_id': ObjectId(updated_spot['created_by'])})
        if creator:
            updated_spot['creator'] = {
                'username': creator['username'],
                'avatar_id': creator.get('avatar_id', 'default')
            }
    
    # Count check-ins
    check_ins_count = db.check_ins.count_documents({'spot_id': spot_id})
    updated_spot['check_ins'] = check_ins_count
    
    return jsonify({
        'success': True,
        'message': f'Occupancy reported successfully! You earned {award_amount} coins.',
        'spot': updated_spot
    })

# API route for adding/removing favorites
@app.route('/api/studyspots/<spot_id>/favorite', methods=['POST'])
def toggle_favorite_spot(spot_id):
    """Add or remove a study spot from favorites"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Find spot
    try:
        spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid spot ID'})
    
    if not spot:
        return jsonify({'success': False, 'message': 'Study spot not found'})
    
    # Check if user has already favorited this spot
    existing_favorite = db.favorite_spots.find_one({
        'user_id': user_id,
        'spot_id': spot_id
    })
    
    if existing_favorite:
        # Remove from favorites
        db.favorite_spots.delete_one({'_id': existing_favorite['_id']})
        return jsonify({
            'success': True,
            'message': 'Removed from favorites',
            'is_favorited': False
        })
    else:
        # Add to favorites
        favorite = {
            'user_id': user_id,
            'spot_id': spot_id,
            'created_at': datetime.now()
        }
        
        db.favorite_spots.insert_one(favorite)
        
        return jsonify({
            'success': True,
            'message': 'Added to favorites',
            'is_favorited': True
        })

# API route for adding a review
@app.route('/api/studyspots/<spot_id>/review', methods=['POST'])
def add_review(spot_id):
    """Add a review for a study spot"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    data = request.get_json()
    
    content = data.get('content')
    rating = data.get('rating')
    
    # Validate data
    if not content:
        return jsonify({'success': False, 'message': 'Review content is required'})
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Rating must be a number between 1 and 5'})
    
    # Find spot
    try:
        spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid spot ID'})
    
    if not spot:
        return jsonify({'success': False, 'message': 'Study spot not found'})
    
    # Check if user has already reviewed this spot
    existing_review = db.spot_reviews.find_one({
        'user_id': user_id,
        'spot_id': spot_id
    })
    
    if existing_review:
        # Update existing review
        db.spot_reviews.update_one(
            {'_id': existing_review['_id']},
            {'$set': {
                'content': content,
                'rating': rating,
                'updated_at': datetime.now()
            }}
        )
        
        # Calculate new average rating
        update_spot_rating(spot_id)
        
        return jsonify({
            'success': True,
            'message': 'Review updated successfully'
        })
    else:
        # Create new review
        review = {
            'user_id': user_id,
            'spot_id': spot_id,
            'content': content,
            'rating': rating,
            'created_at': datetime.now()
        }
        
        # Insert review
        result = db.spot_reviews.insert_one(review)
        
        # Calculate new average rating
        update_spot_rating(spot_id)
        
        # Award coins for first review
        award_amount = 10
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$inc': {'coins_balance': award_amount}}
        )
        
        # Record coin transaction
        transaction = {
            'user_id': user_id,
            'amount': award_amount,
            'transaction_type': 'spot_review',
            'reference_id': str(result.inserted_id),
            'description': f'Reviewed study spot: {spot["name"]}',
            'created_at': datetime.now()
        }
        db.coin_transactions.insert_one(transaction)
        
        return jsonify({
            'success': True,
            'message': f'Review added successfully! You earned {award_amount} coins.',
            'review_id': str(result.inserted_id)
        })

# Helper function to update a spot's average rating
def update_spot_rating(spot_id):
    """Calculate and update the average rating for a study spot"""
    # Get all reviews for this spot
    reviews = list(db.spot_reviews.find({'spot_id': spot_id}))
    
    if not reviews:
        # No reviews, set rating to None
        db.study_spots.update_one(
            {'_id': ObjectId(spot_id)},
            {'$set': {'rating': None}}
        )
        return
    
    # Calculate average rating
    total_rating = sum(review['rating'] for review in reviews)
    average_rating = total_rating / len(reviews)
    
    # Update spot with new rating
    db.study_spots.update_one(
        {'_id': ObjectId(spot_id)},
        {'$set': {'rating': average_rating}}
    )

# Route to handle spot verification (admin only)
@app.route('/api/studyspots/<spot_id>/verify', methods=['POST'])
def verify_spot(spot_id):
    """Verify a study spot (admin only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Check if user is an admin
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if not user or user.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized. Admin access required.'})
    
    # Find spot
    try:
        spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid spot ID'})
    
    if not spot:
        return jsonify({'success': False, 'message': 'Study spot not found'})
    
    # Update spot as verified
    db.study_spots.update_one(
        {'_id': ObjectId(spot_id)},
        {'$set': {'verified': True}}
    )
    
    # Award coins to creator
    creator_id = spot.get('created_by')
    if creator_id:
        award_amount = 30
        users_collection.update_one(
            {'_id': ObjectId(creator_id)},
            {'$inc': {'coins_balance': award_amount}}
        )
        
        # Record coin transaction
        transaction = {
            'user_id': creator_id,
            'amount': award_amount,
            'transaction_type': 'spot_verification',
            'reference_id': spot_id,
            'description': f'Study spot verified: {spot["name"]}',
            'created_at': datetime.now()
        }
        db.coin_transactions.insert_one(transaction)
    
    return jsonify({
        'success': True,
        'message': 'Study spot verified successfully'
    })

# Route to delete a study spot (admin or creator only)
@app.route('/api/studyspots/<spot_id>', methods=['DELETE'])
def delete_spot(spot_id):
    """Delete a study spot (admin or creator only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Find spot
    try:
        spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid spot ID'})
    
    if not spot:
        return jsonify({'success': False, 'message': 'Study spot not found'})
    
    # Check permissions
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    is_admin = user and user.get('role') == 'admin'
    is_creator = spot.get('created_by') == user_id
    
    if not (is_admin or is_creator):
        return jsonify({'success': False, 'message': 'Unauthorized. Only the creator or an admin can delete this spot.'})
    
    # Delete photos if they exist
    if 'photos' in spot and spot['photos']:
        for photo_url in spot['photos']:
            if photo_url.startswith('/uploads/'):
                filename = photo_url.replace('/uploads/', '')
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error removing photo file: {str(e)}")
    
    # Delete related records
    db.check_ins.delete_many({'spot_id': spot_id})
    db.occupancy_reports.delete_many({'spot_id': spot_id})
    db.spot_reviews.delete_many({'spot_id': spot_id})
    db.favorite_spots.delete_many({'spot_id': spot_id})
    
    # Delete spot
    db.study_spots.delete_one({'_id': ObjectId(spot_id)})
    
    return jsonify({
        'success': True,
        'message': 'Study spot deleted successfully'
    })

# Route to get nearby users at a study spot
@app.route('/api/studyspots/<spot_id>/users')
def get_spot_users(spot_id):
    """Get users currently checked in at a study spot"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Find spot
    try:
        spot = db.study_spots.find_one({'_id': ObjectId(spot_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid spot ID'})
    
    if not spot:
        return jsonify({'success': False, 'message': 'Study spot not found'})
    
    # Find active check-ins
    now = datetime.now()
    active_checkins = list(db.check_ins.find({
        'spot_id': spot_id,
        'check_out_time': {'$gt': now}
    }))
    
    # Get user details
    users = []
    for checkin in active_checkins:
        checkin_user = users_collection.find_one({'_id': ObjectId(checkin['user_id'])})
        if checkin_user and checkin_user['_id'] != ObjectId(user_id):  # Exclude current user
            users.append({
                'username': checkin_user['username'],
                'avatar_id': checkin_user.get('avatar_id', 'default'),
                'department': checkin_user.get('department', 'Unknown'),
                'check_in_time': checkin['check_in_time'].isoformat(),
                'check_out_time': checkin['check_out_time'].isoformat()
            })
    
    return jsonify({
        'success': True,
        'users': users,
        'count': len(users)
    })

# Create necessary indexes for study spots collection
def create_studyspot_indexes():
    """Create indexes for the study spots collection"""
    try:
        # Create geospatial index for location-based queries
        db.study_spots.create_index([("location", "2dsphere")])
        
        # Create text index for search
        db.study_spots.create_index([
            ("name", "text"), 
            ("description", "text"),
            ("address", "text")
        ])
        
        # Create indexes for common query fields
        db.study_spots.create_index("campus")
        db.study_spots.create_index("created_by")
        db.study_spots.create_index("created_at")
        db.study_spots.create_index("rating")
        
        # Create indexes for related collections
        db.check_ins.create_index([("spot_id", 1), ("user_id", 1)])
        db.check_ins.create_index([("check_out_time", 1)])
        
        db.occupancy_reports.create_index([("spot_id", 1)])
        db.occupancy_reports.create_index([("reported_at", -1)])
        
        db.spot_reviews.create_index([("spot_id", 1), ("user_id", 1)])
        
        db.favorite_spots.create_index([("user_id", 1), ("spot_id", 1)], unique=True)
        
        print("Study spot indexes created successfully")
        return True
    except Exception as e:
        print(f"Error creating study spot indexes: {str(e)}")
        return False


@app.route('/spotify-control', methods=['POST'])
def spotify_control():
    """Control Spotify playback"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user or 'spotify_token' not in user:
        return jsonify({'success': False, 'message': 'No Spotify account connected'})
    
    data = request.get_json()
    action = data.get('action')  # play, pause, next, previous
    
    access_token = user['spotify_token']
    
    # Check if token is expired and refresh if needed
    if user.get('spotify_token_expiry', 0) < datetime.now().timestamp():
        access_token = refresh_spotify_token(user['spotify_refresh_token'])
    
    try:
        if action == 'play':
            response = requests.put('https://api.spotify.com/v1/me/player/play', 
                                   headers={'Authorization': f'Bearer {access_token}'})
        elif action == 'pause':
            response = requests.put('https://api.spotify.com/v1/me/player/pause', 
                                   headers={'Authorization': f'Bearer {access_token}'})
        elif action == 'next':
            response = requests.post('https://api.spotify.com/v1/me/player/next', 
                                    headers={'Authorization': f'Bearer {access_token}'})
        elif action == 'previous':
            response = requests.post('https://api.spotify.com/v1/me/player/previous', 
                                    headers={'Authorization': f'Bearer {access_token}'})
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
        
        if response.status_code not in [200, 204]:
            return jsonify({'success': False, 'message': f'Failed to control playback: {response.text}'})
        
        return jsonify({'success': True, 'message': f'Successfully performed {action}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Avatar Management
@app.route('/update-avatar', methods=['POST'])
def update_avatar():
    """Update user's avatar"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    avatar_id = data.get('avatar_id')
    
    if not avatar_id:
        return jsonify({'success': False, 'message': 'No avatar selected'})
    
    # Update user's avatar in database
    users_collection.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'avatar_id': avatar_id}}
    )
    
    return jsonify({'success': True, 'message': 'Avatar updated successfully'})

# Update voxel avatar
@app.route('/update-voxel-avatar', methods=['POST'])
def update_voxel_avatar():
    """Update user's voxel avatar"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    voxel_avatar_id = data.get('voxel_avatar_id')
    
    if not voxel_avatar_id:
        return jsonify({'success': False, 'message': 'No voxel avatar selected'})
    
    # Update user's voxel avatar in database
    users_collection.update_one(
        {'_id': ObjectId(session['user_id'])},
        {'$set': {'voxel_avatar_id': voxel_avatar_id}}
    )
    
    return jsonify({'success': True, 'message': 'Voxel avatar updated successfully'})

# Calendar Event API
@app.route('/save-calendar-event', methods=['POST'])
def save_calendar_event():
    """Save a calendar event"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    user_id = session['user_id']
    
    # Validate event data
    event = {
        'title': data.get('title'),
        'date': datetime.fromisoformat(data.get('date').replace('Z', '+00:00')),
        'duration': data.get('duration', 60),
        'color': data.get('color', '#7b3eab')
    }
    
    # Get user's existing events
    calendar_data = calendar_events_collection.find_one({'user_id': user_id})
    
    if calendar_data and 'events' in calendar_data:
        events = calendar_data['events']
        events.append(event)
        
        # Update events in database
        calendar_events_collection.update_one(
            {'user_id': user_id},
            {'$set': {'events': events}}
        )
    else:
        # Create new events document
        calendar_events_collection.insert_one({
            'user_id': user_id,
            'events': [event]
        })
    
    return jsonify({'success': True, 'message': 'Event saved successfully'})

# Database Reset Function (helper for database management)
@app.route('/dev/reset-firebase-users', methods=['POST'])
def reset_firebase_users():
    """Admin-only route to delete Firebase users"""
    # This should be protected with proper authentication in production
    try:
        from firebase_admin import auth
        
        # Get users in batches (Firebase limits to 1000 per request)
        page = auth.list_users()
        deleted_count = 0
        
        for user in page.users:
            try:
                auth.delete_user(user.uid)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting user {user.uid}: {e}")
        
        return jsonify({
            'success': True, 
            'message': f'Successfully deleted {deleted_count} Firebase users'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Success Animation
@app.route('/success')
def success():
    print("Session at success page:", dict(session))
    
    # Make session permanent again to be extra sure
    session.permanent = True
    
    # Use user_id from session or URL parameter
    user_id = session.get('user_id') or request.args.get('uid')
    
    if not user_id:
        flash('Session data missing. Please login again.', 'error')
        return redirect(url_for('login_page'))
    
    # If user_id is not in session but in URL, rebuild session
    if 'user_id' not in session and user_id:
        try:
            user = users_collection.find_one({'_id': ObjectId(user_id)})
            if user:
                session['user_id'] = user_id
                session['email'] = user.get('email')
                session['username'] = user.get('username')
                session['onboarded'] = True
                session.permanent = True
                print(f"Rebuilt session from uid param: {dict(session)}")
        except Exception as e:
            print(f"Error rebuilding session: {str(e)}")
            flash('Error processing your profile. Please login again.', 'error')
            return redirect(url_for('login_page'))
    
    # Double-check the user is fully onboarded in database
    try:
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'onboarded': True}}
        )
    except Exception as e:
        print(f"Error setting onboarded status: {str(e)}")
    
    # Pass the user_id to the template
    return render_template('success.html', uid=user_id)
# Add these imports to your existing imports

# Add these routes to your existing app.py file

@app.route('/bounties')
def bounties_page():
    """Render the bounties page"""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        return redirect(url_for('login_page'))
        
    return render_template('bounty.html', user=user)

# API route to get user data
# API route to get user data
@app.route('/get-user-data')
def get_user_data():
    """Get user data for the bounty page"""
    print("Session data in get-user-data:", dict(session))
    
    if 'user_id' not in session:
        print("User ID not in session")
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    print(f"Looking up user with ID: {user_id}")
    
    try:
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            print(f"User with ID {user_id} not found in database")
            return jsonify({'success': False, 'message': 'User not found'})
        
        # Create a serializable user object
        user_data = {
            '_id': str(user['_id']),
            'username': user.get('username', ''),
            'email': user.get('email', ''),
            'avatar_id': user.get('avatar_id', 'default'),
            'university': user.get('university', ''),
            'department': user.get('department', ''),
            'interests': user.get('interests', []),
            'coins_balance': user.get('coins_balance', 0),
            'github_username': user.get('github_username', None),
            'auth_method': user.get('auth_method', 'email_password')
        }
        
        print(f"Successfully retrieved user data for {user.get('username')}")
        return jsonify({'success': True, 'user': user_data})
    except Exception as e:
        print(f"Error retrieving user data: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
# API route to get categories
@app.route('/api/categories')
def get_categories():
    """Get all categories used in bounties"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Fetch unique categories directly from the bounties collection
        pipeline = [
            {"$group": {"_id": "$category"}},
            {"$match": {"_id": {"$ne": None}}},
            {"$sort": {"_id": 1}}
        ]
        
        unique_categories = list(db.bounties.aggregate(pipeline))
        
        # Map of default icons for common categories
        default_icons = {
            'Computer Science': 'fa-laptop-code',
            'Business': 'fa-chart-line',
            'Law': 'fa-balance-scale',
            'Medicine': 'fa-heartbeat',
            'Engineering': 'fa-cogs',
            'Science': 'fa-atom',
            'Humanities': 'fa-book',
            'Arts': 'fa-paint-brush',
            'Data Science': 'fa-database',
            'Artificial Intelligence': 'fa-brain',
            'Economics': 'fa-chart-bar',
            'Finance': 'fa-dollar-sign',
            'Marketing': 'fa-ad',
            'Psychology': 'fa-brain',
            'History': 'fa-history',
            'Literature': 'fa-book-open',
            'Mathematics': 'fa-calculator'
        }
        
        # Format categories for frontend
        categories = []
        for category_doc in unique_categories:
            category_name = category_doc.get('_id')
            if category_name:  # Skip any None categories
                categories.append({
                    '_id': category_name,
                    'name': category_name,
                    'icon': default_icons.get(category_name, 'fa-tag')
                })
        
        print(f"Found {len(categories)} categories")
        
        # Add default categories if none found
        if not categories:
            default_categories = [
                {'name': 'Computer Science', 'icon': 'fa-laptop-code'},
                {'name': 'Business', 'icon': 'fa-chart-line'},
                {'name': 'Law', 'icon': 'fa-balance-scale'},
                {'name': 'Medicine', 'icon': 'fa-heartbeat'},
                {'name': 'Engineering', 'icon': 'fa-cogs'},
                {'name': 'Science', 'icon': 'fa-atom'},
                {'name': 'Humanities', 'icon': 'fa-book'},
                {'name': 'Arts', 'icon': 'fa-paint-brush'}
            ]
            
            for category in default_categories:
                categories.append({
                    '_id': category['name'],
                    'name': category['name'],
                    'icon': category['icon']
                })
        
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        print(f"Error fetching categories: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})



# API route to create a category
@app.route('/api/categories', methods=['POST'])
def create_category():
    """Create a new category"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    data = request.get_json()
    name = data.get('name')
    icon = data.get('icon', 'fa-tag')  # Default icon if none provided
    
    if not name:
        return jsonify({'success': False, 'message': 'Category name is required'})
    
    try:
        # Check if category already exists
        existing_category = db.categories.find_one({'name': {'$regex': f'^{name}$', '$options': 'i'}})
        if existing_category:
            return jsonify({'success': False, 'message': 'A category with this name already exists'})
        
        # Create new category
        category = {
            'name': name,
            'icon': icon,
            'created_by': session['user_id'],
            'created_at': datetime.now()
        }
        
        result = db.categories.insert_one(category)
        
        return jsonify({
            'success': True,
            'message': 'Category created successfully',
            'category_id': str(result.inserted_id)
        })
    except Exception as e:
        print(f"Error creating category: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

# API route to get bounties
@app.route('/api/bounties')
def get_bounties():
    """Get bounties with filtering and pagination"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Get query parameters
    filter_type = request.args.get('filter', 'all')
    category = request.args.get('category')
    complexity = request.args.get('complexity')
    status = request.args.get('status')
    sort = request.args.get('sort', 'latest')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 12))
    
    # Base query
    query = {}
    
    # Apply filter
   # Apply filter
    if filter_type == 'interests':
    # Show bounties that match user's interests (case insensitive)
        user_interests = user.get('interests', [])
        if user_interests:
            # Convert interests to lowercase for case-insensitive comparison
            user_interests_lower = [interest.lower() for interest in user_interests]
            
            # Find bounties that have tags matching any user interest (case insensitive)
            query['$or'] = []
            for interest in user_interests_lower:
                query['$or'].append({'tags': {'$elemMatch': {'$regex': f"^{re.escape(interest)}$", '$options': 'i'}}})
        if user_interests:
            query['tags'] = {'$in': user_interests}
    elif filter_type == 'department':
        # Show bounties from user's department
        query['category'] = user.get('department')
    elif filter_type == 'created':
        # Show bounties created by the user
        query['creator_id'] = str(user['_id'])
    #In the get_bounties API route in app.py
    elif filter_type == 'solved':
        # Show bounties where the user has submitted a response
        user_responses = list(db.bounty_responses.find(
            {'responder_id': str(user['_id'])}
        ))
        
        if user_responses:
            # Extract bounty IDs as strings (not ObjectId)
            bounty_ids = [resp['bounty_id'] for resp in user_responses]
            # Create list of ObjectIds for query
            bounty_object_ids = [ObjectId(bid) for bid in bounty_ids]
            query['_id'] = {'$in': bounty_object_ids}
        else:
            # No responses, return empty array
            return jsonify({
                'success': True,
                'bounties': [],
                'total': 0,
                'page': page,
                'pages': 0
            })
    
    # Apply additional filters
    if category:
        query['category'] = category
    
    if complexity:
        query['complexity'] = int(complexity)
    
    if status:
        query['status'] = status
    
    if search:
        # Search in title and description
        query['$or'] = [
            {'title': {'$regex': search, '$options': 'i'}},
            {'description': {'$regex': search, '$options': 'i'}}
        ]
    
    # Count total bounties matching the query
    total = db.bounties.count_documents(query)
    
    # Calculate total pages
    total_pages = (total + limit - 1) // limit
    
    # Adjust page number if out of bounds
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Calculate skip
    skip = (page - 1) * limit
    
    # Set up sort
    sort_option = {}
    if sort == 'latest':
        sort_option = [('created_at', -1)]
    elif sort == 'reward':
        sort_option = [('reward', -1)]
    elif sort == 'popular':
        sort_option = [('response_count', -1)]
    elif sort == 'relevance':
        # Relevance is more complex, would require query scoring
        # For now, just sort by a combination of recency and reward
        sort_option = [('reward', -1), ('created_at', -1)]
    
    # Fetch bounties
    bounties_cursor = db.bounties.find(query).sort(sort_option).skip(skip).limit(limit)
    
    # Convert to list and format for frontend
    bounties = []
    for bounty in bounties_cursor:
        # Format bounty
        formatted_bounty = {
            '_id': str(bounty['_id']),
            'title': bounty['title'],
            'description': bounty['description'],
            'category': bounty['category'],
            'complexity': bounty['complexity'],
            'reward': bounty['reward'],
            'status': bounty['status'],
            'created_at': bounty['created_at'].isoformat(),
            'tags': bounty['tags'],
            'response_count': bounty.get('response_count', 0)
        }
        
        bounties.append(formatted_bounty)
    
    return jsonify({
        'success': True,
        'bounties': bounties,
        'total': total,
        'page': page,
        'pages': total_pages
    })

# API route to get single bounty
@app.route('/api/bounties/<bounty_id>')
def get_bounty(bounty_id):
    """Get a single bounty by ID"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    # Find bounty
    try:
        bounty = db.bounties.find_one({'_id': ObjectId(bounty_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid bounty ID'})
    
    if not bounty:
        return jsonify({'success': False, 'message': 'Bounty not found'})
    
    # Get creator info
    creator = users_collection.find_one({'_id': ObjectId(bounty['creator_id'])})
    if not creator:
        creator = {
            '_id': 'deleted',
            'username': 'Deleted User',
            'avatar_id': 'default',
            'university': 'Unknown',
            'department': 'Unknown'
        }
    
    # Format creator data
    creator_data = {
        '_id': str(creator['_id']),
        'username': creator['username'],
        'avatar_id': creator.get('avatar_id', 'default'),
        'university': creator.get('university', 'Unknown'),
        'department': creator.get('department', 'Unknown')
    }
    
    # Format bounty
    formatted_bounty = {
        '_id': str(bounty['_id']),
        'title': bounty['title'],
        'description': bounty['description'],
        'category': bounty['category'],
        'complexity': bounty['complexity'],
        'reward': bounty['reward'],
        'status': bounty['status'],
        'created_at': bounty['created_at'].isoformat(),
        'closed_at': bounty.get('closed_at', '').isoformat() if bounty.get('closed_at') else None,
        'tags': bounty['tags'],
        'creator': creator_data
    }
    
    return jsonify({
        'success': True,
        'bounty': formatted_bounty
    })

# API route to create a bounty
@app.route('/api/bounties', methods=['POST'])
def create_bounty():
    """Create a new bounty"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Get request data
    data = request.form  # Using form data for file upload

    # Validate required fields
    required_fields = ['title', 'description', 'category', 'complexity']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'Missing required field: {field}'})
    
    # Validate complexity
    complexity = int(data['complexity'])
    if complexity < 1 or complexity > 5:
        return jsonify({'success': False, 'message': 'Complexity must be between 1 and 5'})
    
    # Calculate reward based on complexity
    reward = 25  # Default for levels 1-2
    if complexity >= 3 and complexity <= 4:
        reward = 50
    elif complexity == 5:
        reward = 75
    
    # Check if user has enough coins
    if user.get('coins_balance', 0) < reward:
        return jsonify({'success': False, 'message': f'Not enough coins. You need {reward} coins to create this bounty.'})
    
    # Process tags
    tags = []
    tag_indices = [key for key in data.keys() if key.startswith('tags[')]
    for tag_key in tag_indices:
        tag = data.get(tag_key)
        if tag:
            tags.append(tag)
    
    if len(tags) > 5:
        return jsonify({'success': False, 'message': 'Maximum 5 tags allowed'})
    
    # Handle image upload if present
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp for uniqueness
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Set image URL for the bounty
            image_url = f"/uploads/{filename}"
    
    # Create bounty
    bounty = {
        'creator_id': str(user['_id']),
        'title': data['title'],
        'description': data['description'],
        'category': data['category'],
        'complexity': complexity,
        'reward': reward,
        'status': 'open',
        'created_at': datetime.now(),
        'tags': tags,
        'image_url': image_url,
        'response_count': 0
    }
    
    # Insert bounty
    result = db.bounties.insert_one(bounty)
    bounty_id = result.inserted_id
    
    # Deduct coins from user
    new_balance = user.get('coins_balance', 0) - reward
    users_collection.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'coins_balance': new_balance}}
    )
    
    # Record transaction
    transaction = {
        'user_id': str(user['_id']),
        'amount': -reward,
        'transaction_type': 'bounty_posting',
        'reference_id': str(bounty_id),
        'description': f'Posted bounty: {data["title"]}',
        'created_at': datetime.now()
    }
    db.coin_transactions.insert_one(transaction)
    
    return jsonify({
        'success': True,
        'message': 'Bounty created successfully',
        'bounty_id': str(bounty_id),
        'newBalance': new_balance
    })

# API route to get responses for a bounty
@app.route('/api/bounties/<bounty_id>/responses')
def get_responses(bounty_id):
    """Get responses for a bounty"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Find bounty
    try:
        bounty = db.bounties.find_one({'_id': ObjectId(bounty_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid bounty ID'})
    
    if not bounty:
        return jsonify({'success': False, 'message': 'Bounty not found'})
    
    # Find responses
    responses_cursor = db.bounty_responses.find({'bounty_id': bounty_id})
    
    # Convert to list and format for frontend
    responses = []
    for response in responses_cursor:
        # Get responder info
        responder = users_collection.find_one({'_id': ObjectId(response['responder_id'])})
        if not responder:
            responder = {
                '_id': 'deleted',
                'username': 'Deleted User',
                'avatar_id': 'default'
            }
        
        # Format responder data
        responder_data = {
            '_id': str(responder['_id']),
            'username': responder['username'],
            'avatar_id': responder.get('avatar_id', 'default')
        }
        
        # Check if current user has voted on this response
        user_vote = db.bounty_votes.find_one({
            'bounty_response_id': str(response['_id']),
            'user_id': str(user_id)
        })
        
        vote_type = user_vote.get('vote_type') if user_vote else None
        
        # Format response
        formatted_response = {
            '_id': str(response['_id']),
            'bounty_id': response['bounty_id'],
            'content': response['content'],
            'upvotes': response.get('upvotes', 0),
            'downvotes': response.get('downvotes', 0),
            'is_pinned': response.get('is_pinned', False),
            'created_at': response['created_at'].isoformat(),
            'responder': responder_data,
            'your_vote': vote_type  # Add user's vote info
        }
        
        responses.append(formatted_response)
    
    return jsonify({
        'success': True,
        'responses': responses
    })

# API route to create a response
@app.route('/api/responses', methods=['POST'])
def create_response():
    """Create a new response to a bounty"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Get request data
    data = request.get_json()
    bounty_id = data.get('bounty_id')
    content = data.get('content')
    
    # Validate required fields
    if not bounty_id or not content:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    # Validate content - check for empty HTML
    if content.strip() == '' or content == '<p><br></p>':
        return jsonify({'success': False, 'message': 'Response cannot be empty'})
    
    # Find bounty
    try:
        bounty = db.bounties.find_one({'_id': ObjectId(bounty_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid bounty ID'})
    
    if not bounty:
        return jsonify({'success': False, 'message': 'Bounty not found'})
    
    # Check if bounty is still open
    if bounty['status'] != 'open':
        return jsonify({'success': False, 'message': 'This bounty is closed'})
    
    # Check if user is the creator (creators should not answer their own bounties)
    if str(bounty['creator_id']) == str(user_id):
        return jsonify({'success': False, 'message': 'You cannot respond to your own bounty'})
    
    # Check if user already has a response for this bounty
    existing_response = db.bounty_responses.find_one({
        'bounty_id': bounty_id,
        'responder_id': str(user_id)
    })
    
    if existing_response:
        return jsonify({'success': False, 'message': 'You have already responded to this bounty'})
    
    # Create response
    response = {
        'bounty_id': bounty_id,
        'responder_id': str(user_id),
        'content': content,
        'upvotes': 0,
        'downvotes': 0,
        'is_pinned': False,
        'created_at': datetime.now()
    }
    
    # Insert response
    result = db.bounty_responses.insert_one(response)
    response_id = result.inserted_id
    
    # Update bounty response count
    db.bounties.update_one(
        {'_id': ObjectId(bounty_id)},
        {'$inc': {'response_count': 1}}
    )
    
    return jsonify({
        'success': True,
        'message': 'Response created successfully',
        'response_id': str(response_id)
    })

# API route to vote on a response
@app.route('/api/responses/<response_id>/vote', methods=['POST'])
def vote_response(response_id):
    """Vote on a response"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Get request data
    data = request.get_json()
    vote_type = data.get('vote_type')
    
    # Validate vote type
    if vote_type not in ['up', 'down']:
        return jsonify({'success': False, 'message': 'Invalid vote type'})
    
    # Find response
    try:
        response = db.bounty_responses.find_one({'_id': ObjectId(response_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid response ID'})
    
    if not response:
        return jsonify({'success': False, 'message': 'Response not found'})
    
    # Find bounty to check if it's still open
    bounty = db.bounties.find_one({'_id': ObjectId(response['bounty_id'])})
    if not bounty:
        return jsonify({'success': False, 'message': 'Bounty not found'})
    
    # Check if response belongs to user (users can't vote on their own responses)
    if response['responder_id'] == str(user_id):
        return jsonify({'success': False, 'message': 'You cannot vote on your own response'})
    
    # Check if user has already voted
    existing_vote = db.bounty_votes.find_one({
        'bounty_response_id': str(response_id),
        'user_id': str(user_id)
    })
    
    if existing_vote:
        # User is changing their vote
        if existing_vote['vote_type'] == vote_type:
            # Remove vote
            db.bounty_votes.delete_one({'_id': existing_vote['_id']})
            
            # Update response vote count
            if vote_type == 'up':
                db.bounty_responses.update_one(
                    {'_id': ObjectId(response_id)},
                    {'$inc': {'upvotes': -1}}
                )
            else:
                db.bounty_responses.update_one(
                    {'_id': ObjectId(response_id)},
                    {'$inc': {'downvotes': -1}}
                )
                
            return jsonify({
                'success': True,
                'message': 'Vote removed successfully'
            })
        else:
            # Change vote type
            db.bounty_votes.update_one(
                {'_id': existing_vote['_id']},
                {'$set': {'vote_type': vote_type}}
            )
            
            # Update response vote count
            if vote_type == 'up':
                db.bounty_responses.update_one(
                    {'_id': ObjectId(response_id)},
                    {'$inc': {'upvotes': 1, 'downvotes': -1}}
                )
            else:
                db.bounty_responses.update_one(
                    {'_id': ObjectId(response_id)},
                    {'$inc': {'upvotes': -1, 'downvotes': 1}}
                )
                
            return jsonify({
                'success': True,
                'message': 'Vote changed successfully'
            })
    else:
        # New vote
        vote = {
            'bounty_response_id': str(response_id),
            'user_id': str(user_id),
            'vote_type': vote_type,
            'created_at': datetime.now()
        }
        
        # Insert vote
        db.bounty_votes.insert_one(vote)
        
        # Update response vote count
        if vote_type == 'up':
            db.bounty_responses.update_one(
                {'_id': ObjectId(response_id)},
                {'$inc': {'upvotes': 1}}
            )
        else:
            db.bounty_responses.update_one(
                {'_id': ObjectId(response_id)},
                {'$inc': {'downvotes': 1}}
            )
            
        return jsonify({
            'success': True,
            'message': 'Vote recorded successfully'
        })

# API route to pin a response
@app.route('/api/responses/<response_id>/pin', methods=['POST'])
def pin_response(response_id):
    """Pin a response as the accepted answer"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Find response
    try:
        response = db.bounty_responses.find_one({'_id': ObjectId(response_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid response ID'})
    
    if not response:
        return jsonify({'success': False, 'message': 'Response not found'})
    
    # Find bounty
    bounty_id = response['bounty_id']
    try:
        bounty = db.bounties.find_one({'_id': ObjectId(bounty_id)})
    except:
        return jsonify({'success': False, 'message': 'Invalid bounty ID'})
    
    if not bounty:
        return jsonify({'success': False, 'message': 'Bounty not found'})
    
    # Check if user is the bounty creator
    if str(bounty['creator_id']) != str(user_id):
        return jsonify({'success': False, 'message': 'Only the bounty creator can pin a response'})
    
    # Check if bounty is still open
    if bounty['status'] != 'open':
        return jsonify({'success': False, 'message': 'This bounty is already closed'})
    
    # Check if a response is already pinned
    pinned_response = db.bounty_responses.find_one({
        'bounty_id': bounty_id,
        'is_pinned': True
    })
    
    if pinned_response:
        return jsonify({'success': False, 'message': 'A response is already pinned for this bounty'})
    
    # Find responder
    responder = users_collection.find_one({'_id': ObjectId(response['responder_id'])})
    if not responder:
        return jsonify({'success': False, 'message': 'Responder not found'})
    
    # Update response to mark as pinned
    db.bounty_responses.update_one(
        {'_id': ObjectId(response_id)},
        {'$set': {'is_pinned': True}}
    )
    
    # Update bounty to mark as closed
    db.bounties.update_one(
        {'_id': ObjectId(bounty_id)},
        {'$set': {'status': 'closed', 'closed_at': datetime.now()}}
    )
    
    # Award coins to responder
    reward = bounty['reward']
    new_responder_balance = responder.get('coins_balance', 0) + reward
    
    users_collection.update_one(
        {'_id': ObjectId(response['responder_id'])},
        {'$set': {'coins_balance': new_responder_balance}}
    )
    
    # Record transaction
    transaction = {
        'user_id': str(response['responder_id']),
        'amount': reward,
        'transaction_type': 'bounty_reward',
        'reference_id': str(response_id),
        'description': f'Reward for answer to: {bounty["title"]}',
        'created_at': datetime.now()
    }
    db.coin_transactions.insert_one(transaction)
    
    return jsonify({
        'success': True,
        'message': f'Response pinned successfully. {reward} coins awarded to {responder["username"]}.',
        'newBalance': user.get('coins_balance', 0)
    })


@app.route('/get-coin-transactions', methods=['GET'])
def get_coin_transactions():
    """Get user's coin transactions"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Get transactions for this user
    transactions = list(db.coin_transactions.find(
        {'user_id': user_id}
    ).sort('created_at', -1).limit(10))
    
    # Format transactions
    formatted_transactions = []
    for transaction in transactions:
        formatted_transactions.append({
            '_id': str(transaction['_id']),
            'amount': transaction['amount'],
            'transaction_type': transaction['transaction_type'],
            'description': transaction.get('description', ''),
            'created_at': transaction['created_at'].isoformat() if isinstance(transaction['created_at'], datetime) else transaction['created_at']
        })
    
    return jsonify({
        'success': True,
        'transactions': formatted_transactions
    })

# API route to get challenges
@app.route('/api/challenges')
def get_challenges():
    """Get active challenges"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Find challenges from user's university that are still active
    now = datetime.now()
    query = {
        'end_date': {'$gt': now},
        '$or': [
            {'department': user.get('department')},
            {'department': {'$exists': False}}
        ]
    }
    
    challenges_cursor = db.challenges.find(query).sort('start_date', -1)
    
    # Convert to list and format for frontend
    challenges = []
    for challenge in challenges_cursor:
        # Format challenge
        formatted_challenge = {
            '_id': str(challenge['_id']),
            'title': challenge['title'],
            'description': challenge['description'],
            'start_date': challenge['start_date'].isoformat(),
            'end_date': challenge['end_date'].isoformat(),
            'related_tags': challenge.get('related_tags', []),
            'reward_bonus': challenge.get('reward_bonus', 0),
            'department': challenge.get('department')
        }
        
        challenges.append(formatted_challenge)
    
    return jsonify({
        'success': True,
        'challenges': challenges
    })

# API route to get quests
@app.route('/api/quests')
def get_quests():
    """Get quests and user progress"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Find quests
    quests_cursor = db.quests.find()
    
    # Convert to list and format for frontend
    quests = []
    for quest in quests_cursor:
        # Format quest
        formatted_quest = {
            '_id': str(quest['_id']),
            'title': quest['title'],
            'description': quest['description'],
            'bounty_sequence': quest['bounty_sequence'],
            'total_reward': quest['total_reward'],
            'difficulty': quest.get('difficulty', 'intermediate')
        }
        
        quests.append(formatted_quest)
    
    # Get user's quest progress
    user_progress = []
    progress_cursor = db.user_progress.find({'user_id': str(user_id)})
    
    for progress in progress_cursor:
        # Format progress
        if 'quest_progress' in progress:
            formatted_progress = {
                'quest_id': progress['quest_progress']['quest_id'],
                'current_step': progress['quest_progress']['current_step'],
                'completed': progress['quest_progress']['completed']
            }
            
            user_progress.append(formatted_progress)
    
    return jsonify({
        'success': True,
        'quests': quests,
        'user_progress': user_progress
    })

# API route to get badges
@app.route('/api/badges')
def get_badges():
    """Get user badges"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    user_id = session['user_id']
    
    # Find badge types
    badge_types = list(db.badge_types.find())
    
    # Find user badges
    user_badges = list(db.user_badges.find({'user_id': str(user_id)}))
    user_badge_ids = [badge['badge_id'] for badge in user_badges]
    
    # Format badges for frontend
    badges = []
    for badge_type in badge_types:
        # Format badge
        formatted_badge = {
            '_id': str(badge_type['_id']),
            'name': badge_type['name'],
            'description': badge_type['description'],
            'icon': badge_type.get('icon', 'fa-award'), # Default icon
            'earned': str(badge_type['_id']) in user_badge_ids
        }
        
        badges.append(formatted_badge)
    
    return jsonify({
        'success': True,
        'badges': badges
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)