# Shrimp Agent V2 API 文档

## 概述

Shrimp Agent V2 提供了完整的 RESTful API 和 WebSocket API，支持智能搜索、文档管理、用户认证等核心功能。

## 基础信息

- **Base URL**: `https://api.shrimp-agent.com/api/v1`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`
- **API 版本**: v1

## 认证

### JWT Token 认证

所有需要认证的 API 请求都需要在 Header 中包含 JWT Token：

```http
Authorization: Bearer <your_jwt_token>
```

### Token 刷新

Access Token 有效期为 15 分钟，Refresh Token 有效期为 7 天。

## API 端点

### 1. 认证 API

#### 1.1 用户登录

```http
POST /auth/login
```

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "full_name": "User Name",
    "is_active": true
  }
}
```

#### 1.2 用户注册

```http
POST /auth/register
```

**请求体**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "User Name"
}
```

**响应**:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "full_name": "User Name",
    "is_active": true
  }
}
```

#### 1.3 刷新 Token

```http
POST /auth/refresh
```

**请求体**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### 1.4 用户登出

```http
POST /auth/logout
```

**Headers**: `Authorization: Bearer <token>`

**响应**:
```json
{
  "message": "Successfully logged out"
}
```

### 2. 用户管理 API

#### 2.1 获取当前用户信息

```http
GET /users/me
```

**Headers**: `Authorization: Bearer <token>`

**响应**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "full_name": "User Name",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "preferences": {
    "theme": "light",
    "language": "zh-CN",
    "notifications": true
  }
}
```

#### 2.2 更新用户信息

```http
PUT /users/me
```

**Headers**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "full_name": "New Name",
  "preferences": {
    "theme": "dark",
    "language": "en-US",
    "notifications": false
  }
}
```

**响应**:
```json
{
  "message": "User updated successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "full_name": "New Name",
    "preferences": {
      "theme": "dark",
      "language": "en-US",
      "notifications": false
    }
  }
}
```

#### 2.3 修改密码

```http
PUT /users/me/password
```

