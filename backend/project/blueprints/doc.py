import os
import datetime

from flask import Blueprint, request, jsonify, Response, send_file
from flask_login import login_required
from sqlalchemy import text, or_
from werkzeug.exceptions import BadRequest

from .. import db, config
from ..models import Doc, DocTagMap
from ..store import store_file, del_file
from ..utils.snowflake import new_id
from ..services.dispatcher import handle_one_doc
from ..services.eshelper import search_documents

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

    # 对文档进行识别处理
    handle_one_doc(new_doc.id, new_doc.path)

    return jsonify(new_doc), 201


# 获取所有文档
@doc.route('/docs', methods=['GET'])
@login_required
def list_docs():

    # 获取数据库中的所有文档和标签映射
    docs = Doc.query.all()
    maps = DocTagMap.query.all()

    # 将标签映射的ID补充到对应的文档中
    id2doc = {}
    for d in docs:
        id2doc[d.id] = d.to_dict()
        id2doc[d.id]['tags'] = []
    for m in maps:
        if m.doc_id in id2doc:
            id2doc[m.doc_id]['tags'].append(m.tag_id)

    return list(id2doc.values()), 200


# 文档智能搜索，在文件标题、描述和全文内容中搜索
@doc.route('/docs/allin-search', methods=['POST'])
@login_required
def allin_search_docs():
    try:
        request_body = request.get_json()
        keyword = request_body.get('keyword', '')
        tagIds = request_body.get('tagIds', None)
    except KeyError:
        raise BadRequest

    # 最终结果
    id2doc = {}

    # 首先按照文档标题和描述搜索
    tagClause = ''
    if tagIds != None and len(tagIds) > 0:
        tagIds = ','.join(tagIds)
        tagClause = f' AND tagId IN ({tagIds}) '
    results = db.session.execute(
        text(' SELECT d.id, d.name, d.path, d.ct, d.description, d.status, m.tag_id '
             f" FROM doc d LEFT JOIN doc_tag_map m ON d.id = m.doc_id "
             f" WHERE (d.name LIKE '%{keyword}%' OR d.description LIKE '%{keyword}%') "
             f' {tagClause} ')).all()
    for d in results:
        doc = Doc(id=d[0], name=d[1], path=d[2],
                  ct=d[3], description=d[4], status=d[5])
        if not doc.id in id2doc:
            id2doc[doc.id] = doc.to_dict()
            id2doc[d.id]['tagIds'] = []
        if d[6] != None:
            id2doc[d.id]['tagIds'].append(d[6])

    # 其次按照全文内容搜索
    # TODO

    return list(id2doc.values()), 200


# 文档全文搜索
@doc.route('/docs/search', methods=['POST'])
@login_required
def search_docs():
    request_body = request.get_json()
    try:
        keyword = request_body['keyword']
    except KeyError:
        raise BadRequest

    results = search_docs(keyword)
    ids = [r['id'] for r in results]

    # 获取数据库中的相关文档和标签映射
    docs = Doc.query.filter(Doc.id.in_(ids)).all()
    maps = DocTagMap.query.all()

    # 将标签映射的ID和搜索结果补充到对应的文档中
    id2doc = {}
    for d in docs:
        id2doc[d.id] = d.to_dict()
        id2doc[d.id]['tags'] = []
    for m in maps:
        if m.doc_id in id2doc:
            id2doc[m.doc_id]['tags'].append(m.tag_id)
    for r in results:
        if r['id'] in id2doc:
            id2doc[r['id']]['result'] = r['content']

    return list(id2doc.values()), 200


# 下载某个文档
@doc.route('/docs/download/<id>', methods=['GET'])
@login_required
def download_doc(id):
    exists = Doc.query.filter_by(id=id).first()
    if not exists:
        return Response(status=404)

    root_folder = config['store-root']
    abs_path = os.path.join(root_folder, exists.path)
    if not os.path.exists(abs_path):
        return Response(status=404)

    return send_file(abs_path, as_attachment=True)


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
