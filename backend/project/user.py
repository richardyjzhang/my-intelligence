from flask import Blueprint, request
from flask_login import login_required
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import BadRequest

from . import db
from .models import User

user = Blueprint('user', __name__)


# 创建用户
@user.route('/users', methods=['POST'])
@login_required
def create_user():

    request_body = request.get_json()

    try:
        username = request_body["username"]
        password = request_body["password"]
    except KeyError:
        raise BadRequest

    # 禁止添加同名用户
    exists = User.query.filter_by(username=username).first()
    if exists != None:
        raise BadRequest

    new_user = User(username=username,
                    password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()

    return {"success": True}, 201