**Headers**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "current_password": "old_password",
  "new_password": "new_password123"
}
```

**响应**:
```json
{
  "message": "Password updated successfully"
}
```

### 3. 文档管理 API

#### 3.1 获取文档列表

```http
GET /documents
```

**Headers**: `Authorization: Bearer <token>`

**查询参数**:
- `page`: 页码（默认: 1）
- `size`: 每页数量（默认: 20）
- `search`: 搜索关键词
- `file_type`: 文件类型过滤
- `status`: 状态过滤
- `sort`: 排序字段（created_at, updated_at, title, file_size）
- `order`: 排序方向（asc, desc）

**响应**:
```json
{
  "documents": [
    {
      "id": "uuid",
      "title": "Document Title",
      "file_name": "document.pdf",
      "file_type": "application/pdf",
      "file_size": 1024000,
      "status": "processed",
      "tags": ["important", "work"],
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "metadata": {
        "pages": 10,
        "author": "Author Name"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### 3.2 上传文档

```http
POST /documents
```

**Headers**: 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**请求体**:
```
file: <binary_file>
title: "Document Title" (可选)
tags: ["tag1", "tag2"] (可选)
metadata: {"key": "value"} (可选)
```

**响应**:
```json
{
  "message": "Document uploaded successfully",
  "document": {
    "id": "uuid",
    "title": "Document Title",
    "file_name": "document.pdf",
    "file_type": "application/pdf",
    "file_size": 1024000,
    "status": "processing",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 3.3 获取文档详情

```http
GET /documents/{document_id}
```

**Headers**: `Authorization: Bearer <token>`

**响应**:
```json
{
  "id": "uuid",
  "title": "Document Title",
  "file_name": "document.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000,
  "status": "processed",
  "content": "Document content...",
  "tags": ["important", "work"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "metadata": {
    "pages": 10,
    "author": "Author Name",
    "word_count": 5000
  },
  "chunks": [
    {
      "id": "uuid",
      "content": "Chunk content...",
      "chunk_index": 0,
      "start_char": 0,
      "end_char": 500
    }
  ]
}
```

#### 3.4 更新文档

```http
PUT /documents/{document_id}
```

**Headers**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "title": "New Title",
  "tags": ["updated", "important"],
  "metadata": {
    "category": "work",
    "priority": "high"
  }
}
```

**响应**:
```json
{
  "message": "Document updated successfully",
  "document": {
    "id": "uuid",
    "title": "New Title",
    "tags": ["updated", "important"],
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 3.5 删除文档

```http
DELETE /documents/{document_id}
```

**Headers**: `Authorization: Bearer <token>`

**响应**:
```json
{
  "message": "Document deleted successfully"
}
```

#### 3.6 重新处理文档

```http
POST /documents/{document_id}/process
```

**Headers**: `Authorization: Bearer <token>`

**响应**:
```json
{
  "message": "Document processing started",
  "task_id": "uuid"
}
```

### 4. 搜索 API

#### 4.1 搜索文档

```http
POST /search/documents
```

**Headers**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "query": "search query",
  "strategy": "semantic",
  "limit": 10,
  "offset": 0,
  "filters": {
    "file_type": ["application/pdf", "text/plain"],
    "tags": ["important"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    },
    "file_size_range": {
      "min": 1024,
      "max": 10485760
    }
  },
  "sort": {
    "field": "relevance",
    "order": "desc"
  },
  "highlight": true,
  "include_content": true
}
```

**搜索策略**:
- `semantic`: 语义搜索
- `keyword`: 关键词搜索
- `hybrid`: 混合搜索
- `fuzzy`: 模糊搜索

**响应**:
```json
{
  "query": "search query",
  "strategy": "semantic",
  "total": 50,
  "results": [
    {
      "document": {
        "id": "uuid",
        "title": "Document Title",
        "file_name": "document.pdf",
        "file_type": "application/pdf",
        "tags": ["important"],
        "created_at": "2024-01-01T00:00:00Z"
      },
      "chunk": {
        "id": "uuid",
        "content": "Relevant content...",
        "chunk_index": 2,
        "highlighted_content": "Relevant <mark>search</mark> content..."
      },
      "score": 0.95,
      "relevance": "high"
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total": 50,
    "has_next": true
  },
  "facets": {
    "file_types": {
      "application/pdf": 30,
      "text/plain": 15,
      "application/docx": 5
    },
    "tags": {
      "important": 25,
      "work": 20,
      "personal": 5
    }
  },
  "search_time_ms": 150
}
```

#### 4.2 获取搜索建议

```http
GET /search/suggestions
```

**Headers**: `Authorization: Bearer <token>`

**查询参数**:
- `query`: 查询前缀
- `limit`: 建议数量（默认: 5）

**响应**:
```json
{
  "suggestions": [
    {
      "text": "machine learning",
      "type": "query",
      "frequency": 10
    },
    {
      "text": "artificial intelligence",
      "type": "query",
      "frequency": 8
    },
    {
      "text": "Document Title",
      "type": "document",
      "document_id": "uuid"
    }
  ]
}
```

#### 4.3 获取搜索历史

```http
GET /search/history
```

**Headers**: `Authorization: Bearer <token>`

**查询参数**:
- `limit`: 历史记录数量（默认: 20）
- `offset`: 偏移量（默认: 0）

**响应**:
```json
{
  "history": [
    {
      "id": "uuid",
      "query": "search query",
      "strategy": "semantic",
      "results_count": 15,
      "search_time_ms": 150,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 100
  }
}
```

#### 4.4 清除搜索历史

```http
DELETE /search/history
```

**Headers**: `Authorization: Bearer <token>`

**响应**:
```json
{
  "message": "Search history cleared successfully"
}
```

### 5. 智能问答 API

#### 5.1 发起对话

```http
POST /chat
```

**Headers**: `Authorization: Bearer <token>`

**请求体**:
```json
{
  "message": "What is machine learning?",
  "context": {
    "document_ids": ["uuid1", "uuid2"],
    "search_results": true,
    "conversation_id": "uuid"
  },
  "options": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000,
    "stream": false
  }
}
```

**响应**:
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "response": "Machine learning is a subset of artificial intelligence...",
  "sources": [
    {
      "document_id": "uuid",
      "document_title": "ML Basics",
      "chunk_id": "uuid",
      "relevance_score": 0.95
    }
  ],
  "metadata": {
    "model": "gpt-4",
    "tokens_used": 150,
    "response_time_ms": 2000
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 5.2 获取对话历史

```http
GET /chat/history
```

**Headers**: `Authorization: Bearer <token>`

**查询参数**:
- `conversation_id`: 对话 ID（可选）
- `limit`: 消息数量（默认: 50）
- `offset`: 偏移量（默认: 0）

**响应**:
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "Machine Learning Discussion",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T01:00:00Z",
      "message_count": 10,
      "messages": [
        {
          "id": "uuid",
          "role": "user",
          "content": "What is machine learning?",
          "created_at": "2024-01-01T00:00:00Z"
        },
        {
          "id": "uuid",
          "role": "assistant",
          "content": "Machine learning is...",
          "sources": [...],
          "created_at": "2024-01-01T00:01:00Z"
        }
      ]
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 5
  }
}
```

### 6. 管理 API

#### 6.1 系统统计

```http
GET /admin/stats
```

**Headers**: `Authorization: Bearer <admin_token>`

**响应**:
```json
{
  "users": {
    "total": 1000,
    "active": 800,
    "new_today": 10
  },
  "documents": {
    "total": 50000,
    "processed": 48000,
    "processing": 1000,
    "failed": 1000,
    "total_size_bytes": 10737418240
  },
  "searches": {
    "total": 100000,
    "today": 500,
    "avg_response_time_ms": 200
  },
  "system": {
    "uptime_seconds": 86400,
    "memory_usage_percent": 65,
    "cpu_usage_percent": 30,
    "disk_usage_percent": 45
  }
}
```

## WebSocket API

### 1. 实时聊天

**连接**: `ws://localhost:8000/ws/chat/{session_id}`

**认证**: 通过查询参数传递 token: `?token=<jwt_token>`

**消息格式**:

发送消息:
```json
{
  "type": "message",
  "data": {
    "message": "Hello, how can I help?",
    "context": {
      "document_ids": ["uuid1", "uuid2"]
    }
  }
}
```

接收消息:
```json
{
  "type": "response",
  "data": {
    "message_id": "uuid",
    "content": "I can help you with...",
    "sources": [...],
    "finished": true
  }
}
```

流式响应:
```json
{
  "type": "stream",
  "data": {
    "message_id": "uuid",
    "delta": "additional text",
    "finished": false
  }
}
```

### 2. 实时搜索

**连接**: `ws://localhost:8000/ws/search/{session_id}`

**搜索请求**:
```json
{
  "type": "search",
  "data": {
    "query": "search query",
    "strategy": "semantic",
    "filters": {...}
  }
}
```

**搜索结果**:
```json
{
  "type": "results",
  "data": {
    "results": [...],
    "total": 50,
    "search_time_ms": 150
  }
}
```

## 错误处理

### HTTP 状态码

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `422 Unprocessable Entity`: 请求格式正确但语义错误
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 服务器内部错误

### 错误响应格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "uuid"
  }
}
```

### 常见错误代码

- `VALIDATION_ERROR`: 输入验证错误
- `AUTHENTICATION_FAILED`: 认证失败
- `AUTHORIZATION_FAILED`: 授权失败
- `RESOURCE_NOT_FOUND`: 资源不存在
- `DUPLICATE_RESOURCE`: 资源重复
- `RATE_LIMIT_EXCEEDED`: 频率限制超出
- `INTERNAL_ERROR`: 内部服务器错误
- `SERVICE_UNAVAILABLE`: 服务不可用

## 限流规则

### API 限流

- **一般 API**: 100 请求/分钟
- **搜索 API**: 50 请求/分钟
- **上传 API**: 10 请求/分钟
- **认证 API**: 5 请求/分钟

### 限流响应头

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 60
```

## SDK 和客户端库

### JavaScript/TypeScript

```bash
npm install @shrimp-agent/client
```

```typescript
import { ShrimpClient } from '@shrimp-agent/client'

const client = new ShrimpClient({
  baseURL: 'https://api.shrimp-agent.com',
  apiKey: 'your-api-key'
})

// 搜索文档
const results = await client.search.documents({
  query: 'machine learning',
  strategy: 'semantic'
})

// 上传文档
const document = await client.documents.upload(file, {
  title: 'My Document',
  tags: ['important']
})
```

### Python

```bash
pip install shrimp-agent-client
```

```python
from shrimp_agent import ShrimpClient

client = ShrimpClient(
    base_url='https://api.shrimp-agent.com',
    api_key='your-api-key'
)

# 搜索文档
results = client.search.documents(
    query='machine learning',
    strategy='semantic'
)

# 上传文档
with open('document.pdf', 'rb') as f:
    document = client.documents.upload(
        file=f,
        title='My Document',
        tags=['important']
    )
```

## 测试环境

### 测试 API 端点

- **Base URL**: `https://api-test.shrimp-agent.com/api/v1`
- **WebSocket**: `wss://api-test.shrimp-agent.com/ws`

### 测试账户

```json
{
  "email": "test@example.com",
  "password": "test123456"
}
```

### Postman 集合

可以导入我们提供的 Postman 集合来快速测试 API：

[下载 Postman 集合](https://api.shrimp-agent.com/postman/collection.json)

## 更新日志

### v1.0.0 (2024-01-01)

- 初始 API 版本发布
- 支持用户认证和管理
- 支持文档上传和管理
- 支持语义搜索
- 支持智能问答

### v1.1.0 (计划中)

- 支持批量操作
- 增强搜索过滤器
- 支持文档协作
- 增加 Webhook 支持

---

如有任何问题或建议，请联系我们的技术支持团队：support@shrimp-agent.com