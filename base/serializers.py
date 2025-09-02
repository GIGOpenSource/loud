"""
基础序列化器类
提供标准化的序列化器基类，统一处理数据验证、字段处理等
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.validators import validate_email
from django.contrib.auth import get_user_model
from datetime import date, datetime
import re

User = get_user_model()


class BaseSerializer(serializers.Serializer):
    """
    基础序列化器
    提供通用的验证和处理方法
    """
    
    def validate_phone(self, value):
        """验证手机号格式"""
        if not value:
            return value
        
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("手机号格式不正确")
        return value
    
    def validate_email(self, value):
        """验证邮箱格式"""
        if not value:
            return value
        
        try:
            validate_email(value)
        except Exception:
            raise serializers.ValidationError("邮箱格式不正确")
        return value
    
    def validate_date_not_future(self, value, field_name="日期"):
        """验证日期不能是未来"""
        if value and value > date.today():
            raise serializers.ValidationError(f"{field_name}不能是未来日期")
        return value
    
    def validate_datetime_not_future(self, value, field_name="时间"):
        """验证时间不能是未来"""
        if value and value > timezone.now():
            raise serializers.ValidationError(f"{field_name}不能是未来时间")
        return value
    
    def validate_positive_number(self, value, field_name="数值"):
        """验证正数"""
        if value is not None and value <= 0:
            raise serializers.ValidationError(f"{field_name}必须是正数")
        return value
    
    def validate_non_negative_number(self, value, field_name="数值"):
        """验证非负数"""
        if value is not None and value < 0:
            raise serializers.ValidationError(f"{field_name}不能是负数")
        return value
    
    def validate_string_length(self, value, min_length=None, max_length=None, field_name="字段"):
        """验证字符串长度"""
        if not value:
            return value
        
        if min_length and len(value) < min_length:
            raise serializers.ValidationError(f"{field_name}长度不能少于{min_length}个字符")
        
        if max_length and len(value) > max_length:
            raise serializers.ValidationError(f"{field_name}长度不能超过{max_length}个字符")
        
        return value
    
    def validate_chinese_name(self, value):
        """验证中文姓名"""
        if not value:
            return value
        
        pattern = r'^[\u4e00-\u9fa5]{2,10}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("姓名格式不正确，应为2-10个中文字符")
        return value
    
    def validate_username(self, value):
        """验证用户名格式"""
        if not value:
            return value
        
        pattern = r'^[a-zA-Z0-9_-]{3,20}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("用户名格式不正确，应为3-20个字母、数字、下划线或连字符")
        return value


class BaseModelSerializer(BaseSerializer, serializers.ModelSerializer):
    """
    基础模型序列化器
    提供模型序列化的通用功能
    """
    
    # 通用只读字段
    created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    
    class Meta:
        abstract = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 自动设置只读字段
        if hasattr(self.Meta, 'read_only_fields'):
            for field_name in self.Meta.read_only_fields:
                if field_name in self.fields:
                    self.fields[field_name].read_only = True
    
    def validate(self, attrs):
        """模型级别验证"""
        attrs = super().validate(attrs)
        
        # 执行自定义业务验证
        self.validate_business_rules(attrs)
        
        return attrs
    
    def validate_business_rules(self, attrs):
        """业务规则验证，子类可重写"""
        pass
    
    def create(self, validated_data):
        """创建实例"""
        # 添加创建者信息
        if hasattr(self.context.get('request'), 'user'):
            user = self.context['request'].user
            if hasattr(self.Meta.model, 'created_by') and 'created_by' not in validated_data:
                validated_data['created_by'] = user
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新实例"""
        # 添加更新者信息
        if hasattr(self.context.get('request'), 'user'):
            user = self.context['request'].user
            if hasattr(instance, 'updated_by'):
                validated_data['updated_by'] = user
        
        return super().update(instance, validated_data)


class TimestampSerializer(BaseSerializer):
    """
    时间戳序列化器
    用于包含创建和更新时间的序列化
    """
    created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')


