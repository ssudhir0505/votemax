from functools import wraps
import datetime
import json
import base64
import logging
import time
import random
import string
from hashlib import sha256

from flask import render_template, redirect, request, session, flash, url_for, jsonify
import click
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

from app import app, db
from app.models import Voter, BlockModel, Admin, RegistrationRequest
from app.blockchain import Blockchain

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize integrated blockchain
blockchain = None

def get_blockchain():
    global blockchain
    if blockchain is None:
        blockchain = Blockchain()
    return blockchain

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("System Admin access required.", "error")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def auto_logout_voter():
    """Aggressively log out voter and clear temporary data if they navigate away"""
    if request.path.startswith('/static') or not request.endpoint:
        return

    # 1. Clear TEMPORARY search data if moving away from the portal
    if request.endpoint != 'eci_portal':
        session.pop('temp_voter_slip', None)
        session.pop('temp_voter_id_result', None)

    # 2. Clear ACTIVE voter session if moving away from the terminal
    voter_safe_zone = ['index', 'submit_textarea', 'logout', 'evote_login', 'candidates', 'login_action', 'check_session_status']
    
    v_id = session.get('voter_id')
    is_admin = session.get('is_admin')
    
    if v_id and not is_admin:
        if request.endpoint not in voter_safe_zone:
            session.clear()  # Nuclear option for voter sessions
            session['is_admin'] = False # Ensure it stays False after clear

@app.after_request
def add_header(response):
    """Diamond-Hard Caching Control: Prevent any browser reuse of sensitive pages"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    response.headers["Vary"] = "*"
    return response

def _generate_tx_display_id(tx):
    """Helper to generate a stable display hash for a transaction"""
    tx_data = json.dumps({
        "voter_id": tx['voter_id'],
        "party": tx['party'],
        "timestamp": tx['timestamp']
    }, sort_keys=True)
    return sha256(tx_data.encode()).hexdigest()

def generate_unique_voter_id():
    """Generates a unique Voter ID in format CRYV#####"""
    while True:
        # Generate CRYV + 5 random digits
        suffix = ''.join(random.choices(string.digits, k=5))
        new_id = f"CRYV{suffix}"
        # Ensure Uniqueness
        if not Voter.query.get(new_id):
            return new_id

def fetch_posts():
    """Fetch all transactions from the blockchain and mempool for display"""
    bc = get_blockchain()
    content = []
    
    # Process confirmed blocks
    for block in bc.chain:
        for tx in block.transactions:
            tx_copy = tx.copy()
            tx_copy["index"] = block.index
            tx_copy["hash"] = block.hash
            tx_copy["tx_id"] = _generate_tx_display_id(tx)
            content.append(tx_copy)
            
    # Process pending mempool transactions
    for tx in bc.unconfirmed_transactions:
        tx_copy = tx.copy()
        tx_copy["index"] = "Pending"
        tx_copy["hash"] = "Unmined"
        tx_copy["tx_id"] = _generate_tx_display_id(tx)
        content.append(tx_copy)
        
    return sorted(content, key=lambda k: k['timestamp'], reverse=True)

def get_results_data():
    """Calculate current vote totals based on unique voter IDs"""
    bc = get_blockchain()
    unique_votes = {} # voter_id -> party
    
    # 1. Start with the permanent blockchain (The Source of Truth)
    for block in bc.chain:
        for tx in block.transactions:
            unique_votes[tx['voter_id']] = tx['party']
            
    # 2. Add the pending pool
    for tx in bc.unconfirmed_transactions:
        v_id = tx.get('voter_id')
        if v_id and v_id not in unique_votes:
            unique_votes[v_id] = tx['party']
            
    return list(unique_votes.values())

@app.route('/')
def landing():
    voter_registered = 'voter_id' in session
    return render_template('landing.html', title='Voter Services Portal', voter_registered=voter_registered)

