from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from allauth.account.models import EmailAddress
from .models import User, Role, LoginHistory, AuthToken


class RoleAdmin(admin.ModelAdmin):
    """角色管理"""
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {'fields': ('name', 'code', 'description')}),
        (_('权限'), {'fields': ('permissions',)}),
        (_('状态'), {'fields': ('is_active',)}),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


class LoginHistoryInline(admin.TabularInline):
    """登录历史内联管理"""
    model = LoginHistory
    extra = 0
    readonly_fields = ['ip_address', 'user_agent', 'login_method', 'is_successful', 'failure_reason', 'login_time']
    can_delete = False
    verbose_name_plural = '登录历史'


class SocialAccountInline(admin.TabularInline):
    """社交账户内联管理"""
    model = SocialAccount
    extra = 0
    readonly_fields = ['provider', 'uid', 'get_display_name_inline', 'date_joined']
    can_delete = True
    verbose_name_plural = '关联的社交账户'
    
    def get_display_name_inline(self, obj):
        """内联显示名称"""
        extra_data = obj.extra_data or {}
        if obj.provider == 'telegram':
            first_name = extra_data.get('first_name', '')
            username = extra_data.get('username', '')
            if first_name:
                return f"{first_name} (@{username})" if username else first_name
            elif username:
                return f"@{username}"
        return extra_data.get('name', obj.uid)
    
    get_display_name_inline.short_description = "显示名称"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理"""
    inlines = [LoginHistoryInline, SocialAccountInline]
    
    list_display = [
        'username', 'email', 'nickname', 'phone', 'is_active', 
        'is_verified', 'is_staff', 'date_joined', 'last_login'
    ]
    list_filter = [
        'is_active', 'is_verified', 'is_staff', 'is_superuser', 
        'date_joined', 'last_login', 'roles'
    ]
    search_fields = ['username', 'email', 'nickname', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {
            'fields': (
                'email', 'nickname', 'phone', 'avatar',
                'first_name', 'last_name'
            )
        }),
        (_('角色和权限'), {
            'fields': (
                'roles', 'is_active', 'is_verified', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'nickname', 'phone'
            ),
        }),
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """登录历史管理"""
    list_display = ['user', 'ip_address', 'login_method', 'is_successful', 'login_time']
    list_filter = ['login_method', 'is_successful', 'login_time']
    search_fields = ['user__username', 'user__email', 'ip_address']
    ordering = ['-login_time']
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('登录信息'), {
            'fields': ('ip_address', 'user_agent', 'login_method')
        }),
        (_('登录结果'), {
            'fields': ('is_successful', 'failure_reason')
        }),
        (_('时间信息'), {
            'fields': ('login_time',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['login_time']


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    """认证Token管理"""
    list_display = ['user', 'token_preview', 'token_type', 'is_active', 'is_valid_status', 'expires_at', 'created_at']
    list_filter = ['token_type', 'is_active', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'token']
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        (None, {'fields': ('user', 'token_type')}),
        (_('Token信息'), {
            'fields': ('token', 'device_info', 'expires_at', 'is_active')
        }),
        (_('使用信息'), {
            'fields': ('last_used_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['token', 'created_at']
    
    def token_preview(self, obj):
        """Token预览"""
        return f"{obj.token[:8]}***"
    token_preview.short_description = "Token预览"
    
    def is_valid_status(self, obj):
        """Token是否有效"""
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ 有效</span>')
        else:
            return format_html('<span style="color: red;">✗ 无效</span>')
    is_valid_status.short_description = "状态"
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('user')
    
    actions = ['revoke_tokens', 'cleanup_expired']
    
    def revoke_tokens(self, request, queryset):
        """批量撤销token"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'成功撤销 {updated} 个token')
    revoke_tokens.short_description = "撤销选中的token"
    
    def cleanup_expired(self, request, queryset):
        """清理过期token"""
        expired_tokens = queryset.filter(expires_at__lt=timezone.now())
        count = expired_tokens.count()
        expired_tokens.delete()
        self.message_user(request, f'成功清理 {count} 个过期token')
    cleanup_expired.short_description = "清理过期token"


