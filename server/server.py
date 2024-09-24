import os
import logging
from flask import Flask
from flask_login import LoginManager
from models import db, User
from config import Config
from routes import routes

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'routes.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()

app.register_blueprint(routes)

if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('logs/server.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
