import os
from flask import Flask
from models import db, UserAccount
from routes.routes import setup_routes
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-change-this-in-production'

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'placement.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads', 'resumes')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Database
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return UserAccount.query.get(int(user_id))

# Setup all routes
setup_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)