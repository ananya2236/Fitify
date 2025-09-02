# app.py
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from recommendations import generate_recommendation

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
# Database: prefer DATABASE_URL env var (works for Postgres in prod), else sqlite local
db_url = os.getenv('DATABASE_URL', 'sqlite:///fitify.db')
# SQLAlchemy expects postgresql:// rather than postgres:// for some providers
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
mail = Mail(app)

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class MessageModel(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    bmi = db.Column(db.Float)
    category = db.Column(db.String(50))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    goal = db.Column(db.String(50))
    allergies = db.Column(db.Text)  # JSON string
    diet_plan = db.Column(db.Text)  # JSON string
    workout_plan = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for('register'))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid credentials", "danger")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    recs = Recommendation.query.filter_by(user_id=current_user.id).order_by(Recommendation.created_at.desc()).all()
    # parse JSON fields
    for r in recs:
        try:
            r.diet_plan = json.loads(r.diet_plan)
            r.workout_plan = json.loads(r.workout_plan)
            r.allergies = json.loads(r.allergies) if r.allergies else []
        except Exception:
            r.diet_plan = r.diet_plan or []
            r.workout_plan = r.workout_plan or []
            r.allergies = r.allergies or []
    return render_template('dashboard.html', recs=recs)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json() or {}
    result = generate_recommendation(data)
    # Save to DB if logged in
    try:
        rec = Recommendation(
            user_id = current_user.id if hasattr(current_user, "is_authenticated") and current_user.is_authenticated else None,
            bmi = result.get('bmi'),
            category = result.get('category'),
            height = data.get('height'),
            weight = data.get('weight'),
            age = data.get('age'),
            gender = data.get('gender'),
            goal = data.get('goal'),
            allergies = json.dumps(data.get('allergies') or []),
            diet_plan = json.dumps(result.get('diet_plan') or []),
            workout_plan = json.dumps(result.get('workout_plan') or [])
        )
        db.session.add(rec)
        db.session.commit()
    except Exception as ex:
        # don't fail the API if DB save fails; log in real app
        print("Failed to save recommendation:", ex)
    return jsonify(result)

@app.route('/send_message', methods=['POST'])
def send_message():
    # accept both JSON and form
    if request.is_json:
        payload = request.get_json()
        name = payload.get('name')
        email = payload.get('email')
        message_text = payload.get('message')
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        message_text = request.form.get('message')

    # Save to DB
    msg = MessageModel(name=name, email=email, message=message_text)
    db.session.add(msg)
    db.session.commit()

    # Send email if mail configured
    try:
        if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
            message = Message(subject=f"Contact from {name or 'anonymous'}",
                              sender=app.config.get('MAIL_DEFAULT_SENDER'),
                              recipients=[app.config.get('MAIL_USERNAME')])
            message.body = f"From: {name} <{email}>\n\n{message_text}"
            mail.send(message)
    except Exception as ex:
        print("Mail send failed:", ex)

    return jsonify({'status':'ok', 'message':'Thanks! We received your message.'})

if __name__ == '__main__':
    app.run(debug=True)
