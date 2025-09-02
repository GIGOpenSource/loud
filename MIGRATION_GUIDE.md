# Users模块重构迁移指南

## 🚀 重构概述

本次重构将原有的单一users模块拆分为三个独立的子模块，使用base基础架构重新构建，实现了标准化的代码结构和更好的可维护性。

## 📁 新的模块结构

```
users/
├── __init__.py               # 模块初始化
├── apps.py                   # 应用配置
├── dashboard.py              # 仪表板视图
├── views.py                  # 统一视图入口
├── models.py                 # 统一模型导入
├── serializers.py            # 统一序列化器导入
├── admin.py                  # 统一管理后台
├── urls.py                   # 统一路由配置
├── signals.py                # 信号处理
├── migrations/               # 数据库迁移
├── profiles/                 # 用户资料子模块
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── permissions.py
│   ├── filters.py
│   ├── urls.py
│   └── admin.py
├── preferences/              # 用户偏好子模块
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── permissions.py
│   ├── urls.py
│   └── admin.py
└── wallets/                  # 用户钱包子模块
    ├── __init__.py
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── permissions.py
    ├── filters.py
    ├── urls.py
    └── admin.py
```

## 🔄 数据迁移步骤

### 步骤1: 备份现有数据

```bash
# 备份数据库
python manage.py dumpdata users > users_backup.json

# 备份媒体文件
cp -r media/avatars media/avatars_backup
```

### 步骤2: 生成新的迁移文件

```bash
# 删除旧的迁移文件（保留__init__.py和0001_initial.py）
rm users/migrations/0002_*.py  # 如果有的话

# 生成新的迁移
python manage.py makemigrations users
python manage.py makemigrations users.profiles
python manage.py makemigrations users.preferences  
python manage.py makemigrations users.wallets
```

### 步骤3: 执行迁移

```bash
# 运行迁移
python manage.py migrate users
python manage.py migrate users.profiles
python manage.py migrate users.preferences
python manage.py migrate users.wallets
```

### 步骤4: 数据迁移脚本

如果需要从旧结构迁移数据，可以使用以下脚本：

```python
# migration_script.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.profiles.models import UserProfile
from users.preferences.models import UserPreference
from users.wallets.models import UserWallet

User = get_user_model()

def migrate_existing_data():
    """迁移现有数据到新结构"""
    
    # 为所有现有用户创建profile、preference和wallet
    for user in User.objects.all():
        # 创建用户资料
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'nickname': user.username}
        )
        
        # 创建用户偏好
        preference, created = UserPreference.objects.get_or_create(
            user=user,
            defaults={}
        )
        
        # 创建用户钱包
        wallet, created = UserWallet.objects.get_or_create(
            user=user,
            defaults={'currency': 'CNY'}
        )
    
    print("数据迁移完成!")

if __name__ == '__main__':
    migrate_existing_data()
```

## 🔧 API接口变更

### 新的API结构

```
# 统一入口
GET /api/users/dashboard/              # 用户仪表板
GET /api/users/overview/               # 用户概览
GET /api/users/verify/                 # 用户验证
GET /api/users/module-info/            # 模块信息

# 用户资料 (profiles)
GET    /api/users/profiles/                    # 资料列表
POST   /api/users/profiles/                    # 创建资料
GET    /api/users/profiles/{id}/               # 资料详情
PUT    /api/users/profiles/{id}/               # 更新资料
DELETE /api/users/profiles/{id}/               # 删除资料
GET    /api/users/profiles/my_profile/         # 我的资料
PUT    /api/users/profiles/update_my_profile/  # 更新我的资料
POST   /api/users/profiles/{id}/upload_avatar/ # 上传头像
DELETE /api/users/profiles/{id}/delete_avatar/ # 删除头像
GET    /api/users/profiles/{id}/public_profile/ # 公开资料
GET    /api/users/public/{user_id}/            # 公开资料（简化）

# 用户偏好 (preferences)
GET    /api/users/preferences/                      # 偏好列表
POST   /api/users/preferences/                      # 创建偏好
GET    /api/users/preferences/{id}/                 # 偏好详情
PUT    /api/users/preferences/{id}/                 # 更新偏好
GET    /api/users/preferences/my_preferences/       # 我的偏好
PUT    /api/users/preferences/update_my_preferences/ # 更新我的偏好
PATCH  /api/users/preferences/{id}/update_notifications/ # 更新通知设置
POST   /api/users/preferences/{id}/reset_to_defaults/    # 重置默认
GET    /api/users/preferences/{id}/export_settings/      # 导出设置
POST   /api/users/preferences/{id}/import_settings/      # 导入设置

# 用户钱包 (wallets)
GET    /api/users/wallets/                    # 钱包列表
POST   /api/users/wallets/                    # 创建钱包
GET    /api/users/wallets/{id}/               # 钱包详情
PUT    /api/users/wallets/{id}/               # 更新钱包
GET    /api/users/wallets/my_wallet/          # 我的钱包
POST   /api/users/wallets/{id}/deposit/       # 充值
POST   /api/users/wallets/{id}/withdraw/      # 提现
POST   /api/users/wallets/{id}/transfer/      # 转账
POST   /api/users/wallets/{id}/freeze/        # 冻结金额
POST   /api/users/wallets/{id}/unfreeze/      # 解冻金额
POST   /api/users/wallets/{id}/set_payment_password/ # 设置支付密码
GET    /api/users/wallets/{id}/stats/         # 钱包统计
GET    /api/users/wallets/{id}/transactions/  # 交易记录

# 交易记录
GET    /api/users/transactions/              # 交易列表
GET    /api/users/transactions/{id}/         # 交易详情
POST   /api/users/transactions/{id}/refund/  # 申请退款
GET    /api/users/transactions/my_transactions/ # 我的交易
GET    /api/users/transactions/transaction_summary/ # 交易摘要
```

