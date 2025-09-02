"""
用户偏好模型
使用base基础类重构
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import json

from base.models import BaseAuditModel


class UserPreference(BaseAuditModel):
    """
    用户偏好设置模型
    继承BaseAuditModel获得审计功能
    """
    
    user = models.OneToOneField(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name=_('用户')
    )
    
    # 界面设置
    THEME_CHOICES = [
        ('light', _('浅色主题')),
        ('dark', _('深色主题')),
        ('auto', _('跟随系统')),
    ]
    
    LANGUAGE_CHOICES = [
        ('zh-hans', _('简体中文')),
        ('zh-hant', _('繁体中文')),
        ('en', _('English')),
        ('ja', _('日本語')),
        ('ko', _('한국어')),
    ]
    
    theme = models.CharField(
        _('主题'),
        max_length=20,
        choices=THEME_CHOICES,
        default='light',
        help_text=_('界面主题设置')
    )
    
    language = models.CharField(
        _('语言'),
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='zh-hans',
        help_text=_('界面语言设置')
    )
    
    timezone = models.CharField(
        _('时区'),
        max_length=50,
        default='Asia/Shanghai',
        help_text=_('用户所在时区')
    )
    
    # 通知设置
    email_notifications = models.BooleanField(
        _('邮件通知'),
        default=True,
        help_text=_('是否接收邮件通知')
    )
    
    push_notifications = models.BooleanField(
        _('推送通知'),
        default=True,
        help_text=_('是否接收推送通知')
    )
    
    sms_notifications = models.BooleanField(
        _('短信通知'),
        default=False,
        help_text=_('是否接收短信通知')
    )
    
    # 通知类型设置
    notification_types = models.JSONField(
        _('通知类型设置'),
        default=dict,
        blank=True,
        help_text=_('各种通知类型的开关设置')
    )
    
    # 隐私设置
    show_online_status = models.BooleanField(
        _('显示在线状态'),
        default=True,
        help_text=_('是否向其他用户显示在线状态')
    )
    
    allow_friend_requests = models.BooleanField(
        _('允许好友请求'),
        default=True,
        help_text=_('是否允许其他用户发送好友请求')
    )
    
    allow_messages_from_strangers = models.BooleanField(
        _('允许陌生人消息'),
        default=False,
        help_text=_('是否允许非好友用户发送消息')
    )
    
    # 功能设置
    auto_save_drafts = models.BooleanField(
        _('自动保存草稿'),
        default=True,
        help_text=_('是否自动保存编辑中的内容')
    )
    
    enable_keyboard_shortcuts = models.BooleanField(
        _('启用键盘快捷键'),
        default=True,
        help_text=_('是否启用键盘快捷键')
    )
    
    items_per_page = models.PositiveIntegerField(
        _('每页显示条数'),
        default=20,
        help_text=_('列表页面每页显示的项目数量')
    )
    
    # 自定义设置
    custom_settings = models.JSONField(
        _('自定义设置'),
        default=dict,
        blank=True,
        help_text=_('用户自定义的其他设置')
    )
    
    class Meta:
        verbose_name = _('用户偏好')
        verbose_name_plural = _('用户偏好')
        db_table = 'user_preferences'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f'{self.user.username} 的偏好设置'
    
    def clean(self):
        """模型验证"""
        super().clean()
        
        # 验证每页显示条数范围
        if self.items_per_page < 5 or self.items_per_page > 100:
            raise ValidationError({'items_per_page': '每页显示条数必须在5-100之间'})
    
    @property
    def default_notification_types(self):
        """获取默认通知类型设置"""
        return {
            'system_updates': True,          # 系统更新
            'security_alerts': True,        # 安全警告
            'account_changes': True,        # 账户变更
            'friend_requests': True,        # 好友请求
            'messages': True,               # 消息通知
            'mentions': True,               # 提及通知
            'likes': False,                 # 点赞通知
            'comments': True,               # 评论通知
            'marketing': False,             # 营销推广
            'newsletters': False,           # 新闻简报
        }
    
    def get_notification_setting(self, notification_type):
        """获取特定通知类型的设置"""
        default_settings = self.default_notification_types
        current_settings = self.notification_types or {}
        
        # 如果没有设置，使用默认值
        return current_settings.get(notification_type, default_settings.get(notification_type, False))
    
    def set_notification_setting(self, notification_type, enabled):
        """设置特定通知类型"""
        if not self.notification_types:
            self.notification_types = {}
        
        self.notification_types[notification_type] = enabled
        self.save(update_fields=['notification_types', 'updated_at'])
    
    def get_custom_setting(self, key, default=None):
        """获取自定义设置"""
        if not self.custom_settings:
            return default
        return self.custom_settings.get(key, default)
    
    def set_custom_setting(self, key, value):
        """设置自定义设置"""
        if not self.custom_settings:
            self.custom_settings = {}
        
        self.custom_settings[key] = value
        self.save(update_fields=['custom_settings', 'updated_at'])
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        self.theme = 'light'
        self.language = 'zh-hans'
        self.timezone = 'Asia/Shanghai'
        self.email_notifications = True
        self.push_notifications = True
        self.sms_notifications = False
        self.notification_types = self.default_notification_types
        self.show_online_status = True
        self.allow_friend_requests = True
        self.allow_messages_from_strangers = False
        self.auto_save_drafts = True
        self.enable_keyboard_shortcuts = True
        self.items_per_page = 20
        self.custom_settings = {}
        
        self.save()
    
    def export_settings(self):
        """导出设置为JSON"""
        return {
            'theme': self.theme,
            'language': self.language,
            'timezone': self.timezone,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'sms_notifications': self.sms_notifications,
            'notification_types': self.notification_types,
            'show_online_status': self.show_online_status,
            'allow_friend_requests': self.allow_friend_requests,
            'allow_messages_from_strangers': self.allow_messages_from_strangers,
            'auto_save_drafts': self.auto_save_drafts,
            'enable_keyboard_shortcuts': self.enable_keyboard_shortcuts,
            'items_per_page': self.items_per_page,
            'custom_settings': self.custom_settings,
        }
    
    def import_settings(self, settings_data):
        """从JSON导入设置"""
        for key, value in settings_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.save()
    
    def get_effective_timezone(self):
        """获取有效时区"""
        import pytz
        try:
            return pytz.timezone(self.timezone)
        except pytz.UnknownTimeZoneError:
            return pytz.timezone('Asia/Shanghai')  # 默认时区
