"""
Base模块使用示例
演示如何使用基础架构快速开发业务模块
"""

# 1. 模型示例
from django.db import models
from base.models import BaseAuditModel, StatusMixin
from base.validators import mobile_validator, chinese_name_validator

class Customer(BaseAuditModel):
    """客户模型示例"""
    name = models.CharField('客户名称', max_length=100, validators=[chinese_name_validator])
    mobile = models.CharField('手机号', max_length=11, validators=[mobile_validator])
    email = models.EmailField('邮箱', blank=True)
    company = models.CharField('公司', max_length=200, blank=True)
    level = models.CharField('客户等级', max_length=20, default='bronze')
    
    class Meta:
        verbose_name = '客户'
        verbose_name_plural = '客户'
        db_table = 'customers'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


# 2. 序列化器示例
from rest_framework import serializers
from base.serializers import BaseModelSerializer, BaseListSerializer

class CustomerSerializer(BaseModelSerializer):
    """客户序列化器"""
    level_display = serializers.SerializerMethodField('获取等级显示名称')
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'mobile', 'email', 'company', 'level', 'level_display', 
                 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_level_display(self, obj):
        level_map = {
            'bronze': '青铜',
            'silver': '白银', 
            'gold': '黄金',
            'platinum': '铂金'
        }
        return level_map.get(obj.level, obj.level)
    
    def validate_mobile(self, value):
        return self.validate_phone(value)
    
    def validate_business_rules(self, attrs):
        # 业务规则验证示例
        if attrs.get('level') == 'platinum' and not attrs.get('company'):
            raise serializers.ValidationError('铂金客户必须填写公司信息')

class CustomerListSerializer(BaseListSerializer):
    """客户列表序列化器"""
    class Meta:
        model = Customer
        fields = ['id', 'name', 'mobile', 'level', 'is_active', 'created_at']


# 3. 过滤器示例
from django_filters import rest_framework as filters
from base.filters import BaseFilterSet

class CustomerFilterSet(BaseFilterSet):
    """客户过滤器"""
    level = filters.ChoiceFilter(
        choices=[
            ('bronze', '青铜'),
            ('silver', '白银'),
            ('gold', '黄金'),
            ('platinum', '铂金'),
        ]
    )
    company = filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Customer
        fields = ['level', 'company', 'is_active']
        search_fields = ['name', 'mobile', 'email', 'company']


# 4. 权限示例
from base.permissions import BasePermission, IsOwnerOrReadOnly

class CustomerPermission(IsOwnerOrReadOnly):
    """客户权限"""
    def has_permission(self, request, view):
        # 添加额外的权限检查
        if request.method == 'POST':
            # 创建客户需要特定权限
            return request.user.has_perm('customer.add_customer')
        return super().has_permission(request, view)


# 5. 视图示例
from rest_framework.decorators import action
from rest_framework.response import Response
from base.views import BaseModelViewSet
from base.pagination import BasePagination
from utils.response import BaseApiResponse

