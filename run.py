import sys
import os

# Add backend to Python path so we can import the app package
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, backend_path)

from app import app, db
from app.models import Voter, Admin, BlockModel, MempoolModel

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'Voter': Voter, 
        'Admin': Admin, 
        'BlockModel': BlockModel, 
        'MempoolModel': MempoolModel
    }

if __name__ == '__main__':
    # This ensures the app runs on port 5000 and is accessible
    app.run(debug=True, port=8090)