## 🎯 使用base基础类的优势

### 1. 统一的模型基类
- `BaseAuditModel`: 自动审计功能（创建者、更新者、时间戳）
- `StatusMixin`: 状态管理
- 内置缓存清理和业务逻辑钩子

### 2. 标准化的序列化器
- `BaseModelSerializer`: 通用验证方法
- 自动字段验证（手机号、邮箱、日期等）
- 业务规则验证钩子

### 3. 强大的视图基类
- `BaseModelViewSet`: 完整的CRUD操作
- 内置缓存管理
- 统一的错误处理和响应格式
- 自动日志记录

### 4. 灵活的权限控制
- `IsOwnerOrReadOnly`: 所有者权限
- 细粒度的权限控制
- 支持不同操作的不同权限

### 5. 丰富的过滤和搜索
- `BaseFilterSet`: 通用过滤器
- 时间范围过滤
- 复杂的业务逻辑过滤

## 🔒 安全性增强

### 1. 数据验证
- 使用base验证器进行严格的数据验证
- 防止SQL注入和XSS攻击
- 文件上传安全检查

### 2. 权限控制
- 基于角色的权限管理
- 对象级权限控制
- API访问频率限制

### 3. 数据加密
- 支付密码加密存储
- 敏感信息遮掩显示
- Cookie信息签名验证

## 📊 性能优化

### 1. 数据库优化
- 合理的索引设计
- 查询优化（select_related、prefetch_related）
- 分页和批量操作

### 2. 缓存策略
- 自动缓存管理
- 多层缓存策略
- 缓存失效控制

### 3. API性能
- 响应数据压缩
- 并行处理支持
- 异步任务处理

## 🧪 测试建议

### 1. 功能测试
```bash
# 运行完整测试
python manage.py test users

# 测试特定模块
python manage.py test users.profiles
python manage.py test users.preferences
python manage.py test users.wallets
```

### 2. API测试
```bash
# 安装测试工具
pip install httpie

# 测试用户仪表板
http GET localhost:8000/api/users/dashboard/ "Authorization:Bearer YOUR_TOKEN"

# 测试用户资料
http GET localhost:8000/api/users/profiles/my_profile/ "Authorization:Bearer YOUR_TOKEN"

# 测试钱包功能
http GET localhost:8000/api/users/wallets/my_wallet/ "Authorization:Bearer YOUR_TOKEN"
```

### 3. 性能测试
```bash
# 使用locust进行压力测试
pip install locust
locust -f performance_test.py
```

## 🐛 常见问题解决

### 1. 迁移问题
如果遇到迁移冲突：
```bash
# 重置迁移
python manage.py migrate users zero
python manage.py migrate users
```

### 2. 导入问题
如果遇到导入错误，确保在settings.py中：
```python
INSTALLED_APPS = [
    # ...
    'users',
    'users.profiles',
    'users.preferences', 
    'users.wallets',
    # ...
]
```

### 3. 权限问题
如果遇到权限错误，检查用户权限：
```python
# 在Django shell中
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(username='your_username')
>>> user.user_permissions.all()
>>> user.groups.all()
```

## 🎉 迁移完成检查

完成迁移后，请检查以下项目：

1. ✅ 所有API接口正常响应
2. ✅ 用户可以正常登录和访问资料
3. ✅ 钱包功能正常工作
4. ✅ 管理后台可以正常访问
5. ✅ 文件上传功能正常
6. ✅ 缓存和性能正常
7. ✅ 日志记录正常

## 📞 支持

如果在迁移过程中遇到问题，请：

1. 查看Django日志文件
2. 检查数据库连接和配置
3. 确认所有依赖包已安装
4. 检查文件权限设置

迁移完成后，你将拥有一个更加模块化、标准化和可维护的用户管理系统！🚀
