"""
用户资料序列化器
使用base基础类重构
"""

from rest_framework import serializers
from base.serializers import BaseModelSerializer, BaseListSerializer, BaseCreateSerializer, BaseUpdateSerializer
from .models import UserProfile


class UserProfileSerializer(BaseModelSerializer):
    """用户资料序列化器"""
    
    display_name = serializers.ReadOnlyField()
    avatar_url = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'nickname', 'bio', 'avatar', 'avatar_url',
            'birth_date', 'gender', 'country', 'province', 'city', 'address',
            'website', 'twitter', 'github', 'profile_visibility',
            'show_email', 'show_phone', 'display_name', 'age', 'full_address',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_birth_date(self, value):
        """验证出生日期"""
        return self.validate_date_not_future(value, '出生日期')
    
    def validate_website(self, value):
        """验证网站URL"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError('网站链接必须以http://或https://开头')
        return value
    
    def validate_business_rules(self, attrs):
        """业务规则验证"""
        # 如果设置为显示邮箱，资料必须是公开的
        if attrs.get('show_email') and attrs.get('profile_visibility') == 'private':
            raise serializers.ValidationError('私密资料不能显示邮箱')


class UserProfileListSerializer(BaseListSerializer):
    """用户资料列表序列化器"""
    
    display_name = serializers.ReadOnlyField()
    avatar_url = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'display_name', 'avatar_url', 'bio', 'profile_visibility', 'updated_at']


class UserProfileCreateSerializer(BaseCreateSerializer):
    """用户资料创建序列化器"""
    
    class Meta:
        model = UserProfile
        fields = [
            'nickname', 'bio', 'birth_date', 'gender',
            'country', 'province', 'city', 'address',
            'website', 'twitter', 'github', 'profile_visibility',
            'show_email', 'show_phone'
        ]
    
    def validate_nickname(self, value):
        """验证昵称"""
        return self.validate_string_length(value, min_length=2, max_length=50, field_name='昵称')
    
    def validate_bio(self, value):
        """验证个人简介"""
        return self.validate_string_length(value, max_length=500, field_name='个人简介')


class UserProfileUpdateSerializer(BaseUpdateSerializer):
    """用户资料更新序列化器"""
    
    class Meta:
        model = UserProfile
        fields = [
            'nickname', 'bio', 'birth_date', 'gender',
            'country', 'province', 'city', 'address',
            'website', 'twitter', 'github', 'profile_visibility',
            'show_email', 'show_phone'
        ]
    
    def validate_nickname(self, value):
        """验证昵称"""
        return self.validate_string_length(value, min_length=2, max_length=50, field_name='昵称')
    
    def validate_bio(self, value):
        """验证个人简介"""
        return self.validate_string_length(value, max_length=500, field_name='个人简介')


class UserAvatarUploadSerializer(BaseModelSerializer):
    """用户头像上传序列化器"""
    
    class Meta:
        model = UserProfile
        fields = ['avatar']
    
    def validate_avatar(self, value):
        """验证头像文件"""
        if not value:
            raise serializers.ValidationError('请选择头像文件')
        
        # 验证文件大小
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError('头像文件大小不能超过5MB')
        
        # 验证文件格式
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f'不支持的文件格式，请使用：{", ".join(allowed_extensions)}')
        
        return value


class UserPublicProfileSerializer(BaseModelSerializer):
    """用户公开资料序列化器"""
    
    display_name = serializers.ReadOnlyField()
    avatar_url = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'display_name', 'bio', 'avatar_url', 'gender',
            'country', 'city', 'website', 'twitter', 'github', 'age'
        ]
        read_only_fields = ['id', 'user', 'display_name', 'age', 'avatar_url', 'full_address', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """根据隐私设置控制返回数据"""
        data = super().to_representation(instance)
        
        # 使用模型的get_public_data方法
        public_data = instance.get_public_data()
        
        # 只返回公开数据中包含的字段
        filtered_data = {}
        for key, value in data.items():
            if key in public_data:
                filtered_data[key] = public_data[key]
        
        return filtered_data


class UserProfileStatsSerializer(BaseModelSerializer):
    """用户资料统计序列化器"""
    
    profile_completeness = serializers.SerializerMethodField()
    last_login_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['profile_completeness', 'last_login_display']
    
    def get_profile_completeness(self, obj):
        """计算资料完整度"""
        total_fields = 10  # 主要字段数量
        filled_fields = 0
        
        # 检查各个字段是否填写
        if obj.nickname:
            filled_fields += 1
        if obj.bio:
            filled_fields += 1
        if obj.avatar:
            filled_fields += 1
        if obj.birth_date:
            filled_fields += 1
        if obj.gender:
            filled_fields += 1
        if obj.country:
            filled_fields += 1
        if obj.city:
            filled_fields += 1
        if obj.website:
            filled_fields += 1
        if obj.twitter:
            filled_fields += 1
        if obj.github:
            filled_fields += 1
        
        from base.utils import NumberUtils
        percentage = (filled_fields / total_fields)
        return NumberUtils.format_percentage(percentage)
    
    def get_last_login_display(self, obj):
        """获取最后登录时间显示"""
        if obj.user.last_login:
            from base.utils import DateUtils
            return DateUtils.format_datetime(obj.user.last_login)
        return '从未登录'
