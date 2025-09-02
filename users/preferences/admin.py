"""
用户偏好管理后台
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json
from .models import UserPreference


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """用户偏好管理"""
    
    list_display = [
        'user_link', 'theme', 'language', 'timezone',
        'notifications_status', 'privacy_status', 'is_active', 'updated_at'
    ]
    
    list_filter = [
        'theme', 'language', 'email_notifications', 'push_notifications',
        'sms_notifications', 'show_online_status', 'allow_friend_requests',
        'is_active', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'timezone'
    ]
    
    readonly_fields = [
        'user', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'formatted_notification_types', 'formatted_custom_settings'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user',)
        }),
        ('界面设置', {
            'fields': ('theme', 'language', 'timezone', 'items_per_page')
        }),
        ('通知设置', {
            'fields': (
                'email_notifications', 'push_notifications', 'sms_notifications',
                'notification_types', 'formatted_notification_types'
            )
        }),
        ('隐私设置', {
            'fields': (
                'show_online_status', 'allow_friend_requests',
                'allow_messages_from_strangers'
            )
        }),
        ('功能设置', {
            'fields': ('auto_save_drafts', 'enable_keyboard_shortcuts'),
            'classes': ('collapse',)
        }),
        ('自定义设置', {
            'fields': ('custom_settings', 'formatted_custom_settings'),
            'classes': ('collapse',)
        }),
        ('状态信息', {
            'fields': ('is_active', 'status')
        }),
        ('审计信息', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-updated_at']
    
    def user_link(self, obj):
        """用户链接"""
        return format_html(
            '<a href="/admin/authentication/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = '用户'
    user_link.admin_order_field = 'user__username'
    
    def notifications_status(self, obj):
        """通知状态"""
        statuses = []
        if obj.email_notifications:
            statuses.append('<span style="color: green;">📧</span>')
        if obj.push_notifications:
            statuses.append('<span style="color: blue;">🔔</span>')
        if obj.sms_notifications:
            statuses.append('<span style="color: orange;">📱</span>')
        
        if not statuses:
            return mark_safe('<span style="color: #ccc;">无通知</span>')
        
        return mark_safe(' '.join(statuses))
    notifications_status.short_description = '通知状态'
    
    def privacy_status(self, obj):
        """隐私状态"""
        statuses = []
        if obj.show_online_status:
            statuses.append('在线状态')
        if obj.allow_friend_requests:
            statuses.append('好友请求')
        if obj.allow_messages_from_strangers:
            statuses.append('陌生人消息')
        
        if not statuses:
            return '全部关闭'
        
        return ' | '.join(statuses)
    privacy_status.short_description = '隐私设置'
    
    def formatted_notification_types(self, obj):
        """格式化通知类型显示"""
        if not obj.notification_types:
            return mark_safe('<span style="color: #ccc;">无设置</span>')
        
        formatted = json.dumps(obj.notification_types, indent=2, ensure_ascii=False)
        return format_html('<pre style="font-size: 12px;">{}</pre>', formatted)
    formatted_notification_types.short_description = '通知类型设置'
    
    def formatted_custom_settings(self, obj):
        """格式化自定义设置显示"""
        if not obj.custom_settings:
            return mark_safe('<span style="color: #ccc;">无设置</span>')
        
        formatted = json.dumps(obj.custom_settings, indent=2, ensure_ascii=False)
        return format_html('<pre style="font-size: 12px;">{}</pre>', formatted)
    formatted_custom_settings.short_description = '自定义设置'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related(
            'user', 'created_by', 'updated_by'
        )
    
    actions = [
        'activate_preferences', 'deactivate_preferences',
        'enable_all_notifications', 'disable_all_notifications',
        'reset_to_defaults'
    ]
    
    def activate_preferences(self, request, queryset):
        """批量激活偏好设置"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'成功激活 {count} 个偏好设置')
    activate_preferences.short_description = '激活选中的偏好设置'
    
    def deactivate_preferences(self, request, queryset):
        """批量停用偏好设置"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'成功停用 {count} 个偏好设置')
    deactivate_preferences.short_description = '停用选中的偏好设置'
    
    def enable_all_notifications(self, request, queryset):
        """启用所有通知"""
        count = queryset.update(
            email_notifications=True,
            push_notifications=True,
            sms_notifications=True
        )
        self.message_user(request, f'成功为 {count} 个用户启用所有通知')
    enable_all_notifications.short_description = '启用所有通知'
    
    def disable_all_notifications(self, request, queryset):
        """禁用所有通知"""
        count = queryset.update(
            email_notifications=False,
            push_notifications=False,
            sms_notifications=False
        )
        self.message_user(request, f'成功为 {count} 个用户禁用所有通知')
    disable_all_notifications.short_description = '禁用所有通知'
    
    def reset_to_defaults(self, request, queryset):
        """重置为默认设置"""
        count = 0
        for preference in queryset:
            preference.reset_to_defaults()
            count += 1
        self.message_user(request, f'成功重置 {count} 个偏好设置为默认值')
    reset_to_defaults.short_description = '重置为默认设置'
