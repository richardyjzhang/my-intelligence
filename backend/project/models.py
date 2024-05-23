from dataclasses import dataclass
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column

from . import db


# 封装SQLAlchemy的Model
class Base:

    def to_dict(self):
        model_dict = dict(self.__dict__)
        del model_dict['_sa_instance_state']
        return model_dict


# 用户类，用于登录
class User(UserMixin, db.Model, Base):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))


# 标签类，每个文档可以打一个或若干个标签
@dataclass
class Tag(db.Model, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    color: Mapped[str] = mapped_column()


# 文档类
@dataclass
class Doc(db.Model, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    path: Mapped[str] = mapped_column()
    ct: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    status: Mapped[int] = mapped_column()


# 文档和标签关联
@dataclass
class DocTagMap(db.Model, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_id: Mapped[int] = mapped_column()
    tag_id: Mapped[int] = mapped_column()
