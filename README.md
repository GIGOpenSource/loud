# Loud - Django用户认证系统

基于Django 5.1的用户认证系统，支持session和cookie自动登录管理。

## 技术栈

- Django 5.1
- Django REST Framework
- Django Filter
- Django REST Framework Simple JWT
- Django CORS Headers

## 功能特性

### 用户认证
- ✅ 用户注册
- ✅ 用户登录（支持记住我功能）
- ✅ 用户登出
- ✅ 密码修改
- ✅ 密码重置
- ✅ 自动登录管理（Session + Cookie）

### 用户管理
- ✅ 自定义用户模型
- ✅ 用户资料管理
- ✅ 头像上传
- ✅ 用户状态管理

### API功能
- ✅ RESTful API
- ✅ JWT Token认证
- ✅ Session认证
- ✅ 权限控制
- ✅ 数据过滤和搜索
- ✅ 分页

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境配置

复制环境变量文件：
```bash
cp env.example .env
```

编辑 `.env` 文件，设置你的配置。

### 3. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级用户

```bash
python manage.py createsuperuser
```

### 5. 运行开发服务器

```bash
python manage.py runserver
```

## API接口

### 认证相关

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/auth/register/` | 用户注册 |
| POST | `/api/auth/login/` | 用户登录 |
| POST | `/api/auth/logout/` | 用户登出 |
| GET | `/api/auth/check/` | 检查认证状态 |
| POST | `/api/auth/refresh-session/` | 刷新session |
| POST | `/api/auth/token/refresh/` | 刷新JWT token |

### 密码相关

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/auth/password/change/` | 修改密码 |
| POST | `/api/auth/password/reset/` | 重置密码 |
| POST | `/api/auth/password/reset/confirm/` | 确认密码重置 |

### 用户资料

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/profile/` | 获取用户资料 |
| PUT | `/api/profile/` | 更新用户资料 |

### 用户管理（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/users/` | 用户列表 |
| GET | `/api/users/{id}/` | 用户详情 |
| PUT | `/api/users/{id}/` | 更新用户 |
| DELETE | `/api/users/{id}/` | 删除用户 |

## 使用示例

### 用户注册

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123",
    "nickname": "测试用户"
  }'
```

### 用户登录

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "remember_me": true
  }'
```

### 获取用户资料

```bash
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 配置说明

### Session配置

- `SESSION_COOKIE_AGE`: Session过期时间（7天）
- `SESSION_COOKIE_SECURE`: 生产环境设置为True
- `SESSION_COOKIE_HTTPONLY`: 防止XSS攻击
- `SESSION_COOKIE_SAMESITE`: 防止CSRF攻击

### JWT配置

- `ACCESS_TOKEN_LIFETIME`: 访问令牌有效期（60分钟）
- `REFRESH_TOKEN_LIFETIME`: 刷新令牌有效期（1天）

### CORS配置

支持跨域请求，默认允许localhost和127.0.0.1。

## 开发说明

### 自定义用户模型

项目使用自定义用户模型 `users.User`，扩展了Django默认用户模型：

- 添加了昵称、头像、手机号等字段
- 支持用户验证状态
- 记录最后登录时间

### 用户资料模型

`users.UserProfile` 模型存储用户的详细信息：

- 个人简介
- 出生日期、性别
- 地址信息
- 社交媒体链接

### 认证机制

系统支持双重认证机制：

1. **Session认证**: 用于Web界面，支持自动登录
2. **JWT认证**: 用于API接口，支持移动端和前端应用

## 部署说明

### 生产环境配置

1. 设置 `DEBUG=False`
2. 配置安全的 `SECRET_KEY`
3. 设置 `SESSION_COOKIE_SECURE=True`
4. 配置HTTPS
5. 使用生产级数据库（PostgreSQL/MySQL）

### 静态文件

```bash
python manage.py collectstatic
```

## 许可证

MIT License
