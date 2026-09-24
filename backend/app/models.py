from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Voter(db.Model):
    voter_id = db.Column(db.String(50), primary_key=True)  # Format: CRYV#####
    public_key = db.Column(db.Text, nullable=False)
    has_voted = db.Column(db.Boolean, default=False)
    
    # Personal Details (Transferred from Registration Request upon approval)
    full_name = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

class RegistrationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100)) # Optional
    
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BlockModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, nullable=False)
    transactions = db.Column(db.Text, nullable=False) # JSON list
    timestamp = db.Column(db.Float, nullable=False)
    previous_hash = db.Column(db.String(64), nullable=False)
    nonce = db.Column(db.Integer, nullable=False)
    hash = db.Column(db.String(64), nullable=False)

class MempoolModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(50), nullable=False)
    party = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    signature = db.Column(db.Text, nullable=False)
    public_key = db.Column(db.Text, nullable=False)
