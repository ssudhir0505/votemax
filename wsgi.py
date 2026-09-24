import sys
import os

# Add backend to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, backend_path)

# Import the Flask app - this will automatically register all CLI commands
from app import app, db
from app.models import Voter, Admin, BlockModel, MempoolModel

# Make shell context available
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Voter': Voter,
        'Admin': Admin,
        'BlockModel': BlockModel,
        'MempoolModel': MempoolModel
    }

# This is what Flask CLI will use
if __name__ == "__main__":
    app.run()
