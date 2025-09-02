"""
用户偏好序列化器
使用base基础类重构
"""

from rest_framework import serializers
from base.serializers import BaseModelSerializer, BaseCreateSerializer, BaseUpdateSerializer
from .models import UserPreference


class UserPreferenceSerializer(BaseModelSerializer):
    """用户偏好序列化器"""
    
    # 添加一些计算字段
    available_themes = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    notification_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPreference
        fields = [
            'id', 'user', 'theme', 'language', 'timezone',
            'email_notifications', 'push_notifications', 'sms_notifications',
            'notification_types', 'show_online_status', 'allow_friend_requests',
            'allow_messages_from_strangers', 'auto_save_drafts',
            'enable_keyboard_shortcuts', 'items_per_page', 'custom_settings',
            'available_themes', 'available_languages', 'notification_summary',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_available_themes(self, obj):
        """获取可用主题列表"""
        return [{'value': choice[0], 'label': choice[1]} for choice in UserPreference.THEME_CHOICES]
    
    def get_available_languages(self, obj):
        """获取可用语言列表"""
        return [{'value': choice[0], 'label': choice[1]} for choice in UserPreference.LANGUAGE_CHOICES]
    
    def get_notification_summary(self, obj):
        """获取通知设置摘要"""
        enabled_count = 0
        total_count = 0
        
        # 统计基本通知设置
        basic_notifications = [
            obj.email_notifications,
            obj.push_notifications,
            obj.sms_notifications
        ]
        enabled_count += sum(basic_notifications)
        total_count += len(basic_notifications)
        
        # 统计详细通知类型
        if obj.notification_types:
            for enabled in obj.notification_types.values():
                if enabled:
                    enabled_count += 1
                total_count += 1
        
        return {
            'enabled_count': enabled_count,
            'total_count': total_count,
            'percentage': round((enabled_count / total_count * 100) if total_count > 0 else 0, 1)
        }
    
    def validate_theme(self, value):
        """验证主题设置"""
        valid_themes = [choice[0] for choice in UserPreference.THEME_CHOICES]
        if value not in valid_themes:
            raise serializers.ValidationError(f'无效的主题选择，可选项：{", ".join(valid_themes)}')
        return value
    
    def validate_language(self, value):
        """验证语言设置"""
        valid_languages = [choice[0] for choice in UserPreference.LANGUAGE_CHOICES]
        if value not in valid_languages:
            raise serializers.ValidationError(f'无效的语言选择，可选项：{", ".join(valid_languages)}')
        return value
    
    def validate_timezone(self, value):
        """验证时区设置"""
        import pytz
        try:
            pytz.timezone(value)
        except pytz.UnknownTimeZoneError:
            raise serializers.ValidationError('无效的时区设置')
        return value
    
    def validate_items_per_page(self, value):
        """验证每页显示条数"""
        return self.validate_positive_number(value, '每页显示条数')
    
    def validate_business_rules(self, attrs):
        """业务规则验证"""
        # 验证每页显示条数范围
        items_per_page = attrs.get('items_per_page')
        if items_per_page and (items_per_page < 5 or items_per_page > 100):
            raise serializers.ValidationError({'items_per_page': '每页显示条数必须在5-100之间'})


class UserPreferenceCreateSerializer(BaseCreateSerializer):
    """用户偏好创建序列化器"""
    
    class Meta:
        model = UserPreference
        fields = [
            'theme', 'language', 'timezone',
            'email_notifications', 'push_notifications', 'sms_notifications',
            'notification_types', 'show_online_status', 'allow_friend_requests',
            'allow_messages_from_strangers', 'auto_save_drafts',
            'enable_keyboard_shortcuts', 'items_per_page', 'custom_settings'
        ]
    
    def create(self, validated_data):
        """创建偏好设置"""
        # 设置默认通知类型
        if 'notification_types' not in validated_data:
            instance = UserPreference()
            validated_data['notification_types'] = instance.default_notification_types
        
        return super().create(validated_data)


class UserPreferenceUpdateSerializer(BaseUpdateSerializer):
    """用户偏好更新序列化器"""
    
    class Meta:
        model = UserPreference
        fields = [
            'theme', 'language', 'timezone',
            'email_notifications', 'push_notifications', 'sms_notifications',
            'notification_types', 'show_online_status', 'allow_friend_requests',
            'allow_messages_from_strangers', 'auto_save_drafts',
            'enable_keyboard_shortcuts', 'items_per_page', 'custom_settings'
        ]


class NotificationTypeSerializer(BaseModelSerializer):
    """通知类型设置序列化器"""
    
    class Meta:
        model = UserPreference
        fields = ['notification_types']
    
    def validate_notification_types(self, value):
        """验证通知类型设置"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('通知类型设置必须是字典格式')
        
        # 验证所有值都是布尔类型
        for key, val in value.items():
            if not isinstance(val, bool):
                raise serializers.ValidationError(f'通知类型 {key} 的值必须是布尔类型')
        
        return value


class CustomSettingSerializer(BaseModelSerializer):
    """自定义设置序列化器"""
    
    class Meta:
        model = UserPreference
        fields = ['custom_settings']
    
    def validate_custom_settings(self, value):
        """验证自定义设置"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('自定义设置必须是字典格式')
        
        # 限制自定义设置的大小
        import json
        settings_size = len(json.dumps(value))
        if settings_size > 10 * 1024:  # 10KB
            raise serializers.ValidationError('自定义设置数据过大，不能超过10KB')
        
        return value


class PreferenceExportSerializer(BaseModelSerializer):
    """偏好设置导出序列化器"""
    
    export_data = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPreference
        fields = ['export_data']
    
    def get_export_data(self, obj):
        """获取导出数据"""
        return obj.export_settings()


class PreferenceImportSerializer(serializers.Serializer):
    """偏好设置导入序列化器"""
    
    settings_data = serializers.JSONField(help_text='要导入的设置数据')
    
    def validate_settings_data(self, value):
        """验证导入的设置数据"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('设置数据必须是字典格式')
        
        # 验证必要的字段
        required_fields = ['theme', 'language']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f'缺少必要字段：{field}')
        
        # 验证主题和语言的有效性
        valid_themes = [choice[0] for choice in UserPreference.THEME_CHOICES]
        if value['theme'] not in valid_themes:
            raise serializers.ValidationError(f'无效的主题：{value["theme"]}')
        
        valid_languages = [choice[0] for choice in UserPreference.LANGUAGE_CHOICES]
        if value['language'] not in valid_languages:
            raise serializers.ValidationError(f'无效的语言：{value["language"]}')
        
        return value


class UserPreferenceSummarySerializer(BaseModelSerializer):
    """用户偏好摘要序列化器"""
    
    theme_display = serializers.SerializerMethodField()
    language_display = serializers.SerializerMethodField()
    notifications_enabled = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPreference
        fields = [
            'theme', 'theme_display', 'language', 'language_display',
            'timezone', 'notifications_enabled', 'items_per_page'
        ]
    
    def get_theme_display(self, obj):
        """获取主题显示名称"""
        return obj.get_theme_display()
    
    def get_language_display(self, obj):
        """获取语言显示名称"""
        return obj.get_language_display()
    
    def get_notifications_enabled(self, obj):
        """获取通知启用状态"""
        return {
            'email': obj.email_notifications,
            'push': obj.push_notifications,
            'sms': obj.sms_notifications,
            'total_enabled': sum([
                obj.email_notifications,
                obj.push_notifications,
                obj.sms_notifications
            ])
        }
