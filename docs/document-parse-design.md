# 文档解析流程设计

## 概述

文档上传后通过 Redis 队列驱动异步解析流程：Java 后端发布任务，Python 服务消费执行，包含 OCR 识别、全文索引、向量化存储三个阶段。

## 整体架构

```
用户上传 → Java(保存文件+写DB) → Redis doc:parse:queue
                                        ↓
                                  Python: 消费删除队列(清理ES+ChromaDB)
                                        ↓
                                  Python 阶段1: 清理旧数据 → 提交MinerU异步OCR
                                        ↓
                                  Redis doc:mineru:tasks (Hash跟踪)
                                        ↓
                                  Python 阶段2: 轮询MinerU结果 → Redis doc:index:queue
                                        ↓                      ↓ status=2 → Java更新DB
                                  Python 阶段3: 写ES + ChromaDB (每轮1个)
                                        ↓
                                  status=3 → Java更新DB

用户删除 → Java(删文件+删DB) → Redis doc:delete:queue
                                        ↓
                                  Python: 清理ES + ChromaDB
```

## 文档状态流转

| status | 含义 | 触发时机 |
|--------|------|----------|
| 1 | 待识别 | 文档上传成功后，Java 写入 DB |
| 2 | 识别完成 | MinerU OCR 完成，Python 通知 Java |
| 3 | 处理完成 | ES + ChromaDB 写入完成，Python 通知 Java |
| -1 | 处理失败 | 任何步骤异常时，Python 通知 Java |

## Redis 队列与数据结构

### 1. 解析任务队列 `doc:parse:queue`（List）

**方向**：Java → Python

**操作**：Java `LPUSH` 入队，Python `LPOP` 消费

```json
{
  "documentId": 123,
  "filePath": "documents/2026/03/xxx.pdf",
  "fileName": "原始文件名.pdf",
  "title": "文档标题",
  "tags": ["标签1", "标签2"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| documentId | long | 文档 ID（MySQL 主键） |
| filePath | string | 文件相对存储路径（相对于 `app.file.root-path`） |
| fileName | string | 原始文件名 |
| title | string | 文档标题 |
| tags | string[] | 标签名称列表 |

### 2. 删除任务队列 `doc:delete:queue`（List）

**方向**：Java → Python

**操作**：Java `LPUSH` 入队，Python `RPOP` 消费

```json
{
  "documentId": 123
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| documentId | long | 文档 ID（MySQL 主键） |

- 文档删除时由 Java 推入队列
- Python 消费后清理该文档在 ES 和 ChromaDB 中的数据
- 清理失败不影响流程（数据可能本就不存在）

### 3. MinerU 任务跟踪 `doc:mineru:tasks`（Hash）

**方向**：Python 内部使用

**操作**：`HSET` 写入，`HGETALL` 遍历，`HDEL` 移除

```
field: "123"  (documentId 字符串)
value: JSON字符串
```

```json
{
  "taskId": "mineru-task-uuid",
  "filePath": "documents/2026/03/xxx.pdf",
  "title": "文档标题",
  "tags": ["标签1", "标签2"],
  "fileName": "原始文件名.pdf",
  "submittedAt": "2026-03-31T10:01:00"
}
```

- 提交 MinerU 异步任务后写入
- 每轮轮询遍历，检查 MinerU 任务状态
- 完成或失败后 `HDEL` 移除
- 持久化在 Redis 中，Python 服务重启可恢复

### 4. 索引任务队列 `doc:index:queue`（List）

**方向**：Python 内部使用（阶段 2 生产 → 阶段 3 消费）

**操作**：`LPUSH` 入队，`LPOP` 消费（每轮仅取 1 个）

```json
{
  "documentId": 123,
  "title": "文档标题",
  "content": "MinerU 提取的完整 Markdown 文本...",
  "tags": ["标签1", "标签2"],
  "fileName": "原始文件名.pdf"
}
```

- MinerU 任务完成后，将 OCR 结果推入此队列
- 阶段 3 每轮只消费 1 个，串行写入 ES 和 ChromaDB，避免资源争抢

### 5. 状态回调队列 `doc:status:queue`（List）

**方向**：Python → Java

**操作**：Python `LPUSH` 入队，Java `BRPOP` 消费

```json
{
  "documentId": 123,
  "status": 2,
  "message": "OCR识别完成",
  "errorDetail": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| documentId | long | 文档 ID |
| status | int | 目标状态（2=识别完成, 3=处理完成, -1=失败） |
| message | string | 状态描述 |
| errorDetail | string/null | 仅 status=-1 时携带，错误详情 |

## Python 主循环设计

```
while True:
    # 消费删除队列（批量取完）
    while task = redis.RPOP("doc:delete:queue"):
        es.delete(task.documentId)
        chroma.delete(task.documentId)

    # 阶段1：消费解析队列（批量取完）
    while task = redis.RPOP("doc:parse:queue"):
        es.delete(task.documentId)        # 清理旧数据（首次/重识别均执行）
        chroma.delete(task.documentId)
        task_id = mineru.submit(task.filePath)
        redis.HSET("doc:mineru:tasks", task.documentId, {taskId, ...})

    # 阶段2：轮询 MinerU 结果
    for docId, info in redis.HGETALL("doc:mineru:tasks"):
        result = mineru.get_status(info.taskId)
        if result.done:
            redis.LPUSH("doc:index:queue", {docId, content, ...})
            redis.LPUSH("doc:status:queue", {docId, status=2})
            redis.HDEL("doc:mineru:tasks", docId)
        elif result.failed:
            redis.LPUSH("doc:status:queue", {docId, status=-1})
            redis.HDEL("doc:mineru:tasks", docId)

    # 阶段3：消费索引队列（每轮只处理1个）
    if item = redis.RPOP("doc:index:queue"):
        es.index(item)
        chroma.store(item)
        redis.LPUSH("doc:status:queue", {docId, status=3})

    sleep(60)
```

## MinerU 调用方式

调用 MinerU 云端精准解析 API（`https://mineru.net/api/v4`），需申请 Token。

- 申请上传链接：`POST /api/v4/file-urls/batch`（返回 batch_id + OSS 上传链接）
- 上传文件到 OSS：`PUT file_url`（系统自动提交解析任务）
- 轮询结果：`GET /api/v4/extract-results/batch/{batch_id}`
- 完成后返回 `full_zip_url`，下载 zip 解压取 `full.md` 即为 Markdown 文本
- 默认使用 vlm 模型，开启 OCR
- 多文档可并行解析，不互相阻塞

## 设计要点

- **Redis List 持久化**：重启不丢消息，LPOP 保证单消费者
- **Redis Hash 持久化**：MinerU 任务跟踪可恢复
- **索引串行消费**：每轮仅处理 1 个文档，避免 ES/Chroma 资源争抢
- **轮询间隔 60 秒**：平衡响应速度与资源消耗
- **状态解耦**：OCR 完成（status=2）和索引完成（status=3）分两次通知 Java
