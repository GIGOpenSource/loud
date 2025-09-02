"""
用户偏好视图
使用base基础类重构
"""

from rest_framework import permissions
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from base.views import BaseModelViewSet, BaseRetrieveUpdateAPIView
from base.permissions import IsOwnerOrReadOnly
from utils.response import BaseApiResponse
from utils.decorators import log_api_call, handle_exceptions

from .models import UserPreference
from .serializers import (
    UserPreferenceSerializer, UserPreferenceCreateSerializer,
    UserPreferenceUpdateSerializer, NotificationTypeSerializer,
    CustomSettingSerializer, PreferenceExportSerializer,
    PreferenceImportSerializer, UserPreferenceSummarySerializer
)
from .permissions import UserPreferencePermission


class UserPreferenceViewSet(BaseModelViewSet):
    """
    用户偏好视图集
    提供完整的偏好设置管理
    """
    queryset = UserPreference.objects.select_related('user').all()
    serializer_class = UserPreferenceSerializer
    create_serializer_class = UserPreferenceCreateSerializer
    update_serializer_class = UserPreferenceUpdateSerializer
    
    permission_classes = [permissions.IsAuthenticated, UserPreferencePermission]
    
    search_fields = ['user__username', 'theme', 'language']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 普通用户只能管理自己的偏好
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def perform_create_pre(self, serializer):
        """创建前设置用户"""
        serializer.validated_data['user'] = self.request.user
    
    def perform_create_post(self, instance, serializer):
        """创建后的业务逻辑"""
        # 清除用户相关缓存
        self.clear_user_cache(instance.user)
        
        # 记录日志
        self.log_preference_action('created', instance)
    
    def perform_update_post(self, instance, serializer):
        """更新后的业务逻辑"""
        # 清除用户相关缓存
        self.clear_user_cache(instance.user)
        
        # 记录更新的字段
        updated_fields = list(serializer.validated_data.keys())
        self.log_preference_action('updated', instance, extra_data={'fields': updated_fields})
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """获取当前用户的偏好设置"""
        preference, created = UserPreference.objects.get_or_create(
            user=request.user,
            defaults={}
        )
        
        serializer = self.get_serializer(preference)
        message = '获取偏好设置成功'
        if created:
            message = '首次创建偏好设置成功'
        
        return BaseApiResponse.success(
            data=serializer.data,
            message=message
        )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_my_preferences(self, request):
        """更新当前用户的偏好设置"""
        preference, created = UserPreference.objects.get_or_create(
            user=request.user,
            defaults={}
        )
        
        partial = request.method == 'PATCH'
        serializer = UserPreferenceUpdateSerializer(
            preference,
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # 清除缓存
            self.clear_user_cache(request.user)
            
            response_serializer = self.get_serializer(preference)
            return BaseApiResponse.success(
                data=response_serializer.data,
                message='偏好设置更新成功'
            )
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='偏好设置更新失败'
        )
    
    @action(detail=True, methods=['patch'])
    @log_api_call
    @handle_exceptions
    def update_notifications(self, request, pk=None):
        """更新通知设置"""
        preference = self.get_object()
        serializer = NotificationTypeSerializer(
            preference,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # 清除缓存
            self.clear_user_cache(preference.user)
            
            return BaseApiResponse.success(
                data=serializer.data,
                message='通知设置更新成功'
            )
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='通知设置更新失败'
        )
    
    @action(detail=True, methods=['patch'])
    @log_api_call
    @handle_exceptions
    def update_custom_settings(self, request, pk=None):
        """更新自定义设置"""
        preference = self.get_object()
        serializer = CustomSettingSerializer(
            preference,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # 清除缓存
            self.clear_user_cache(preference.user)
            
            return BaseApiResponse.success(
                data=serializer.data,
                message='自定义设置更新成功'
            )
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='自定义设置更新失败'
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    def reset_to_defaults(self, request, pk=None):
        """重置为默认设置"""
        preference = self.get_object()
        preference.reset_to_defaults()
        
        # 清除缓存
        self.clear_user_cache(preference.user)
        
        serializer = self.get_serializer(preference)
        return BaseApiResponse.success(
            data=serializer.data,
            message='已重置为默认设置'
        )
    
    @action(detail=True, methods=['get'])
    @method_decorator(cache_page(60 * 5))  # 缓存5分钟
    def export_settings(self, request, pk=None):
        """导出设置"""
        preference = self.get_object()
        serializer = PreferenceExportSerializer(preference)
        
        return BaseApiResponse.success(
            data=serializer.data,
            message='设置导出成功'
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    def import_settings(self, request, pk=None):
        """导入设置"""
        preference = self.get_object()
        serializer = PreferenceImportSerializer(data=request.data)
        
        if serializer.is_valid():
            settings_data = serializer.validated_data['settings_data']
            preference.import_settings(settings_data)
            
            # 清除缓存
            self.clear_user_cache(preference.user)
            
            response_serializer = self.get_serializer(preference)
            return BaseApiResponse.success(
                data=response_serializer.data,
                message='设置导入成功'
            )
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='设置导入失败'
        )
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """获取偏好设置摘要"""
        preference = self.get_object()
        serializer = UserPreferenceSummarySerializer(preference)
        
        return BaseApiResponse.success(
            data=serializer.data,
            message='获取偏好摘要成功'
        )
    
    @action(detail=False, methods=['get'])
    def available_options(self, request):
        """获取可用选项"""
        options = {
            'themes': [{'value': choice[0], 'label': choice[1]} for choice in UserPreference.THEME_CHOICES],
            'languages': [{'value': choice[0], 'label': choice[1]} for choice in UserPreference.LANGUAGE_CHOICES],
            'timezones': self.get_available_timezones(),
            'notification_types': self.get_notification_types_info(),
        }
        
        return BaseApiResponse.success(
            data=options,
            message='获取可用选项成功'
        )
    
    def get_available_timezones(self):
        """获取可用时区列表"""
        import pytz
        
        # 常用时区
        common_timezones = [
            ('Asia/Shanghai', '中国标准时间 (UTC+8)'),
            ('Asia/Hong_Kong', '香港时间 (UTC+8)'),
            ('Asia/Taipei', '台北时间 (UTC+8)'),
            ('Asia/Tokyo', '日本标准时间 (UTC+9)'),
            ('Asia/Seoul', '韩国标准时间 (UTC+9)'),
            ('US/Pacific', '美国太平洋时间 (UTC-8)'),
            ('US/Eastern', '美国东部时间 (UTC-5)'),
            ('Europe/London', '格林威治标准时间 (UTC+0)'),
            ('Europe/Paris', '中欧时间 (UTC+1)'),
            ('UTC', '协调世界时 (UTC+0)'),
        ]
        
        return [{'value': tz[0], 'label': tz[1]} for tz in common_timezones]
    
    def get_notification_types_info(self):
        """获取通知类型信息"""
        instance = UserPreference()
        default_types = instance.default_notification_types
        
        type_descriptions = {
            'system_updates': '系统更新通知',
            'security_alerts': '安全警告通知',
            'account_changes': '账户变更通知',
            'friend_requests': '好友请求通知',
            'messages': '消息通知',
            'mentions': '提及通知',
            'likes': '点赞通知',
            'comments': '评论通知',
            'marketing': '营销推广通知',
            'newsletters': '新闻简报通知',
        }
        
        return [
            {
                'key': key,
                'label': type_descriptions.get(key, key),
                'default': default_value,
                'description': f'控制是否接收{type_descriptions.get(key, key)}'
            }
            for key, default_value in default_types.items()
        ]
    
    def clear_user_cache(self, user):
        """清除用户相关缓存"""
        from django.core.cache import cache
        cache_keys = [
            f'user_preferences_{user.id}',
            f'user_dashboard_{user.id}',
            f'user_settings_{user.id}',
        ]
        for key in cache_keys:
            cache.delete(key)
    
    def log_preference_action(self, action, preference, extra_data=None):
        """记录偏好操作日志"""
        import logging
        logger = logging.getLogger('business')
        
        log_data = {
            'action': action,
            'user_id': preference.user.id,
            'preference_id': preference.id,
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        logger.info(f'User preference {action}', extra=log_data)
