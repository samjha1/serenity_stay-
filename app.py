from flask import Flask
from flask_login import LoginManager
from models import db, User

app = Flask(__name__)
app.config["SECRET_KEY"] = "serenity-secret-2024-xyz"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    if not user_id or not str(user_id).isdigit():
        return None
    return User.query.get(int(user_id))

from routes.auth import auth_bp
from routes.main import main_bp
from routes.staff import staff_bp

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(staff_bp, url_prefix="/staff")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
