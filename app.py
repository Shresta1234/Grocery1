from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
import base64
from threading import Timer
import schedule
import time

app = Flask(__name__)
# Set a long session lifetime (30 days)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.secret_key = os.urandom(24)  # Strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grocery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------------- Database Models -------------------------- #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    dark_mode = db.Column(db.Boolean, default=False)
    notification_days = db.Column(db.Integer, default=3)
    notification_method = db.Column(db.String(20), default='email')
    remember_me = db.Column(db.Boolean, default=True)
    notification_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, custom
    custom_notification_times = db.Column(db.String(200), default='')  # JSON string of times
    ai_notifications = db.Column(db.Boolean, default=True)
    browser_notifications = db.Column(db.Boolean, default=True)
    items = db.relationship('GroceryItem', backref='user', lazy=True)

class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='Other')
    quantity = db.Column(db.String(50), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    added_date = db.Column(db.Date, default=datetime.utcnow().date())
    status = db.Column(db.String(20), default='active')  # 'active' or 'completed'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'quantity': self.quantity,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d'),
            'added_date': self.added_date.strftime('%Y-%m-%d'),
            'status': self.status,
            'user_id': self.user_id,
            'safety_status': self.safety_status if hasattr(self, 'safety_status') else None,
            'days_until_expiry': self.days_until_expiry if hasattr(self, 'days_until_expiry') else None
        }

# -------------------------- Helper Functions -------------------------- #
def get_expiring_items(user_id):
    today = datetime.utcnow().date()
    expiry_threshold = today + timedelta(days=7)  # Items expiring within 7 days
    return GroceryItem.query.filter(
        GroceryItem.user_id == user_id,
        GroceryItem.status == 'active',
        GroceryItem.expiry_date <= expiry_threshold,
        GroceryItem.expiry_date >= today
    ).order_by(GroceryItem.expiry_date).all()

def get_item_status(expiry_date, notification_days):
    today = datetime.utcnow().date()
    days_until_expiry = (expiry_date - today).days
    
    if days_until_expiry < 0:
        return 'expired'  # Red
    elif days_until_expiry <= notification_days:
        return 'expiring_soon'  # Yellow
    else:
        return 'safe'  # Green

def get_category_stats(items):
    categories = {}
    for item in items:
        categories[item.category] = categories.get(item.category, 0) + 1
    return {
        'labels': list(categories.keys()),
        'data': list(categories.values())
    }

def get_expiry_stats(items, notification_days):
    stats = {
        'safe': 0,
        'expiring_soon': 0,
        'expired': 0
    }
    
    today = datetime.utcnow().date()
    for item in items:
        days_until_expiry = (item.expiry_date - today).days
        if days_until_expiry < 0:
            stats['expired'] += 1
        elif days_until_expiry <= notification_days:
            stats['expiring_soon'] += 1
        else:
            stats['safe'] += 1
    
    return {
        'labels': ['Safe', 'Expiring Soon', 'Expired'],
        'data': [stats['safe'], stats['expiring_soon'], stats['expired']],
        'colors': ['#28a745', '#ffc107', '#dc3545']  # Green, Yellow, Red
    }

def get_days_until_expiry(expiry_date):
    today = datetime.utcnow().date()
    return (expiry_date - today).days

def get_expiry_message(days_until_expiry):
    if days_until_expiry < 0:
        return f"Expired {-days_until_expiry} days ago"
    elif days_until_expiry == 0:
        return "Expires today"
    else:
        return f"Expires in {days_until_expiry} days"

def generate_grocery_image(items, user):
    # Create a new image with white background
    width = 800
    height = 100 + (len(items) * 30)
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Add title
    title = f"{user.username}'s Grocery List"
    draw.text((20, 20), title, fill='black')
    
    # Add items
    y = 60
    for item in items:
        expiry_text = item.expiry_date.strftime('%Y-%m-%d')
        text = f"{item.name} - {item.quantity} - Expires: {expiry_text}"
        
        # Color code based on expiry status
        if item.safety_status == 'expired':
            fill = 'red'
        elif item.safety_status == 'expiring_soon':
            fill = 'orange'
        else:
            fill = 'green'
            
        draw.text((20, y), text, fill=fill)
        y += 30
    
    # Convert image to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return image_base64

