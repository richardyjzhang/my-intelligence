# 封装ElasticSearch操作
from elasticsearch import Elasticsearch


from .. import config


# ElasticSearch连接
es = Elasticsearch(hosts=config['es-hosts'])

# ElasticSearch Index
ES_INDEX = 'my-intelligence'


# 存储一份文档
def index_one_document(id: int, content: str):
    try:
        es.index(index=ES_INDEX, body={
            "id": id,
            "content": content,
        })
    except Exception as e:
        print(e)


# 通过关键字全文检索文档
def search_documents(keyword: str):
    rs = es.search(
        query={
            'match': {
                'content': {
                    'query': keyword,
                    'analyzer': 'ik_smart'
                }
            },
        },
        _source=['id'],
        highlight={
            'pre_tags': '<FUCK>',
            'post_tags': '</FUCK>',
            'fields': {
                'content': {}
            }
        }
    )

    # 组装ES搜索结果并返回
    results = [{
        'id': r['_source']['id'],
        'content': r['highlight']['content']
    } for r in rs['hits']['hits']]
    return results
