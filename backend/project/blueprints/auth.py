from flask import Blueprint, request, Response
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from werkzeug.exceptions import BadRequest

from ..models import User

auth = Blueprint('auth', __name__)


# 登录接口
@auth.route('/login', methods=['POST'])
def login():

    request_body = request.get_json()

    try:
        username = request_body["username"]
        password = request_body["password"]
    except KeyError:
        raise BadRequest

    # 用户名不存在或密码错误，均认为登录错误
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return {"success": False, "message": "用户名或密码错误"}, 200

    login_user(user)
    return {"success": True}, 200


# 登出接口
@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return Response(status=200)
