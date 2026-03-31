# Elasticsearch 索引设计

## 概述

使用 Elasticsearch 存储文档 OCR 识别后的全文内容，支持中文全文检索。配合 IK 分词器实现精准的中文分词。

## 索引信息

- 索引名：`documents`
- ES 版本：8.x
- 分词器：IK（需安装 `elasticsearch-analysis-ik` 插件）

## 索引 Mapping

```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
      "analyzer": {
        "ik_max_analyzer": {
          "type": "custom",
          "tokenizer": "ik_max_word"
        },
        "ik_smart_analyzer": {
          "type": "custom",
          "tokenizer": "ik_smart"
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "documentId": {
        "type": "long"
      },
      "title": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart"
      },
      "content": {
        "type": "text",
        "analyzer": "ik_max_word",
        "search_analyzer": "ik_smart"
      },
      "tags": {
        "type": "keyword"
      },
      "fileName": {
        "type": "keyword"
      }
    }
  }
}
```

## 字段说明

| 字段 | ES 类型 | 说明 |
|------|---------|------|
| documentId | long | MySQL 中的文档主键，用于关联 |
| title | text (ik) | 文档标题，支持中文全文检索 |
| content | text (ik) | MinerU 提取的完整文本内容 |
| tags | keyword | 标签名称数组，精确过滤 |
| fileName | keyword | 原始文件名，精确匹配 |

## 分词器选择

- **索引时**使用 `ik_max_word`：最细粒度切分，确保最大化召回
- **搜索时**使用 `ik_smart`：智能切分，提高查准率

示例："中华人民共和国"
- ik_max_word：中华人民共和国 / 中华人民 / 中华 / 华人 / 人民共和国 / 人民 / 共和国 / 共和 / 国
- ik_smart：中华人民共和国

## 创建索引命令

```bash
curl -X PUT "http://localhost:9200/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    },
    "mappings": {
      "properties": {
        "documentId": { "type": "long" },
        "title": { "type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_smart" },
        "content": { "type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_smart" },
        "tags": { "type": "keyword" },
        "fileName": { "type": "keyword" }
      }
    }
  }'
```

## 查询示例

### 全文检索（标题 + 内容）

```json
{
  "query": {
    "multi_match": {
      "query": "搜索关键词",
      "fields": ["title^2", "content"],
      "type": "best_fields"
    }
  },
  "highlight": {
    "fields": {
      "title": {},
      "content": { "fragment_size": 200, "number_of_fragments": 3 }
    }
  }
}
```

- `title^2` 表示标题权重是内容的 2 倍

### 按标签过滤 + 全文检索

```json
{
  "query": {
    "bool": {
      "must": {
        "multi_match": {
          "query": "搜索关键词",
          "fields": ["title^2", "content"]
        }
      },
      "filter": {
        "terms": { "tags": ["标签1", "标签2"] }
      }
    }
  }
}
```

### 按文档 ID 精确查询

```json
{
  "query": {
    "term": { "documentId": 123 }
  }
}
```

## ChromaDB 向量存储

与 ES 全文检索互补，ChromaDB 用于语义相似度搜索。

- Collection 名：`documents`
- 分块策略：按段落分块，每块约 500 字，重叠 100 字
- Embedding：通过 OpenAI 兼容协议调用 Ollama 本地模型
- 每个 chunk 元数据：`documentId`、`chunkIndex`、`title`、`tags`
- ChromaDB 嵌入式运行（PersistentClient），数据持久化到 `data/chroma/` 目录