class UserInfoSerializer(BaseSerializer):
    """
    用户信息序列化器
    用于显示用户基本信息
    """
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    nickname = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


class CreatedBySerializer(UserInfoSerializer):
    """
    创建者信息序列化器
    """
    pass


class UpdatedBySerializer(UserInfoSerializer):
    """
    更新者信息序列化器
    """
    pass


class AuditSerializer(BaseSerializer):
    """
    审计信息序列化器
    包含创建者、更新者和时间戳信息
    """
    created_by = CreatedBySerializer(read_only=True)
    updated_by = UpdatedBySerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')


class BaseListSerializer(BaseModelSerializer):
    """
    基础列表序列化器
    用于列表展示，通常包含较少字段
    """
    
    class Meta:
        abstract = True
        fields = ['id', 'created_at', 'updated_at']


class BaseDetailSerializer(BaseModelSerializer):
    """
    基础详情序列化器
    用于详情展示，包含完整字段
    """
    
    class Meta:
        abstract = True


class BaseCreateSerializer(BaseModelSerializer):
    """
    基础创建序列化器
    用于创建操作，排除自动生成的字段
    """
    
    class Meta:
        abstract = True
        read_only_fields = ['id', 'created_at', 'updated_at']


class BaseUpdateSerializer(BaseModelSerializer):
    """
    基础更新序列化器
    用于更新操作，排除不可更新的字段
    """
    
    class Meta:
        abstract = True
        read_only_fields = ['id', 'created_at', 'updated_at']


class BatchOperationSerializer(BaseSerializer):
    """
    批量操作序列化器
    """
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="要操作的ID列表"
    )
    
    def validate_ids(self, value):
        """验证ID列表"""
        if not value:
            raise serializers.ValidationError("ID列表不能为空")
        
        if len(value) > 100:
            raise serializers.ValidationError("单次操作不能超过100条记录")
        
        return value


class BatchUpdateSerializer(BatchOperationSerializer):
    """
    批量更新序列化器
    """
    data = serializers.DictField(help_text="要更新的数据")
    
    def validate_data(self, value):
        """验证更新数据"""
        if not value:
            raise serializers.ValidationError("更新数据不能为空")
        
        # 禁止更新敏感字段
        forbidden_fields = ['id', 'created_at', 'updated_at', 'created_by']
        for field in forbidden_fields:
            if field in value:
                raise serializers.ValidationError(f"不允许更新字段: {field}")
        
        return value


class SoftDeleteSerializer(BaseSerializer):
    """
    软删除序列化器
    """
    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    deleted_by = UserInfoSerializer(read_only=True)


class StatusSerializer(BaseSerializer):
    """
    状态序列化器
    """
    is_active = serializers.BooleanField(default=True, help_text="是否激活")
    status = serializers.CharField(max_length=20, required=False, help_text="状态")


class SearchSerializer(BaseSerializer):
    """
    搜索序列化器
    """
    search = serializers.CharField(
        required=False,
        max_length=100,
        help_text="搜索关键词"
    )
    
    def validate_search(self, value):
        """验证搜索关键词"""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("搜索关键词至少需要2个字符")
        
        return value.strip() if value else value


class PaginationSerializer(BaseSerializer):
    """
    分页序列化器
    """
    page = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="页码"
    )
    page_size = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        help_text="每页数量"
    )


class OrderingSerializer(BaseSerializer):
    """
    排序序列化器
    """
    ordering = serializers.CharField(
        required=False,
        max_length=50,
        help_text="排序字段，支持多字段用逗号分隔，负号表示降序"
    )
    
    def validate_ordering(self, value):
        """验证排序字段"""
        if not value:
            return value
        
        # 获取允许的排序字段
        allowed_fields = getattr(self.context.get('view'), 'ordering_fields', [])
        
        if not allowed_fields:
            return value
        
        # 解析排序字段
        fields = [field.strip() for field in value.split(',')]
        
        for field in fields:
            # 移除负号
            clean_field = field.lstrip('-')
            if clean_field not in allowed_fields:
                raise serializers.ValidationError(f"不支持的排序字段: {clean_field}")
        
        return value