@app.route('/voter')
def index():
    # Only authenticated voters can access
    if 'voter_id' not in session:
        flash("Please login with your Secure Voter ID first.", "error")
        return redirect(url_for('eci_portal')) # Redirect to search/login page

    voter_id = session.get('voter_id')
    voter = Voter.query.get(voter_id)
    
    # Fetch Vote Choice if voted
    vote_choice = None
    if voter and voter.has_voted:
        bc = get_blockchain()
        # Check mined blocks
        for block in bc.chain:
            for tx in block.transactions:
                if tx['voter_id'] == voter_id:
                    vote_choice = tx['party']
                    break
        # Check mempool if not found
        if not vote_choice:
             for tx in bc.unconfirmed_transactions:
                if tx['voter_id'] == voter_id:
                    vote_choice = tx['party']
                    break
    
    vote_gain = get_results_data()
    voter_count = Voter.query.count()
    
    return render_template('index.html',
                           title='Voter Dashboard',
                           voter_count=voter_count,
                           readable_time=datetime.datetime.fromtimestamp,
                           political_parties=['Democratic Party', 'Republican Party', 'Libertarian Party'],
                           voter_registered=True,
                           voter_id=voter_id,
                           vote_choice=vote_choice)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Form 6 Application Page"""
    if request.method == 'POST':
        full_name = request.form.get("full_name")
        dob = request.form.get("dob")
        address = request.form.get("address")
        phone = request.form.get("phone")
        email = request.form.get("email")
        
        # Check if already applied (simplified check using name+phone)
        existing = RegistrationRequest.query.filter_by(full_name=full_name, phone=phone).first()
        if existing:
            flash("Application already submitted! Please wait for Admin approval.", "warning")
            return redirect(url_for('eci_portal'))
            
        req = RegistrationRequest(full_name=full_name, dob=dob, address=address, phone=phone, email=email)
        db.session.add(req)
        db.session.commit()
        
        flash("Start Date: Application (Form 6) submitted successfully! Reference No: Pending Approval.", "success")
        return redirect(url_for('eci_portal'))
        
    return render_template('register.html', title='Voter Registration (Form 6)')

@app.route('/eci-portal')
def eci_portal():
    """Render the Search/Home Portal"""
    voter_slip = session.pop('temp_voter_slip', None)
    voter_id_result = session.pop('temp_voter_id_result', None)
    return render_template('eci_portal.html', title="Voter Services Portal", voter_slip=voter_slip, voter_id_result=voter_id_result)

@app.route('/view_slip', methods=['POST'])
def view_slip():
    """Method 1: View Slip (No Login)"""
    voter_id = request.form.get("voter_id")
    voter = Voter.query.get(voter_id)
    
    if voter:
        # Calculate Age
        if isinstance(voter.dob, str):
            dob_date = datetime.datetime.strptime(voter.dob, "%Y-%m-%d").date()
        else:
            dob_date = voter.dob
        
        age = (datetime.date.today() - dob_date).days // 365
        
        # Store dict in session (JSON serializable)
        session['temp_voter_slip'] = {
            'voter_id': voter.voter_id,
            'full_name': voter.full_name,
            'dob': str(voter.dob),
            'age': age,
            'phone': voter.phone,
            # 'email': voter.email, # Voter model has no email field
            'address': voter.address,
            'has_voted': voter.has_voted,
            'public_key': voter.public_key
        }
        flash(f"Voter Slip Retrieved for {voter.full_name}", "success")
    else:
        flash("Invalid Voter ID. Please check and try again.", "error")
        
    return redirect(url_for('eci_portal'))

@app.route('/find_voter_id', methods=['POST'])
def find_voter_id():
    """Method 2: Find ID (No Login)"""
    phone = request.form.get("phone")
    dob = request.form.get("dob")
    
    voter = Voter.query.filter_by(phone=phone, dob=dob).first()
    if voter:
        flash("Identity Verified. Voter ID Found.", "success")
        session['temp_voter_id_result'] = voter.voter_id
    else:
        # Check Pending
        req = RegistrationRequest.query.filter_by(phone=phone, dob=dob).first()
        if req:
            flash(f"Application Found: Status is '{req.status}'", "info")
        else:
            flash("No record found with these details.", "error")
        
    return redirect(url_for('eci_portal'))

@app.route('/evote_login', methods=['POST'])
def evote_login():
    """Method 3: Login for Voting (Session Start)"""
    voter_id = request.form.get("voter_id")
    voter = Voter.query.get(voter_id)
    
    if voter:
        # Start Session
        session['voter_id'] = voter_id
        session['is_admin'] = False  # CRITICAL: Prevent admin flag leakage
        
        # Security: Always regenerate Key for Demo Login to ensure sync
        if not voter.has_voted:
             session.pop('private_key', None) # Clear stale keys
             
             private_key = ec.generate_private_key(ec.SECP256R1())
             public_key = private_key.public_key()
             public_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
             private_pem = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode('utf-8')
             
             voter.public_key = public_pem
             db.session.commit()
             session['private_key'] = private_pem
        
        return redirect(url_for('index'))
    
    flash("Invalid Voter ID for Login.", "error")
    return redirect(url_for('eci_portal'))

@app.route('/candidates')
def candidates():
    return render_template('candidates.html', title="Know Your Candidate")

@app.route('/login_action', methods=['POST'])
def login_action():
    """Handle login from Search Page"""
    voter_id = request.form.get("voter_id")
    voter = Voter.query.get(voter_id)
    if voter:
        session['voter_id'] = voter_id
        session['is_admin'] = False  # CRITICAL: Prevent admin flag leakage
        # DEMO HACK: Simulate loading private key. 
        # Since we don't have it, we'll re-generate one and update public key if they haven't voted yet.
        # If they HAVE voted, they can't vote again anyway, so it doesn't matter.
        if not voter.has_voted:
             private_key = ec.generate_private_key(ec.SECP256R1())
             public_key = private_key.public_key()
             public_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
             private_pem = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode('utf-8')
             
             voter.public_key = public_pem
             db.session.commit()
             session['private_key'] = private_pem
        else:
            # If voted, they don't need private key anymore (only for verifying, not signing new)
            pass
            
        return redirect(url_for('index'))
    return redirect(url_for('eci_portal'))


@app.route('/submit', methods=['POST'])
def submit_textarea():
    voter_id = session.get('voter_id')
    private_key_pem = session.get('private_key')

    if not voter_id:
        flash("You must be logged in to vote.", "error")
        return redirect(url_for('eci_portal'))
    
    voter = Voter.query.get(voter_id)
    if not voter:
        flash("Voter record not found.", "error")
        session.clear()
        return redirect(url_for('eci_portal'))

    if voter.has_voted:
        flash("Duplicate vote prevention: You have already voted.", "error")
        return redirect(url_for('index'))
    
    if not private_key_pem:
        # Auto-regenerate if needed for demo flow continuity
        if not voter.has_voted:
             private_key = ec.generate_private_key(ec.SECP256R1())
             public_key = private_key.public_key()
             public_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
             private_pem = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode('utf-8')
             voter.public_key = public_pem
             db.session.commit()
             session['private_key'] = private_pem
             private_key_pem = private_pem
        else:
            flash("Security Error: Digital Signature Key missing. Please re-login.", "error")
            return redirect(url_for('eci_portal'))

    party = request.form.get("party")
    timestamp = time.time()
    
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None
        )
        message = json.dumps({"voter_id": voter_id, "party": party, "timestamp": timestamp}, sort_keys=True).encode()
        signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))
        
        transaction = {
            'voter_id': voter_id,
            'party': party,
            'timestamp': timestamp,
            'signature': base64.b64encode(signature).decode('utf-8'),
            'public_key': base64.b64encode(voter.public_key.encode('utf-8')).decode('utf-8')
        }
        
        bc = get_blockchain()
        
        # SECURITY FIX: Mark as voted + COMMIT BEFORE the time-consuming mining process
        # This prevents "Double-Click" or "Back-Button" race conditions
        voter.has_voted = True
        db.session.commit()
        
        if bc.add_new_transaction(transaction):
            flash(f"Vote cast for {party} successfully!", "success")
        else:
            # Rollback if signature failed (rare since we check keys, but safe)
            voter.has_voted = False
            db.session.commit()
            flash("Signature verification failed.", "error")

    except Exception as e:
        logger.error(f"Error: {e}")
        flash("An error occurred during vote submission.", "error")
        
    return redirect(url_for('index'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session.permanent = True
            session['is_admin'] = True
            session['voter_id'] = f'ADMIN:{username}'
            flash(f"System Administrator '{username}' Access Granted.", "success")
            return redirect(url_for('admin'))
        flash("Invalid credentials.", "error")
    return render_template('admin_login.html', title='Admin Login')

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin():
    # Handle Manual Registration
    if request.method == 'POST':
        full_name = request.form.get("full_name")
        dob = request.form.get("dob")
        address = request.form.get("address")
        phone = request.form.get("phone")
        
        # Determine existing or new
        # For simplicity, we create a new voter directly
        vid = generate_unique_voter_id()
        
        # Generate Keys
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
        
        new_voter = Voter(
            voter_id=vid, 
            public_key=public_pem,
            full_name=full_name,
            dob=dob,
            address=address,
            phone=phone
        )
        db.session.add(new_voter)
        db.session.commit()
        flash(f"Offline Voter Registered! Generated ID: {vid}", "success")
        return redirect(url_for('admin'))

    voters = Voter.query.all()
    pending_requests = RegistrationRequest.query.filter_by(status='Pending').all()
    bc = get_blockchain()
    posts = fetch_posts()
    vote_gain = get_results_data()
    
    return render_template('admin.html',
                           title='Official Admin Portal',
                           voters=voters,
                           pending_requests=pending_requests,
                           chain=bc.chain,
                           unconfirmed=bc.unconfirmed_transactions,
                           posts=posts, 
                           vote_gain=vote_gain,
                           readable_time=datetime.datetime.fromtimestamp,
                           political_parties=['Democratic Party', 'Republican Party', 'Libertarian Party'],
                           voter_id=session.get('voter_id'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    session.pop('voter_id', None)
    flash("Admin logged out successfully.", "success")
    return redirect(url_for('admin_login'))

@app.route('/admin/approve/<int:req_id>')
@admin_required
def approve_voter(req_id):
    req = RegistrationRequest.query.get(req_id)
    if not req:
        flash("Request not found", "error")
        return redirect(url_for('admin'))
    
    vid = generate_unique_voter_id()
    
    # Generate Keys
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
    
    new_voter = Voter(
        voter_id=vid,
        public_key=public_pem,
        full_name=req.full_name,
        dob=req.dob,
        address=req.address,
        phone=req.phone
    )
    
    req.status = 'Approved'
    db.session.add(new_voter)
    db.session.commit()
    
    flash(f"Application Approved! New Voter ID: {vid}", "success")
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:req_id>')
@admin_required
def reject_voter(req_id):
    req = RegistrationRequest.query.get(req_id)
    if req:
        req.status = 'Rejected'
        db.session.commit()
        flash("Application Rejected.", "error")
    return redirect(url_for('admin'))

@app.route('/admin/console')
@admin_required
def admin_console():
    return render_template('console.html', 
                           title='Developer Console', 
                           voter_id=session.get('voter_id'))

@app.route('/api/system_state')
@admin_required
def get_system_state():
    bc = get_blockchain()
    voters = Voter.query.all()
    
    voter_data = [
        {
            "voter_id": v.voter_id,
            "digital_seal_public": v.public_key,
            "has_voted": v.has_voted,
            "registered_at": v.registered_at.strftime('%Y-%m-%d %H:%M:%S')
        } for v in voters
    ]

    chain_data = [block.__dict__ for block in bc.chain]
    
    return jsonify({
        "node_id": "ECI_NODE_01",
        "status": "synchronized",
        "blockchain": {
            "length": len(chain_data),
            "ledger": chain_data
        },
        "voter_registry": {
            "total_registered": len(voter_data),
            "registry": voter_data
        },
        "pending_pool": {
            "count": len(bc.unconfirmed_transactions),
            "transactions": bc.unconfirmed_transactions
        }
    })

@app.route('/api/mine', methods=['POST'])
@admin_required
def trigger_mine():
    bc = get_blockchain()
    if bc.mine(force=True):
        return jsonify({"success": True, "message": "Manual mining successful."})
    return jsonify({"success": False, "message": "Mining failed. Pool empty."}), 400

@app.route('/logout')
def logout():
    session.clear()
    flash("Session terminated successfully.", "success")
    return redirect(url_for('landing'))

# CLI Commands
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
def create_admin(username, password):
    existing = Admin.query.filter_by(username=username).first()
    if existing:
        click.echo(f"[ERROR] Superuser '{username}' already exists!")
        return
    admin = Admin(username=username)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"[SUCCESS] Superuser '{username}' created successfully!")

@app.cli.command("reset-db")
def reset_db():
    db.drop_all()
    db.create_all()
    click.echo("Database has been reset. All data wiped.")

@app.cli.command("sync-ledger")
def sync_ledger():
    bc = Blockchain()
    voters = Voter.query.all()
    active_ids = {tx['voter_id'] for block in bc.chain for tx in block.transactions}
    active_ids.update({tx['voter_id'] for tx in bc.unconfirmed_transactions})
    
    fixed_count = 0
    for voter in voters:
        correct_status = voter.voter_id in active_ids
        if voter.has_voted != correct_status:
            voter.has_voted = correct_status
            fixed_count += 1
    db.session.commit()
    click.echo(f"Sync complete. Reconciled {fixed_count} voter states.")

@app.route('/api/session-status')
def check_session_status():
    """Client-Side Heartbeat to detect Ghost Sessions (cached pages)"""
    return jsonify({
        "voter_id": session.get('voter_id'),
        "is_admin": session.get('is_admin', False),
        "has_session": 'voter_id' in session or 'is_admin' in session
    })
