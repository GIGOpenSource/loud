# 业务模块基础架构

## 概述

本基础架构提供了标准化的业务模块开发框架，包含视图、序列化器、模型、过滤器、权限、验证器等基础组件，旨在提高团队开发效率和代码质量。

## 组件说明

### 1. 基础视图 (views.py)

提供标准化的API视图基类：

- `BaseAPIView` - 基础API视图，提供通用功能
- `BaseListAPIView` - 列表查询视图
- `BaseCreateAPIView` - 创建数据视图
- `BaseRetrieveAPIView` - 获取详情视图
- `BaseUpdateAPIView` - 更新数据视图
- `BaseDestroyAPIView` - 删除数据视图
- `BaseModelViewSet` - 完整的CRUD视图集

### 2. 基础序列化器 (serializers.py)

提供标准化的序列化器基类：

- `BaseSerializer` - 基础序列化器，包含通用验证方法
- `BaseModelSerializer` - 基础模型序列化器
- `BaseListSerializer` - 列表展示序列化器
- `BaseDetailSerializer` - 详情展示序列化器
- `BaseCreateSerializer` - 创建操作序列化器
- `BaseUpdateSerializer` - 更新操作序列化器

### 3. 基础模型 (models.py)

提供标准化的模型基类和混入：

- `TimestampMixin` - 时间戳混入
- `SoftDeleteMixin` - 软删除混入
- `AuditMixin` - 审计混入
- `StatusMixin` - 状态混入
- `BaseModel` - 基础模型
- `BaseAuditModel` - 审计模型
- `BaseSoftDeleteModel` - 软删除模型
- `BaseFullModel` - 完整功能模型

### 4. 基础过滤器 (filters.py)

提供标准化的过滤功能：

- `BaseFilterSet` - 基础过滤器
- `TimestampFilterSet` - 时间戳过滤器
- `SoftDeleteFilterSet` - 软删除过滤器
- `AuditFilterSet` - 审计过滤器

### 5. 基础权限 (permissions.py)

提供标准化的权限控制：

- `BasePermission` - 基础权限类
- `IsOwnerOrReadOnly` - 所有者或只读权限
- `RoleBasedPermission` - 基于角色的权限
- `ActionBasedPermission` - 基于动作的权限

### 6. 验证器 (validators.py)

提供常用的数据验证器：

- 中文姓名验证器
- 手机号验证器
- 身份证验证器
- 密码强度验证器
- 文件验证器等

### 7. 工具类 (utils.py)

提供通用的业务工具：

- `IDGenerator` - ID生成器
- `NumberUtils` - 数字工具
- `DateUtils` - 日期工具
- `CacheUtils` - 缓存工具
- `ValidationUtils` - 验证工具

## 使用指南

### 1. 创建基础模型

```python
from base.models import BaseAuditModel

class Product(BaseAuditModel):
    name = models.CharField('产品名称', max_length=100)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
    description = models.TextField('描述', blank=True)
    
    class Meta:
        verbose_name = '产品'
        verbose_name_plural = '产品'
        db_table = 'products'
```

### 2. 创建序列化器

```python
from base.serializers import BaseModelSerializer

class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        return self.validate_positive_number(value, '价格')

class ProductCreateSerializer(BaseCreateSerializer):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description']
```

### 3. 创建视图

```python
from base.views import BaseModelViewSet
from base.permissions import IsOwnerOrReadOnly

class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    create_serializer_class = ProductCreateSerializer
    permission_classes = [IsOwnerOrReadOnly]
    filterset_fields = ['name', 'price']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price']
```

### 4. 配置URL

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

## 开发规范

### 1. 命名规范

- **模型类**: 使用大驼峰命名，如 `UserProfile`
- **字段名**: 使用小写+下划线，如 `created_at`
- **方法名**: 使用小写+下划线，如 `get_user_info`
- **常量**: 使用大写+下划线，如 `MAX_FILE_SIZE`

### 2. 模型规范

