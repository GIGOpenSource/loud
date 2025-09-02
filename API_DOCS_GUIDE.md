# 🚀 Loud 项目在线API文档使用指南

## 📚 文档访问地址

启动项目后，您可以通过以下地址访问API文档：

### 🎯 Swagger UI (推荐)
```
http://localhost:8000/api/docs/
```
- **功能**: 交互式API文档
- **特色**: 支持在线测试、自动认证管理
- **推荐用途**: 开发测试、接口调试

### 📖 ReDoc 
```
http://localhost:8000/api/redoc/
```
- **功能**: 美观的文档展示
- **特色**: 清晰的结构、详细说明
- **推荐用途**: 文档阅读、接口了解

### 🔧 OpenAPI Schema
```
http://localhost:8000/api/schema/
```
- **功能**: 原始OpenAPI 3.0格式数据
- **推荐用途**: 代码生成、第三方工具集成

## 🔐 认证系统

本项目支持多种认证方式，特别针对前端团队优化：

### 1. Cookie认证 (推荐) ✅
- **优势**: 登录后自动管理，无需手动设置token
- **使用方式**: 
  1. 先在文档中调用 `/api/auth/login/` 登录
  2. 登录成功后系统自动设置cookie
  3. 后续所有API调用自动携带认证信息

### 2. Token认证
- **使用方式**: 在请求头中添加 `Authorization: Token <your-token>`
- **获取token**: 通过 `/api/auth/login/` 接口返回

## 🚀 快速开始 (前端团队测试流程)

### 步骤1: 启动项目
```bash
# 进入项目目录
cd /Users/chan/Python/loud

# 激活虚拟环境
source .venv/bin/activate

# 启动开发服务器
python manage.py runserver 8000
```

### 步骤2: 访问API文档
打开浏览器访问: http://localhost:8000/api/docs/

### 步骤3: 用户登录
1. 找到 **Authentication** 标签下的 `/api/auth/login/` 接口
2. 点击 "Try it out"
3. 输入测试用户信息：
   ```json
   {
     "username": "admin",
     "password": "admin"
   }
   ```
4. 点击 "Execute"
5. 登录成功后，系统会自动设置cookie

### 步骤4: 测试其他接口
现在您可以测试任何需要认证的接口，例如：
- `/api/users/dashboard/` - 用户仪表板
- `/api/users/profiles/` - 用户资料管理
- `/api/users/wallets/` - 钱包管理

## 📋 主要API模块

### 🔑 Authentication (认证模块)
- **注册**: `POST /api/auth/register/`
- **登录**: `POST /api/auth/login/`
- **登出**: `POST /api/auth/logout/`
- **Token刷新**: `POST /api/auth/token/refresh/`

### 👤 User Profiles (用户资料)  
- **资料列表**: `GET /api/users/profiles/`
- **我的资料**: `GET /api/users/profiles/my_profile/`
- **公开资料**: `GET /api/users/public/{user_id}/`
- **更新资料**: `PUT/PATCH /api/users/profiles/{id}/`

### ⚙️ User Preferences (用户偏好)
- **偏好设置**: `GET/PUT /api/users/preferences/`
- **我的设置**: `GET /api/users/preferences/my_preferences/`

### 💰 User Wallets (用户钱包)
- **钱包信息**: `GET /api/users/wallets/`
- **我的钱包**: `GET /api/users/wallets/my_wallet/`
- **充值**: `POST /api/users/wallets/{id}/deposit/`
- **提现**: `POST /api/users/wallets/{id}/withdraw/`
- **转账**: `POST /api/users/wallets/{id}/transfer/`

### 📊 User Dashboard (用户仪表板)
- **仪表板**: `GET /api/users/dashboard/`
- **用户概览**: `GET /api/users/overview/`
- **用户验证**: `GET /api/users/verify/`

## 🎨 文档特色功能

### ✨ 交互式测试
- **一键测试**: 每个接口都有 "Try it out" 按钮
- **实时响应**: 显示真实的API响应数据
- **错误处理**: 清晰显示错误信息和状态码

### 🔄 自动认证管理
- **Cookie持久化**: 登录后自动保持认证状态
- **安全提示**: 显示当前认证状态
- **token刷新**: 支持token自动刷新

### 📖 详细文档
- **接口描述**: 每个接口都有详细的功能说明
- **参数说明**: 清晰的请求参数和响应格式
- **示例数据**: 提供真实的请求/响应示例

## 🛠️ 高级功能

### 🔍 API过滤和搜索
- 使用顶部搜索框快速找到特定接口
- 按标签分类浏览接口
- 支持操作ID搜索

### 📥 导出功能
- **OpenAPI规范**: 导出标准的OpenAPI 3.0文件
- **代码生成**: 支持多语言客户端代码生成
- **集成工具**: 兼容Postman、Insomnia等工具

### 🎯 测试技巧

#### 1. 批量测试流程
```
1. 登录 → 2. 获取用户信息 → 3. 测试业务接口 → 4. 登出
```

#### 2. 错误调试
- 查看响应状态码
- 检查错误消息详情
- 验证请求参数格式

#### 3. 性能观察
- 观察响应时间
- 检查数据结构
- 验证缓存效果

## 🔧 开发团队集成

### 前端集成
1. **API客户端生成**: 使用OpenAPI schema生成TypeScript/JavaScript客户端
2. **Mock数据**: 基于schema生成mock数据
3. **接口联调**: 使用真实接口进行开发测试

### 移动端集成
1. **SDK生成**: 支持iOS/Android SDK自动生成
2. **接口测试**: 使用文档验证移动端集成
3. **错误处理**: 参考文档处理各种异常情况

## 📞 技术支持

如果在使用过程中遇到问题：

1. **查看控制台**: 检查浏览器开发者工具的网络请求
2. **检查认证**: 确认登录状态和token有效性
3. **参数验证**: 对照文档检查请求参数格式
4. **服务状态**: 确认后端服务正常运行

## 🎉 总结

通过这个在线API文档系统，前端团队可以：
- ✅ **快速了解**: 所有可用的API接口
- ✅ **在线测试**: 无需额外工具即可测试接口
- ✅ **自动认证**: 登录后自动管理认证状态
- ✅ **实时调试**: 查看真实的请求和响应数据
- ✅ **高效协作**: 减少前后端沟通成本

**立即开始**: 访问 http://localhost:8000/api/docs/ 开始探索我们的API！

---

*更新时间: 2025-08-31*  
*文档版本: 2.0.0*  
*支持的API版本: v1*

