# 🤖 Telegram社交登录集成指南

## 📋 概述

本项目已集成Telegram社交登录功能，用户可以通过Telegram账户快速登录系统。本指南详细介绍如何配置和使用Telegram登录功能。

## 🔧 配置要求

### 1. 创建Telegram Bot

1. **联系 @BotFather**
   - 在Telegram中搜索 `@BotFather`
   - 发送 `/newbot` 命令
   - 按提示设置bot名称和用户名

2. **获取Bot Token**
   - BotFather会提供一个token，格式类似：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - 妥善保存此token，它将用于API认证

3. **配置Bot设置**
   ```
   /setdomain - 设置网站域名
   /setdescription - 设置bot描述
   /setabouttext - 设置关于信息
   /setuserpic - 设置头像
   ```

### 2. 配置环境变量

在 `.env` 文件中添加以下配置：

```env
# Telegram社交登录设置
TELEGRAM_BOT_TOKEN=你的bot-token
TELEGRAM_BOT_NAME=你的bot用户名
```

### 3. Django配置

项目已自动配置以下内容：

- ✅ `django-allauth` 依赖已安装
- ✅ Telegram provider已启用
- ✅ 数据库migrations已应用
- ✅ URL路由已配置
- ✅ 认证后端已设置

## 📡 API端点

### 社交登录相关端点

```
POST /api/social/telegram/auth/          # Telegram登录认证
GET  /api/social/telegram/callback/      # Telegram登录回调
GET  /api/social/accounts/connected/     # 获取已连接账户
DELETE /api/social/accounts/disconnect/<provider>/  # 断开社交账户
GET  /api/social/check/                  # 社交登录状态检查
```

### 传统认证端点（仍然可用）

```
POST /api/auth/register/     # 用户注册
POST /api/auth/login/        # 用户登录
POST /api/auth/logout/       # 用户登出
GET  /api/auth/check/        # 认证状态检查
```

## 🔐 认证流程

### Telegram登录流程

1. **前端集成**
   - 使用Telegram Login Widget或自定义实现
   - 获取Telegram认证数据

2. **API调用**
   ```javascript
   // POST /api/social/telegram/auth/
   {
     "id": 123456789,
     "first_name": "张三",
     "last_name": "Li",
     "username": "zhangsan",
     "photo_url": "https://...",
     "auth_date": 1609459200,
     "hash": "abc123..."
   }
   ```

3. **响应示例**
   ```json
   {
     "success": true,
     "code": 2000,
     "message": "Telegram登录成功",
     "data": {
       "message": "Telegram登录成功",
       "user": {
         "id": 1,
         "username": "zhangsan_123",
         "email": "tg_123456789@telegram.local",
         "first_name": "张三",
         "last_name": "Li"
       },
       "access_token": "32位短token",
       "refresh_token": "32位刷新token",
       "is_new_user": true
     }
   }
   ```

## 💻 前端集成示例

### 1. Telegram Login Widget (推荐)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Telegram登录</title>
    <script async src="https://telegram.org/js/telegram-widget.js?22"
            data-telegram-login="YourBotName"
            data-size="large"
            data-onauth="onTelegramAuth(user)"
            data-request-access="write">
    </script>
</head>
<body>
    <script type="text/javascript">
      function onTelegramAuth(user) {
        // 发送认证数据到后端
        fetch('/api/social/telegram/auth/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify(user)
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            console.log('登录成功:', data.data.user);
            // 处理登录成功逻辑
            window.location.href = '/dashboard/';
          } else {
            console.error('登录失败:', data.message);
          }
        })
        .catch(error => {
          console.error('请求失败:', error);
        });
      }
      
      function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
      }
    </script>
</body>
</html>
```

### 2. 自定义登录按钮

```javascript
// 检查Telegram Web App可用性
if (window.Telegram?.WebApp) {
  // 在Telegram内部浏览器中
  const tg = window.Telegram.WebApp;
  
  // 获取用户信息
  const user = tg.initDataUnsafe?.user;
  if (user) {
    // 自动登录
    authenticateWithTelegram(user);
  }
}

