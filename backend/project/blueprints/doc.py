import datetime

from flask import Blueprint, request, jsonify, Response
from flask_login import login_required
from sqlalchemy import text
from werkzeug.exceptions import BadRequest

from .. import db
from ..models import Doc, DocTagMap
from ..store import store_file, del_file
from ..utils.snowflake import new_id

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

    new_doc = Doc(id=new_id(), name=name, path=path, ct=ct,
                  description=description, status=status)

    db.session.add(new_doc)
    db.session.commit()

    return jsonify(new_doc), 201


# 获取所有文档
@doc.route('/docs', methods=['GET'])
@login_required
def list_docs():

    # 获取数据库中的所有文档和标签映射
    docs = Doc.query.all()
    maps = DocTagMap.query.all()

    # 将标签映射的ID补充道对应的文档中
    id2doc = {}
    for d in docs:
        id2doc[d.id] = d.to_dict()
        id2doc[d.id]['tags'] = []
    for m in maps:
        if m.doc_id in id2doc:
            id2doc[m.doc_id]['tags'].append(m.tag_id)

    return list(id2doc.values()), 200


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
        del_file(exists.path)
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


# 修改某个文档的标签，全量修改
@doc.route('/docs/tags/<id>', methods=['POST'])
@login_required
def set_doc_tags(id):

    tag_ids = request.get_json()
    if not isinstance(tag_ids, list):
        raise BadRequest
    db.get_or_404(Doc, id)

    # 删除已有标签，并重新添加标签
    new_maps = [DocTagMap(id=new_id(), doc_id=id, tag_id=t) for t in tag_ids]
    db.session.execute(text(f'DELETE FROM doc_tag_map WHERE doc_id = {id}'))
    db.session.add_all(new_maps)
    db.session.commit()

    return Response(status=200)
