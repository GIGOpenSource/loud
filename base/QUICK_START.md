# Base模块快速开始指南

## 🚀 5分钟快速上手

### 1. 创建一个简单的业务模型

```python
# myapp/models.py
from base.models import BaseAuditModel
from base.validators import mobile_validator

class Customer(BaseAuditModel):
    name = models.CharField('客户名称', max_length=100)
    mobile = models.CharField('手机号', max_length=11, validators=[mobile_validator])
    email = models.EmailField('邮箱', blank=True)
    
    class Meta:
        verbose_name = '客户'
        verbose_name_plural = '客户'
        db_table = 'customers'
    
    def __str__(self):
        return self.name
```

### 2. 创建序列化器

```python
# myapp/serializers.py
from base.serializers import BaseModelSerializer

class CustomerSerializer(BaseModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'mobile', 'email', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_mobile(self, value):
        return self.validate_phone(value)
```

### 3. 创建视图

```python
# myapp/views.py
from base.views import BaseModelViewSet

class CustomerViewSet(BaseModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    search_fields = ['name', 'mobile', 'email']
    filterset_fields = ['is_active']
    ordering = ['-created_at']
```

### 4. 配置URL

```python
# myapp/urls.py
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
urlpatterns = router.urls
```

### 5. 运行迁移

```bash
python manage.py makemigrations myapp
python manage.py migrate
```

## 🎯 立即获得的功能

- ✅ **完整的CRUD API** - 增删改查全套接口
- ✅ **自动时间戳** - created_at, updated_at 自动管理
- ✅ **审计功能** - created_by, updated_by 自动记录
- ✅ **状态管理** - is_active, status 内置支持
- ✅ **搜索过滤** - 自动支持搜索和过滤
- ✅ **分页功能** - 标准化分页响应
- ✅ **错误处理** - 统一的错误处理和响应格式
- ✅ **权限控制** - 灵活的权限管理
- ✅ **数据验证** - 丰富的验证器支持
- ✅ **批量操作** - 批量创建、更新、删除
- ✅ **缓存支持** - 自动缓存管理
- ✅ **日志记录** - API调用日志
- ✅ **工具类** - 丰富的业务工具

## 📋 可用的API接口

创建了上述代码后，你自动获得以下API接口：

```
GET    /customers/          # 获取客户列表（支持分页、搜索、过滤）
POST   /customers/          # 创建新客户
GET    /customers/{id}/     # 获取客户详情
PUT    /customers/{id}/     # 完整更新客户
PATCH  /customers/{id}/     # 部分更新客户  
DELETE /customers/{id}/     # 删除客户

# 批量操作
POST   /customers/batch_create/    # 批量创建
PATCH  /customers/batch_update/    # 批量更新
DELETE /customers/batch_destroy/   # 批量删除
```

## 🎨 高级功能示例

### 软删除模型

```python
from base.models import BaseSoftDeleteModel

class Product(BaseSoftDeleteModel):
    name = models.CharField('产品名称', max_length=100)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
```

### 自定义验证

```python
class ProductSerializer(BaseModelSerializer):
    def validate_business_rules(self, attrs):
        if attrs.get('price') <= 0:
            raise serializers.ValidationError('价格必须大于0')
```

### 自定义权限

```python
from base.permissions import BasePermission

class ProductPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user
```

### 自定义过滤器

```python
from base.filters import BaseFilterSet

class ProductFilterSet(BaseFilterSet):
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
```

## 💡 最佳实践

1. **模型继承**: 根据需要选择合适的基础模型
   - `BaseModel` - 基础功能（时间戳+状态）
   - `BaseAuditModel` - 审计功能
   - `BaseSoftDeleteModel` - 软删除功能
   - `BaseFullModel` - 完整功能

2. **序列化器分离**: 为不同操作创建专门的序列化器
   ```python
   class ProductListSerializer(BaseListSerializer):  # 列表展示
   class ProductDetailSerializer(BaseDetailSerializer):  # 详情展示
   class ProductCreateSerializer(BaseCreateSerializer):  # 创建操作
   ```

3. **权限分层**: 为不同操作设置不同权限
   ```python
   class ProductViewSet(BaseModelViewSet):
       list_permission_classes = [permissions.AllowAny]
       create_permission_classes = [permissions.IsAuthenticated]
       update_permission_classes = [IsOwnerOrAdmin]
   ```

## 🔧 工具类使用

```python
from base.utils import IDGenerator, NumberUtils, TextUtils

# 生成唯一ID
order_no = IDGenerator.generate_order_no('ORDER')

# 格式化数字
price = NumberUtils.format_currency(1234.56)  # ¥1234.56

# 文本处理
masked_phone = TextUtils.mask_mobile('13888888888')  # 138****8888
```

## 📚 完整文档

- 📖 [完整文档](README.md) - 详细的使用指南和API文档
- 🔍 [使用示例](../example_usage.py) - 完整的业务模块示例
- 🧪 测试你的模块 - 运行 `python manage.py shell` 测试功能

## 🆘 常见问题

**Q: 如何添加自定义字段验证？**
```python
def validate_custom_field(self, value):
    if not self.is_valid_custom_logic(value):
        raise serializers.ValidationError('自定义验证失败')
    return value
```

**Q: 如何覆盖默认行为？**
```python
def perform_create_post(self, instance, serializer):
    # 创建后的自定义逻辑
    self.send_notification(instance)
```

**Q: 如何添加自定义动作？**
```python
@action(detail=True, methods=['post'])
def custom_action(self, request, pk=None):
    instance = self.get_object()
    # 自定义逻辑
    return BaseApiResponse.success(data=...)
```

现在你已经准备好开始快速开发了！🎉
