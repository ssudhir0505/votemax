import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '6dbf23122cb5046cc5c0c1b245c75f8e43c59ca8ffeac292715e5078e631d0c9'
    
    # Calculate path to backend/instance/voting_system.db
    # BASE_DIR = backend/
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'instance', 'voting_system.db')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    import tempfile
    SESSION_FILE_DIR = os.path.join(tempfile.gettempdir(), 'flask_session_vote_app')
