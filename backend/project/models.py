from dataclasses import dataclass
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column

from . import db


# 用户类，用于登录
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))


# 标签类，每个文档可以打一个或若干个标签
@dataclass
class Tag(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int] = mapped_column()
