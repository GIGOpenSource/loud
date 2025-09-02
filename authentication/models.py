from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, Group, Permission
import secrets
import string
from datetime import timedelta
from django.utils import timezone


class Role(models.Model):
    """
    角色模型
    用于定义用户的角色和权限
    """
    name = models.CharField(_('角色名称'), max_length=50, unique=True, help_text=_('角色名称'))
    code = models.CharField(_('角色代码'), max_length=50, unique=True, help_text=_('角色代码，用于程序识别'))
    description = models.TextField(_('角色描述'), blank=True, help_text=_('角色描述'))
    
    # 权限相关
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('权限'),
        blank=True,
        help_text=_('该角色拥有的权限')
    )
    
    # 状态信息
    is_active = models.BooleanField(_('是否激活'), default=True, help_text=_('角色是否激活'))
    
    # 时间信息
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('角色')
        verbose_name_plural = _('角色')
        db_table = 'auth_roles'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_permissions_display(self):
        """获取权限显示名称"""
        return [perm.name for perm in self.permissions.all()]


class User(AbstractUser):
    """
    自定义用户模型
    扩展Django默认用户模型，添加角色支持
    """
    # 基本信息
    nickname = models.CharField(_('昵称'), max_length=50, blank=True, help_text=_('用户昵称'))
    avatar = models.ImageField(_('头像'), upload_to='avatars/', blank=True, null=True, help_text=_('用户头像'))
    phone = models.CharField(_('手机号'), max_length=11, blank=True, help_text=_('手机号码'))
    
    # 角色信息
    roles = models.ManyToManyField(
        Role,
        verbose_name=_('角色'),
        blank=True,
        help_text=_('用户拥有的角色')
    )
    
    # 状态信息
    is_active = models.BooleanField(_('是否激活'), default=True, help_text=_('用户是否激活'))
    is_verified = models.BooleanField(_('是否验证'), default=False, help_text=_('用户是否已验证'))
    
    # 时间信息
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    last_login_at = models.DateTimeField(_('最后登录时间'), null=True, blank=True)
    
    # 设置字段
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        db_table = 'auth_users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.username
    
    @property
    def display_name(self):
        """显示名称，优先使用昵称，否则使用用户名"""
        return self.nickname or self.username
    
    def get_full_name(self):
        """获取全名"""
        if self.first_name and self.last_name:
            return f"{self.last_name}{self.first_name}"
        return self.display_name
    
    def get_short_name(self):
        """获取短名称"""
        return self.display_name
    
    def has_role(self, role_code):
        """检查用户是否拥有指定角色"""
        return self.roles.filter(code=role_code, is_active=True).exists()
    
    def has_any_role(self, role_codes):
        """检查用户是否拥有任意一个指定角色"""
        return self.roles.filter(code__in=role_codes, is_active=True).exists()
    
    def get_all_permissions(self):
        """获取用户所有权限（包括角色权限和个人权限）"""
        permissions = set()
        
        # 获取角色权限
        for role in self.roles.filter(is_active=True):
            permissions.update(role.permissions.all())
        
        # 获取个人权限
        permissions.update(self.user_permissions.all())
        
        # 获取组权限
        for group in self.groups.all():
            permissions.update(group.permissions.all())
        
        return permissions
    
    def has_permission(self, permission_codename):
        """检查用户是否拥有指定权限"""
        all_permissions = self.get_all_permissions()
        return any(perm.codename == permission_codename for perm in all_permissions)


class LoginHistory(models.Model):
    """
    登录历史记录
    记录用户的登录信息
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history',
        verbose_name=_('用户')
    )
    
    # 登录信息
    ip_address = models.GenericIPAddressField(_('IP地址'), null=True, blank=True)
    user_agent = models.TextField(_('用户代理'), blank=True)
    login_method = models.CharField(_('登录方式'), max_length=20, choices=[
        ('password', _('密码登录')),
        ('token', _('Token登录')),
        ('oauth', _('OAuth登录')),
    ], default='password')
    
    # 登录结果
    is_successful = models.BooleanField(_('是否成功'), default=True)
    failure_reason = models.CharField(_('失败原因'), max_length=200, blank=True)
    
    # 时间信息
    login_time = models.DateTimeField(_('登录时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('登录历史')
        verbose_name_plural = _('登录历史')
        db_table = 'auth_login_history'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"


class AuthToken(models.Model):
    """
    32位短认证Token模型
    用于替代长JWT token
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='auth_tokens',
        verbose_name=_('用户')
    )
    
    # Token信息
    token = models.CharField(_('Token'), max_length=32, unique=True, db_index=True)
    
    # Token类型
    TOKEN_TYPE_CHOICES = [
        ('access', _('访问令牌')),
        ('refresh', _('刷新令牌')),
    ]
    token_type = models.CharField(
        _('Token类型'), 
        max_length=10, 
        choices=TOKEN_TYPE_CHOICES,
        default='access'
    )
    
    # 设备信息
    device_info = models.JSONField(_('设备信息'), default=dict, blank=True)
    
    # 过期时间
    expires_at = models.DateTimeField(_('过期时间'))
    
    # 状态信息
    is_active = models.BooleanField(_('是否激活'), default=True)
    last_used_at = models.DateTimeField(_('最后使用时间'), null=True, blank=True)
    
    # 时间信息
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('认证Token')
        verbose_name_plural = _('认证Token')
        db_table = 'auth_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'token_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.token[:8]}***"
    
    @classmethod
    def generate_token(cls):
        """生成32位随机token"""
        # 使用数字和字母组合，避免混淆字符
        alphabet = string.ascii_letters + string.digits
        # 移除容易混淆的字符
        alphabet = alphabet.replace('0', '').replace('O', '').replace('l', '').replace('I', '')
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    @classmethod
    def create_token_pair(cls, user, device_info=None):
        """为用户创建access和refresh token对"""
        now = timezone.now()
        
        # 创建access token (1小时过期)
        access_token = cls.objects.create(
            user=user,
            token=cls.generate_token(),
            token_type='access',
            device_info=device_info or {},
            expires_at=now + timedelta(hours=1)
        )
        
        # 创建refresh token (7天过期)
        refresh_token = cls.objects.create(
            user=user,
            token=cls.generate_token(),
            token_type='refresh',
            device_info=device_info or {},
            expires_at=now + timedelta(days=7)
        )
        
        return access_token, refresh_token
    
    def is_valid(self):
        """检查token是否有效"""
        return (
            self.is_active and 
            self.expires_at > timezone.now() and
            self.user.is_active
        )
    
    def refresh(self):
        """刷新token（延长过期时间）"""
        if self.token_type == 'access':
            self.expires_at = timezone.now() + timedelta(hours=1)
        elif self.token_type == 'refresh':
            self.expires_at = timezone.now() + timedelta(days=7)
        
        self.last_used_at = timezone.now()
        self.save(update_fields=['expires_at', 'last_used_at'])
    
    def revoke(self):
        """撤销token"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    @classmethod
    def cleanup_expired(cls):
        """清理过期的token"""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        return expired_count