# -------------------------- Routes -------------------------- #
@app.route('/')
def home():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('landing.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get all active items
    items = GroceryItem.query.filter_by(
        user_id=user.id,
        status='active'
    ).order_by(GroceryItem.expiry_date).all()
    
    # Calculate statistics
    today = datetime.utcnow().date()
    expired_items = []
    expiring_soon_items = []
    safe_items = []
    
    # Convert items to dictionaries for JSON serialization
    serialized_items = []
    for item in items:
        days_until_expiry = (item.expiry_date - today).days
        item_dict = {
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'quantity': item.quantity,
            'expiry_date': item.expiry_date.strftime('%Y-%m-%d'),
            'added_date': item.added_date.strftime('%Y-%m-%d'),
            'status': item.status,
            'user_id': item.user_id,
            'safety_status': 'safe',
            'days_until_expiry': days_until_expiry
        }
        
        if days_until_expiry < 0:
            item_dict['safety_status'] = 'expired'
            expired_items.append(item)
        elif days_until_expiry <= user.notification_days:
            item_dict['safety_status'] = 'expiring_soon'
            expiring_soon_items.append(item)
        else:
            item_dict['safety_status'] = 'safe'
            safe_items.append(item)
            
        serialized_items.append(item_dict)
    
    # Prepare data for charts
    expiry_stats = {
        'labels': ['Safe', 'Expiring Soon', 'Expired'],
        'data': [len(safe_items), len(expiring_soon_items), len(expired_items)],
        'colors': ['#28a745', '#ffc107', '#dc3545']
    }
    
    # Get category statistics
    categories = {}
    for item in items:
        categories[item.category] = categories.get(item.category, 0) + 1
    
    category_stats = {
        'labels': list(categories.keys()) if categories else ['No Items'],
        'data': list(categories.values()) if categories else [0],
        'colors': [
            '#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f',
            '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'
        ][:len(categories) or 1]
    }
    
    return render_template('index.html',
                         user=user,
                         items=items,
                         serialized_items=serialized_items,
                         expired_items=expired_items,
                         expiring_soon_items=expiring_soon_items,
                         safe_items=safe_items,
                         expiry_stats=expiry_stats,
                         category_stats=category_stats)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/add_item', methods=['POST'])
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        name = request.form['name']
        category = request.form['category']
        quantity = request.form['quantity']
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        
        item = GroceryItem(
            name=name,
            category=category,
            quantity=quantity,
            expiry_date=expiry_date,
            status='active',
            user_id=session['user_id']
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully!')
    except Exception as e:
        flash('Error adding item')
    return redirect(url_for('dashboard'))

@app.route('/update_item/<int:item_id>', methods=['POST'])
def update_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    item = GroceryItem.query.get_or_404(item_id)
    if item.user_id != session['user_id']:
        flash('Unauthorized action', 'error')
        return redirect(url_for('dashboard'))
    item.name = request.form['name']
    item.category = request.form['category']
    item.quantity = request.form['quantity']
    item.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
    db.session.commit()
    flash('Item updated successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    item = GroceryItem.query.get_or_404(item_id)
    if item.user_id != session['user_id']:
        flash('Unauthorized')
        return redirect(url_for('dashboard'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/mark_used/<int:item_id>')
def mark_used(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    item = GroceryItem.query.get_or_404(item_id)
    if item.user_id != session['user_id']:
        flash('Unauthorized action', 'error')
        return redirect(url_for('dashboard'))
    item.status = 'used'
    db.session.commit()
    flash('Item marked as used!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update notification settings
        user.notification_days = int(request.form.get('notification_days', 3))
        
        # Update email
        new_email = request.form.get('email')
        if new_email and new_email != user.email:
            user.email = new_email
        
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if check_password_hash(user.password, current_password):
                if new_password == confirm_password:
                    user.password = generate_password_hash(new_password)
                    flash('Password updated successfully!', 'success')
                else:
                    flash('New passwords do not match!', 'error')
            else:
                flash('Current password is incorrect!', 'error')
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', user=user)

@app.route('/shopping_list')
def shopping_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    items = GroceryItem.query.filter_by(user_id=session['user_id']).all()
    return render_template('shopping_list.html', items=items)

@app.route('/api/expiring_soon')
def api_expiring_soon():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    items = get_expiring_items(session['user_id'])
    result = [{
        'name': item.name,
        'expiry_date': item.expiry_date.strftime('%Y-%m-%d'),
        'days_left': (item.expiry_date - datetime.now().date()).days
    } for item in items]
    return jsonify(result)

@app.route('/complete_item/<int:item_id>')
def complete_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    item = GroceryItem.query.get_or_404(item_id)
    if item.user_id != session['user_id']:
        flash('Unauthorized')
        return redirect(url_for('dashboard'))
    
    item.status = 'completed'
    db.session.commit()
    flash('Item marked as completed!')
    return redirect(url_for('dashboard'))

@app.route('/share_list/<int:user_id>')
def share_list(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if session['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    items = GroceryItem.query.filter_by(
        user_id=user_id,
        status='active'
    ).order_by(GroceryItem.expiry_date).all()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Generate share URL
    share_url = request.url_root + f'share/{user_id}'
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(share_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR code to base64
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
    
    # Generate grocery list image
    image_base64 = generate_grocery_image(items, user)
    
    return jsonify({
        'success': True,
        'image': image_base64,
        'qr_code': qr_base64,
        'share_url': share_url
    })

@app.route('/share/<int:user_id>')
def view_shared_list(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    
    items = GroceryItem.query.filter_by(
        user_id=user_id,
        status='active'
    ).order_by(GroceryItem.expiry_date).all()
    
    # Calculate item statuses
    today = datetime.utcnow().date()
    for item in items:
        days_until_expiry = (item.expiry_date - today).days
        if days_until_expiry < 0:
            item.safety_status = 'expired'
        elif days_until_expiry <= 3:  # Default notification days
            item.safety_status = 'expiring_soon'
        else:
            item.safety_status = 'safe'
        item.days_until_expiry = days_until_expiry
    
    return render_template('shared_list.html', 
                         user=user,
                         items=items)

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'success': False}), 404
    
    today = datetime.utcnow().date()
    expiring_items = GroceryItem.query.filter(
        GroceryItem.user_id == user.id,
        GroceryItem.status == 'active',
        GroceryItem.expiry_date <= today + timedelta(days=user.notification_days),
        GroceryItem.expiry_date >= today
    ).all()
    
    notifications = []
    if expiring_items:
        notifications.append({
            'type': 'warning',
            'message': f'You have {len(expiring_items)} items expiring soon!',
            'items': [{'name': item.name, 'expiry_date': item.expiry_date.strftime('%Y-%m-%d')}
                     for item in expiring_items]
        })
    
    return jsonify({
        'success': True,
        'notifications': notifications
    })

@app.route('/update_dark_mode', methods=['POST'])
def update_dark_mode():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    dark_mode = data.get('dark_mode', False)
    
    user = User.query.get(session['user_id'])
    if user:
        user.dark_mode = dark_mode
        db.session.commit()
        session['dark_mode'] = dark_mode
        return jsonify({'success': True})
    
    return jsonify({'error': 'User not found'}), 404

# Add this to handle session expiry
@app.before_request
def check_session():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and not user.remember_me:
            session.clear()
            return redirect(url_for('login'))

# Add notification checking function
def check_notifications():
    with app.app_context():
        now = datetime.utcnow()
        users = User.query.all()
        
        for user in users:
            if not user.notification_days:
                continue
                
            expiry_threshold = now.date() + timedelta(days=user.notification_days)
            expiring_items = GroceryItem.query.filter(
                GroceryItem.user_id == user.id,
                GroceryItem.status == 'active',
                GroceryItem.expiry_date <= expiry_threshold,
                GroceryItem.expiry_date >= now.date()
            ).all()
            
            if expiring_items:
                # Handle browser notifications
                if user.notification_method == 'browser':
                    notification = {
                        'type': 'expiring_items',
                        'message': f'You have {len(expiring_items)} items expiring soon!',
                        'items': [{
                            'name': item.name,
                            'expiry_date': item.expiry_date.strftime('%Y-%m-%d')
                        } for item in expiring_items]
                    }
                    # Store notification in session or database
                    
                # Handle email notifications
                elif user.notification_method == 'email':
                    send_expiry_notification_email(user, expiring_items)

# Schedule notification checks
def start_notification_scheduler():
    schedule.every(1).minutes.do(check_notifications)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start the scheduler in a separate thread
import threading
notification_thread = threading.Thread(target=start_notification_scheduler)
notification_thread.daemon = True
notification_thread.start()

# Add template global functions
@app.template_global()
def get_expiry_message(days_until_expiry):
    if days_until_expiry < 0:
        return f"Expired {-days_until_expiry} days ago"
    elif days_until_expiry == 0:
        return "Expires today"
    else:
        return f"Expires in {days_until_expiry} days"

# -------------------------- Create Database -------------------------- #
if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
