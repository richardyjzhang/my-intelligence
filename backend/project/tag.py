from flask import Blueprint, request, jsonify, Response
from flask_login import login_required
from sqlalchemy import text
from werkzeug.exceptions import BadRequest

from . import db
from .models import Tag

tag = Blueprint('tag', __name__)


# 创建标签
@tag.route('/tags', methods=['POST'])
@login_required
def create_tag():

    request_body = request.get_json()

    try:
        name = request_body["name"]
        color = request_body["color"]
    except KeyError:
        raise BadRequest

    # 禁止添加同名标签
    exists = Tag.query.filter_by(name=name).first()
    if exists != None:
        raise BadRequest

    new_tag = Tag(name=name, color=color)
    db.session.add(new_tag)
    db.session.commit()

    return jsonify(new_tag), 201


# 获取所有标签
@tag.route('/tags', methods=['GET'])
@login_required
def list_tags():
    tags = Tag.query.all()
    return tags, 200


# 删除某个标签
@tag.route('/tags/<id>', methods=['DELETE'])
@login_required
def delete_tag(id):
    exists = Tag.query.filter_by(id=id).first()
    if exists != None:
        db.session.delete(exists)
        db.session.execute(
            text(f'DELETE FROM doc_tag_map WHERE tag_id = {id}'))
        db.session.commit()
    return Response(status=204)


# 修改某个标签
@tag.route('/tags/<id>', methods=['PUT'])
@login_required
def modify_tag(id):
    request_body = request.get_json()

    try:
        name = request_body["name"]
        color = request_body["color"]
    except KeyError:
        raise BadRequest

    # 禁止添加同名标签
    exists = Tag.query.filter_by(name=name).first()
    if exists != None and exists.color == color:
        raise BadRequest

    # 对已有标签进行修改
    exists = db.get_or_404(Tag, id)
    exists.name = name
    exists.color = color

    exists.verified = True
    db.session.commit()

    return jsonify(exists), 200