class CustomerViewSet(BaseModelViewSet):
    """客户视图集"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    list_serializer_class = CustomerListSerializer
    filterset_class = CustomerFilterSet
    permission_classes = [CustomerPermission]
    pagination_class = BasePagination
    
    search_fields = ['name', 'mobile', 'email', 'company']
    ordering_fields = ['created_at', 'name', 'level']
    ordering = ['-created_at']
    
    def perform_create_post(self, instance, serializer):
        """创建后的业务逻辑"""
        # 发送欢迎邮件
        self.send_welcome_email(instance)
        
        # 记录操作日志
        self.log_customer_action('created', instance)
    
    def perform_update_post(self, instance, serializer):
        """更新后的业务逻辑"""
        # 如果等级发生变化，发送通知
        if 'level' in serializer.validated_data:
            self.send_level_change_notification(instance)
    
    @action(detail=True, methods=['post'])
    def upgrade_level(self, request, pk=None):
        """升级客户等级"""
        customer = self.get_object()
        
        level_progression = {
            'bronze': 'silver',
            'silver': 'gold', 
            'gold': 'platinum'
        }
        
        next_level = level_progression.get(customer.level)
        if not next_level:
            return BaseApiResponse.error(message='已是最高等级')
        
        customer.level = next_level
        customer.save(update_fields=['level'])
        
        return BaseApiResponse.success(
            data=self.get_serializer(customer).data,
            message=f'客户等级已升级为{next_level}'
        )
    
    @action(detail=False, methods=['get'])
    def level_statistics(self, request):
        """客户等级统计"""
        from django.db.models import Count
        
        stats = Customer.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')
        
        return BaseApiResponse.success(
            data=list(stats),
            message='获取等级统计成功'
        )
    
    def send_welcome_email(self, customer):
        """发送欢迎邮件"""
        from base.utils import EmailUtils
        
        if customer.email:
            EmailUtils.send_template_email(
                template_name='emails/welcome.html',
                context={'customer': customer},
                subject='欢迎加入我们',
                recipient_list=[customer.email]
            )
    
    def send_level_change_notification(self, customer):
        """发送等级变更通知"""
        # 这里可以集成短信、邮件、站内信等通知方式
        pass
    
    def log_customer_action(self, action, customer):
        """记录客户操作日志"""
        import logging
        logger = logging.getLogger('business')
        logger.info(f'Customer {action}: {customer.id} - {customer.name}')


# 6. URL配置示例
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]


# 7. 管理后台示例
from django.contrib import admin
from base.utils import TextUtils

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile_masked', 'email', 'level', 'is_active', 'created_at']
    list_filter = ['level', 'is_active', 'created_at']
    search_fields = ['name', 'mobile', 'email', 'company']
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'mobile', 'email', 'company')
        }),
        ('等级信息', {
            'fields': ('level', 'is_active')
        }),
        ('审计信息', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mobile_masked(self, obj):
        """遮掩手机号显示"""
        return TextUtils.mask_mobile(obj.mobile)
    mobile_masked.short_description = '手机号'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'updated_by')


# 8. 测试示例
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()

class CustomerModelTest(TestCase):
    """客户模型测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_customer(self):
        """测试创建客户"""
        customer = Customer.objects.create(
            name='张三',
            mobile='13888888888',
            email='zhangsan@example.com',
            level='bronze',
            created_by=self.user
        )
        
        self.assertEqual(customer.name, '张三')
        self.assertEqual(customer.level, 'bronze')
        self.assertTrue(customer.is_active)
        self.assertIsNotNone(customer.created_at)

class CustomerAPITest(APITestCase):
    """客户API测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_customer_api(self):
        """测试创建客户API"""
        data = {
            'name': '李四',
            'mobile': '13999999999',
            'email': 'lisi@example.com',
            'company': '测试公司',
            'level': 'silver'
        }
        
        response = self.client.post('/api/v1/customers/', data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['name'], '李四')
    
    def test_upgrade_level_api(self):
        """测试升级等级API"""
        customer = Customer.objects.create(
            name='王五',
            mobile='13777777777',
            level='bronze',
            created_by=self.user
        )
        
        response = self.client.post(f'/api/v1/customers/{customer.id}/upgrade_level/')
        self.assertEqual(response.status_code, 200)
        
        customer.refresh_from_db()
        self.assertEqual(customer.level, 'silver')


# 使用说明：
"""
1. 将以上代码保存为 customers/models.py、customers/serializers.py 等对应文件
2. 运行 python manage.py makemigrations customers
3. 运行 python manage.py migrate
4. 在 urls.py 中包含 customers.urls
5. 启动服务器，访问 /api/v1/customers/ 即可使用完整的客户管理API

这个示例展示了如何使用base模块快速构建一个完整的业务模块，包括：
- 模型定义（继承BaseAuditModel）
- 序列化器（继承BaseModelSerializer）
- 过滤器（继承BaseFilterSet）
- 权限控制（继承BasePermission）
- 视图集（继承BaseModelViewSet）
- 管理后台配置
- 测试用例

通过继承base模块的基础类，可以快速获得以下功能：
- 自动的时间戳管理
- 统一的错误处理
- 标准化的API响应格式
- 内置的分页和过滤
- 完整的CRUD操作
- 批量操作支持
- 缓存支持
- 日志记录
- 权限控制
"""
