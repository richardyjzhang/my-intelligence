from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = 'my-intelligence'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .tag import tag as tag_blueprint
    app.register_blueprint(tag_blueprint)

    from .doc import doc as doc_blueprint
    app.register_blueprint(doc_blueprint)

    # from .user import user as user_blueprint
    # app.register_blueprint(user_blueprint)

    return app
