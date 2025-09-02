"""
用户资料管理后台
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料管理"""
    
    list_display = [
        'user_link', 'nickname', 'gender', 'city', 'country',
        'profile_visibility', 'avatar_preview', 'is_active', 'updated_at'
    ]
    
    list_filter = [
        'gender', 'profile_visibility', 'country', 'province', 'city',
        'is_active', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'nickname', 'bio',
        'city', 'country', 'website'
    ]
    
    readonly_fields = [
        'user', 'created_by', 'updated_by', 'created_at', 'updated_at',
        'avatar_preview', 'display_name', 'age', 'full_address'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'nickname', 'bio', 'display_name')
        }),
        ('个人资料', {
            'fields': ('avatar', 'avatar_preview', 'birth_date', 'age', 'gender')
        }),
        ('地址信息', {
            'fields': ('country', 'province', 'city', 'address', 'full_address'),
            'classes': ('collapse',)
        }),
        ('联系方式', {
            'fields': ('website', 'twitter', 'github'),
            'classes': ('collapse',)
        }),
        ('隐私设置', {
            'fields': ('profile_visibility', 'show_email', 'show_phone')
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
    
    def avatar_preview(self, obj):
        """头像预览"""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%;" />',
                obj.avatar.url
            )
        return mark_safe('<span style="color: #ccc;">无头像</span>')
    avatar_preview.short_description = '头像预览'
    
    def display_name(self, obj):
        """显示名称"""
        return obj.display_name
    display_name.short_description = '显示名称'
    
    def age(self, obj):
        """年龄"""
        return f"{obj.age}岁" if obj.age else "未设置"
    age.short_description = '年龄'
    
    def full_address(self, obj):
        """完整地址"""
        return obj.full_address or "未设置"
    full_address.short_description = '完整地址'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related(
            'user', 'created_by', 'updated_by'
        )
    
    actions = ['activate_profiles', 'deactivate_profiles', 'set_public', 'set_private']
    
    def activate_profiles(self, request, queryset):
        """批量激活资料"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'成功激活 {count} 个用户资料')
    activate_profiles.short_description = '激活选中的资料'
    
    def deactivate_profiles(self, request, queryset):
        """批量停用资料"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'成功停用 {count} 个用户资料')
    deactivate_profiles.short_description = '停用选中的资料'
    
    def set_public(self, request, queryset):
        """设置为公开"""
        count = queryset.update(profile_visibility='public')
        self.message_user(request, f'成功设置 {count} 个资料为公开')
    set_public.short_description = '设置为公开资料'
    
    def set_private(self, request, queryset):
        """设置为私密"""
        count = queryset.update(profile_visibility='private')
        self.message_user(request, f'成功设置 {count} 个资料为私密')
    set_private.short_description = '设置为私密资料'
