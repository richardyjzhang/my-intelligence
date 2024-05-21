import datetime

from flask import Blueprint, request, jsonify, Response
from flask_login import login_required
from sqlalchemy import text
from werkzeug.exceptions import BadRequest

from . import db
from .models import Doc
from .store import store_file

doc = Blueprint('doc', __name__)


# 创建文档
@doc.route('/docs', methods=['POST'])
@login_required
def create_doc():

    try:
        name = request.form.get('name')
    except ValueError:
        raise BadRequest

    try:
        file = request.files['file']
    except:
        raise BadRequest

    description = request.form.get('description', default='')
    ct = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = 0

    path = store_file(file)

    new_doc = Doc(name=name, path=path, ct=ct,
                  description=description, status=status)

    db.session.add(new_doc)
    db.session.commit()

    return jsonify(new_doc), 201


# 获取所有文档
@doc.route('/docs', methods=['GET'])
@login_required
def list_docs():
    docs = Doc.query.all()
    return docs, 200


# 删除某个文档
@doc.route('/docs/<id>', methods=['DELETE'])
@login_required
def delete_doc(id):
    exists = Doc.query.filter_by(id=id).first()
    if exists != None:
        db.session.delete(exists)
        db.session.execute(
            text(f'DELETE FROM doc_tag_map WHERE doc_id = {id}'))
        db.session.commit()
    return Response(status=204)


# 修改某个文档，仅能修改基本信息
@doc.route('/docs/<id>', methods=['PUT'])
@login_required
def modify_doc(id):
    request_body = request.get_json()

    try:
        name = request_body['name']
        description = request_body['description']
    except KeyError:
        raise BadRequest

    # 对已有标签进行修改
    exists = db.get_or_404(Doc, id)
    exists.name = name
    exists.description = description

    exists.verified = True
    db.session.commit()

    return jsonify(exists), 200
