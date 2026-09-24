import os
from flask import Flask
from flask_session import Session
from config import Config
from .models import db

# Calculate absolute path to the frontend/templates folder
# __file__ is at backend/app/__init__.py
base_dir = os.path.abspath(os.path.dirname(__file__))
# Going up two levels to reach the root, then into frontend/templates
template_dir = os.path.abspath(os.path.join(base_dir, '..', '..', 'frontend', 'templates'))

# Static folder is at frontend/static
static_dir = os.path.abspath(os.path.join(base_dir, '..', '..', 'frontend', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config.from_object(Config)

Session(app)
db.init_app(app)

from app import views