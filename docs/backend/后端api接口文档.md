# 智能字幕翻译系统API接口文档

版本：v1.0.0  
生效日期：2025-05-06  

---

## 一、用户系统接口

### 1.1 用户基础接口（基于FastAPI-Users）  

| 接口     | 方法    | 路径                   | 输入                             | 输出        | 权限   |  
|--------|-------|----------------------|--------------------------------|-----------|------|  
| 用户注册   | POST  | `/auth/register`     | `email`, `password`            | 用户ID      | 公开   |  
| 用户登录   | POST  | `/auth/login`        | `email`, `password`            | JWT令牌     | 公开   |  
| 获取当前用户 | GET   | `/users/me`          | -                              | 用户详情（含角色） | 认证用户 |  
| 修改密码   | PATCH | `/users/me/password` | `old_password`, `new_password` | 状态码       | 认证用户 |  

技术实现：  
• 使用FastAPI-Users的`UserManager`和`AuthenticationBackend`
• JWT令牌有效期24小时，通过`python-jose`库实现  


---

## 二、核心翻译接口

### 2.1 文件翻译  
接口：POST `/v1/translate/file`  
输入：  
```json
{
  "file": "Base64编码的SRT文件",
  "source_lang": "zh",
  "target_lang": "en",
  "glossary_id": "GL20250506"
}
```  
输出：  
```json
{
  "task_id": "UUID",
  "status": "pending",
  "download_url": "https://cdn.example.com/files/{task_id}.srt"
}
```  
流程：  
1. 异步处理流水线（Agno智能体协作）  
2. 支持进度查询WebSocket：`/v1/translate/status/{task_id}`  

---

### 2.2 文本翻译
接口：POST `/v1/translate/text`  
输入：  
```json
{
  "text": "需要翻译的文本",
  "source_lang": "zh",
  "target_lang": "en",
  "glossary_id": "GL20250506"
}
```  
输出：  
```json
{
  "translated_text": "Translated text",
  "detected_lang": "zh",
  "model": "deepseek"
}
```  

---

## 三、术语管理接口

### 3.1 术语表操作

| 接口    | 方法     | 路径                    | 输入                                    | 输出      | 权限   |  
|-------|--------|-----------------------|---------------------------------------|---------|------|  
| 创建术语表 | POST   | `/v1/glossaries`      | `name`, `entries: [{source, target}]` | 术语表ID   | 管理员  |  
| 查询术语表 | GET    | `/v1/glossaries`      | `page=1`, `limit=10`                  | 分页术语表列表 | 认证用户 |  
| 更新术语表 | PUT    | `/v1/glossaries/{id}` | `entries`（全量更新）                       | 更新后的术语表 | 管理员  |  
| 删除术语表 | DELETE | `/v1/glossaries/{id}` | -                                     | 状态码     | 管理员  |  

数据结构：
```python
from pydantic import BaseModel
from typing import Optional

class GlossaryEntry(BaseModel):
    source: str  # 源语言术语
    target: str  # 目标语言术语
    context: Optional[str]  # 上下文示例
```  

---

## 四、敏感词管理接口

### 4.1 敏感词校验  
接口：POST `/v1/sensitive/validate`  
输入：  
```json
{
  "text": "待校验文本",
  "lang": "zh"
}
```  
输出：  
```json
{
  "is_valid": false,
  "invalid_words": ["敏感词1", "敏感词2"]
}
```  

### 4.2 敏感词库管理

| 接口    | 方法   | 路径                     | 输入                | 输出    | 权限  |  
|-------|------|------------------------|-------------------|-------|-----|  
| 添加敏感词 | POST | `/v1/sensitive/words`  | `word`, `lang`    | 新增词ID | 管理员 |  
| 批量导入  | POST | `/v1/sensitive/import` | CSV文件             | 导入结果  | 管理员 |  
| 查询敏感词 | GET  | `/v1/sensitive/words`  | `keyword`, `lang` | 敏感词列表 | 管理员 |  

---

## 五、历史记录接口

### 5.1 翻译历史

| 接口   | 方法     | 路径                 | 输入                       | 输出     | 权限   |  
|------|--------|--------------------|--------------------------|--------|------|  
| 查询历史 | GET    | `/v1/history`      | `start_date`, `end_date` | 翻译记录列表 | 认证用户 |  
| 删除记录 | DELETE | `/v1/history/{id}` | -                        | 状态码    | 认证用户 |  

数据结构：  
```python
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class TranslationHistory(BaseModel):
    id: UUID
    source_text: str
    translated_text: str
    created_at: datetime
```  

---

## 六、权限管理接口

### 6.1 角色管理（扩展FastAPI-Users）

| 接口   | 方法   | 路径                          | 输入                          | 输出   | 权限    |  
|------|------|-----------------------------|-----------------------------|------|-------|  
| 创建角色 | POST | `/v1/roles`                 | `name`, `permissions: list` | 角色ID | 超级管理员 |  
| 分配角色 | POST | `/v1/users/{user_id}/roles` | `role_id`                   | 状态码  | 管理员   |  
| 查询角色 | GET  | `/v1/roles`                 | `page=1`, `limit=10`        | 角色列表 | 管理员   |  

权限码设计：  
```text
translate:basic   基础翻译权限  
glossary:edit    术语编辑权限  
admin:full       超级管理员权限
```  

---

## 七、技术规范

1. RESTFul设计  
   • 资源命名使用复数形式（如`/glossaries`）
   • 错误响应统一格式：  

     ```json
     {
       "code": 4001,
       "detail": "SRT文件格式错误"
     }
     ```  

2. 安全规范  
   • 所有接口强制HTTPS
   • 敏感操作（如删除）需二次确认（X-Confirm头）  

3. 性能优化  
   • 文件翻译接口启用FastAPI的`BackgroundTasks`
   • 高频查询接口（如术语表）使用Redis缓存  