# 注册角色模型
admin.site.register(Role, RoleAdmin)


# ===============================
# Django Allauth 社交登录管理
# ===============================

# 取消注册allauth的默认admin，使用我们的自定义admin
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)
admin.site.unregister(EmailAddress)

@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    """社交账户管理"""
    list_display = ['user', 'provider', 'uid', 'get_display_name', 'date_joined']
    list_filter = ['provider', 'date_joined']
    search_fields = ['user__username', 'user__email', 'uid', 'extra_data']
    ordering = ['-date_joined']
    readonly_fields = ['uid', 'date_joined']
    
    fieldsets = (
        (None, {'fields': ('user', 'provider', 'uid')}),
        (_('社交账户信息'), {
            'fields': ('extra_data',),
            'classes': ('collapse',)
        }),
        (_('时间信息'), {
            'fields': ('date_joined',),
            'classes': ('collapse',)
        }),
    )
    
    def get_display_name(self, obj):
        """获取显示名称"""
        extra_data = obj.extra_data or {}
        if obj.provider == 'telegram':
            first_name = extra_data.get('first_name', '')
            last_name = extra_data.get('last_name', '')
            username = extra_data.get('username', '')
            
            if first_name or last_name:
                display_name = f"{first_name} {last_name}".strip()
                if username:
                    display_name += f" (@{username})"
                return display_name
            elif username:
                return f"@{username}"
            else:
                return f"TG:{obj.uid}"
        
        return extra_data.get('name', obj.uid)
    
    get_display_name.short_description = "显示名称"
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('user')


@admin.register(SocialApp)
class SocialAppAdmin(admin.ModelAdmin):
    """社交应用管理"""
    list_display = ['name', 'provider', 'client_id_preview', 'is_configured']
    list_filter = ['provider']
    search_fields = ['name', 'provider', 'client_id']
    
    fieldsets = (
        (None, {'fields': ('provider', 'name')}),
        (_('应用配置'), {
            'fields': ('client_id', 'secret', 'settings'),
            'description': 'Telegram Bot的配置信息'
        }),
        (_('关联站点'), {
            'fields': ('sites',),
            'classes': ('collapse',)
        }),
    )
    
    def client_id_preview(self, obj):
        """客户端ID预览"""
        if obj.client_id:
            return f"{obj.client_id[:10]}..."
        return "未配置"
    client_id_preview.short_description = "客户端ID"
    
    def is_configured(self, obj):
        """是否已配置"""
        if obj.client_id and obj.secret:
            return format_html('<span style="color: green;">✓ 已配置</span>')
        else:
            return format_html('<span style="color: red;">✗ 未配置</span>')
    is_configured.short_description = "配置状态"


@admin.register(SocialToken)
class SocialTokenAdmin(admin.ModelAdmin):
    """社交Token管理"""
    list_display = ['account', 'app', 'token_preview', 'expires_at']
    list_filter = ['app__provider', 'expires_at']
    search_fields = ['account__user__username', 'account__uid', 'token']
    ordering = ['-id']
    readonly_fields = ['token', 'token_secret']
    
    fieldsets = (
        (None, {'fields': ('account', 'app')}),
        (_('Token信息'), {
            'fields': ('token', 'token_secret', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def token_preview(self, obj):
        """Token预览"""
        if obj.token:
            return f"{obj.token[:12]}..."
        return "无"
    token_preview.short_description = "Token预览"
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('account__user', 'app')


@admin.register(EmailAddress)
class EmailAddressAdmin(admin.ModelAdmin):
    """邮箱地址管理"""
    list_display = ['email', 'user', 'verified', 'primary']
    list_filter = ['verified', 'primary']
    search_fields = ['email', 'user__username']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('user', 'email')}),
        (_('状态'), {'fields': ('verified', 'primary')}),
    )
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('user')


# 自定义管理界面标题
admin.site.site_header = "Loud 认证管理系统"
admin.site.site_title = "认证管理"
admin.site.index_title = "欢迎使用认证管理系统 - 支持社交登录"