- 继承适当的基础模型类
- 添加必要的Meta信息
- 实现`__str__`方法
- 添加模型级验证

```python
class Product(BaseAuditModel):
    name = models.CharField('产品名称', max_length=100)
    
    class Meta:
        verbose_name = '产品'
        verbose_name_plural = '产品'
        db_table = 'products'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        # 模型级验证
        if self.price <= 0:
            raise ValidationError('价格必须大于0')
```

### 3. 序列化器规范

- 继承适当的基础序列化器
- 添加字段级验证
- 实现业务逻辑验证

```python
class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        return self.validate_positive_number(value, '价格')
    
    def validate_business_rules(self, attrs):
        # 业务规则验证
        if attrs.get('category') == 'premium' and attrs.get('price') < 1000:
            raise serializers.ValidationError('高端产品价格不能低于1000元')
```

### 4. 视图规范

- 继承适当的基础视图类
- 配置必要的权限和过滤器
- 实现业务钩子方法

```python
class ProductViewSet(BaseModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filterset_class = ProductFilterSet
    search_fields = ['name', 'description']
    
    def perform_create_post(self, instance, serializer):
        # 创建后的业务逻辑
        self.send_notification(instance)
```

### 5. 权限规范

- 使用基础权限类
- 实现具体的权限逻辑
- 提供清晰的错误消息

```python
class ProductPermission(BasePermission):
    permission_code = 'product.manage'
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.created_by == request.user
```

### 6. 错误处理规范

- 使用标准的异常类
- 提供清晰的错误消息
- 记录必要的日志

```python
from utils.exceptions import BusinessException

class ProductNotAvailableException(BusinessException):
    default_detail = '产品暂不可用'
    default_code = 'product_not_available'
```

### 7. 文档规范

- 为所有公共方法添加文档字符串
- 使用类型提示
- 添加必要的注释

```python
def calculate_total_price(self, quantity: int) -> Decimal:
    """
    计算总价格
    
    Args:
        quantity: 购买数量
        
    Returns:
        计算后的总价格
        
    Raises:
        ValueError: 当数量小于等于0时
    """
    if quantity <= 0:
        raise ValueError('数量必须大于0')
    
    return self.price * quantity
```

## 最佳实践

### 1. 性能优化

- 使用`select_related`和`prefetch_related`优化查询
- 合理使用缓存
- 避免N+1查询问题

### 2. 安全性

- 验证所有用户输入
- 使用适当的权限控制
- 避免敏感信息泄露

### 3. 可维护性

- 保持代码简洁
- 遵循单一职责原则
- 编写测试用例

### 4. 扩展性

- 使用基础类便于扩展
- 保持接口稳定
- 支持向后兼容

## 示例项目结构

```
myapp/
├── models.py           # 模型定义
├── serializers.py      # 序列化器
├── views.py           # 视图
├── urls.py            # URL配置
├── permissions.py     # 权限类
├── filters.py         # 过滤器
├── admin.py          # 管理后台
├── tests.py          # 测试用例
└── migrations/       # 数据库迁移
```

## 常见问题

### Q: 如何选择合适的基础模型？

A: 根据业务需求选择：
- 只需要时间戳：继承`BaseModel`
- 需要审计功能：继承`BaseAuditModel`
- 需要软删除：继承`BaseSoftDeleteModel`
- 需要完整功能：继承`BaseFullModel`

### Q: 如何自定义验证器？

A: 继承基础验证器类并实现具体逻辑：

```python
@deconstructible
class CustomValidator:
    def __call__(self, value):
        if not self.is_valid(value):
            raise ValidationError('验证失败')
    
    def is_valid(self, value):
        # 实现验证逻辑
        return True
```

### Q: 如何处理复杂的权限逻辑？

A: 使用复合权限类：

```python
class ComplexPermission(CompositePermission):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    permission_logic = 'and'
```

## 更新日志

- v1.0.0: 初始版本，包含基础组件
- 后续版本将根据实际使用情况进行优化和扩展
