from flask import Flask
from routes.routes import setup_routes

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-change-this-in-production'

# Setup all routes
setup_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)