function authenticateWithTelegram(userData) {
  // 构建认证数据
  const authData = {
    id: userData.id,
    first_name: userData.first_name,
    last_name: userData.last_name,
    username: userData.username,
    photo_url: userData.photo_url,
    auth_date: Math.floor(Date.now() / 1000),
    hash: calculateHash(userData) // 需要实现hash计算
  };
  
  // 发送到后端认证
  fetch('/api/social/telegram/auth/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(authData)
  })
  .then(response => response.json())
  .then(handleAuthResponse);
}
```

## 🛠️ 开发测试

### 1. 启动开发服务器

```bash
python manage.py runserver
```

### 2. 访问API文档

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

### 3. 测试API端点

```bash
# 检查社交登录状态
curl http://localhost:8000/api/social/check/

# 模拟Telegram登录（需要真实的认证数据）
curl -X POST http://localhost:8000/api/social/telegram/auth/ \\
     -H "Content-Type: application/json" \\
     -d '{
       "id": 123456789,
       "first_name": "测试",
       "auth_date": 1609459200,
       "hash": "valid_hash_here"
     }'
```

## 🔒 安全考虑

### 1. 数据验证

- ✅ **HMAC验证**: 使用bot token验证Telegram数据完整性
- ✅ **时间窗口**: 认证数据5分钟内有效，防止重放攻击
- ✅ **签名校验**: 验证hash签名确保数据未被篡改

### 2. 用户管理

- ✅ **自动创建**: 首次登录自动创建用户账户
- ✅ **账户关联**: 支持绑定已有邮箱账户
- ✅ **防重复**: 避免重复创建相同Telegram用户

### 3. Token管理

- ✅ **短token**: 32位随机token，提高安全性
- ✅ **双token**: access token + refresh token机制
- ✅ **自动清理**: 定期清理过期token

## 🎯 用户体验优化

### 1. 自动填充信息

```python
# 系统会自动使用Telegram信息填充：
- username: 优先使用Telegram username，冲突时自动添加后缀
- first_name, last_name: 直接使用Telegram姓名
- email: 生成格式 tg_{telegram_id}@telegram.local
- avatar: 可获取Telegram头像URL
```

### 2. 无缝登录体验

- Cookie自动管理：登录后自动设置认证cookie
- 状态保持：支持"记住我"功能
- 快速认证：后续访问无需重新登录

### 3. 多端同步

- 支持Web端、移动端一致的登录体验
- Telegram内置浏览器优化
- 跨设备登录状态同步

## 📊 API文档集成

Telegram社交登录API已完全集成到项目的API文档中：

- **分类标签**: "Social Authentication"
- **详细描述**: 每个端点都有完整的参数说明
- **示例数据**: 提供真实的请求/响应示例
- **错误处理**: 详细的错误码和处理说明

## 🚀 生产部署

### 1. 环境配置

```bash
# 生产环境配置
TELEGRAM_BOT_TOKEN=真实的bot-token
TELEGRAM_BOT_NAME=生产环境bot名称
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 2. HTTPS要求

Telegram Login Widget要求HTTPS环境，确保：
- SSL证书正确配置
- 域名已在bot设置中注册
- 回调URL使用HTTPS协议

### 3. 性能优化

- 启用数据库连接池
- 配置Redis缓存
- 使用CDN加速静态资源

## ❓ 常见问题

### Q: Telegram登录失败怎么办？

A: 检查以下项目：
1. Bot Token是否正确配置
2. 认证数据hash是否有效
3. 时间戳是否在有效期内
4. 网络连接是否正常

### Q: 如何自定义登录后跳转？

A: 修改settings.py中的LOGIN_REDIRECT_URL配置

### Q: 支持哪些Telegram数据？

A: 支持的字段：
- id (必需)
- first_name (必需)
- last_name (可选)
- username (可选)
- photo_url (可选)
- auth_date (必需)
- hash (必需)

### Q: 如何处理用户名冲突？

A: 系统自动处理：
- 优先使用Telegram username
- 冲突时自动添加数字后缀
- 无username时使用 tg_{telegram_id} 格式

## 📞 技术支持

如需技术支持，请：

1. 查看API文档：http://localhost:8000/api/docs/
2. 检查日志文件：`logs/api.log`
3. 联系开发团队

---

**🎉 Telegram社交登录已成功集成！**

现在用户可以通过Telegram账户快速、安全地登录系统，享受无缝的身份验证体验。
