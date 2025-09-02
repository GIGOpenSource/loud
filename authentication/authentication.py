"""
自定义认证后端
支持短token和cookie认证
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import AuthToken
from .cookie_utils import cookie_manager

User = get_user_model()


class ShortTokenBackend(BaseBackend):
    """32位短token认证后端"""
    
    def authenticate(self, request, token=None):
        """使用短token认证用户"""
        if not token:
            return None
        
        try:
            auth_token = AuthToken.objects.select_related('user').get(
                token=token,
                token_type='access'
            )
            
            if not auth_token.is_valid():
                return None
            
            # 更新最后使用时间
            auth_token.last_used_at = timezone.now()
            auth_token.save(update_fields=['last_used_at'])
            
            return auth_token.user
        except AuthToken.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        """根据用户ID获取用户"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class CookieTokenAuthentication(BaseAuthentication):
    """
    基于Cookie的Token认证
    优先从Header获取token，如果没有则从Cookie获取
    """
    
    def authenticate(self, request):
        """认证请求"""
        # 1. 首先尝试从Header获取token
        token = self.get_token_from_header(request)
        
        # 2. 如果Header没有token，尝试从Cookie获取
        if not token:
            token = cookie_manager.get_token_from_cookie(request)
        
        if not token:
            return None
        
        # 3. 验证token
        user = self.authenticate_token(token)
        if not user:
            return None
        
        return (user, token)
    
    def get_token_from_header(self, request):
        """从请求头获取token"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        try:
            auth_type, token = auth_header.split(' ', 1)
            if auth_type.lower() != 'bearer':
                return None
            return token
        except ValueError:
            return None
    
    def authenticate_token(self, token):
        """验证token并返回用户"""
        try:
            auth_token = AuthToken.objects.select_related('user').get(
                token=token,
                token_type='access'
            )
            
            if not auth_token.is_valid():
                raise AuthenticationFailed(_('Token已过期或无效'))
            
            # 更新最后使用时间
            auth_token.last_used_at = timezone.now()
            auth_token.save(update_fields=['last_used_at'])
            
            return auth_token.user
        except AuthToken.DoesNotExist:
            raise AuthenticationFailed(_('无效的token'))


class CookieUserAuthentication(BaseAuthentication):
    """
    基于Cookie的用户信息认证
    直接从Cookie获取用户信息，避免数据库查询
    """
    
    def authenticate(self, request):
        """认证请求"""
        # 获取cookie中的用户信息
        user_data = cookie_manager.get_user_from_cookie(request)
        if not user_data:
            return None
        
        # 创建一个轻量级的用户对象
        user = self.create_user_from_cookie(user_data)
        if not user:
            return None
        
        return (user, 'cookie')
    
    def create_user_from_cookie(self, user_data):
        """从cookie数据创建用户对象"""
        try:
            # 创建一个模拟的用户对象，包含必要的属性
            class CookieUser:
                def __init__(self, data):
                    self.id = data.get('id')
                    self.username = data.get('username')
                    self.email = data.get('email')
                    self.nickname = data.get('nickname', '')
                    self.display_name = data.get('display_name')
                    self.is_active = data.get('is_active', True)
                    self.is_verified = data.get('is_verified', False)
                    self.roles = data.get('roles', [])
                    self.permissions = data.get('permissions', [])
                    self.last_login_str = data.get('last_login')
                    self.is_authenticated = True
                    self.is_anonymous = False
                    self._from_cookie = True  # 标记这是从cookie来的用户
                
                def has_role(self, role_code):
                    """检查是否有指定角色"""
                    return role_code in self.roles
                
                def has_permission(self, permission_code):
                    """检查是否有指定权限"""
                    return permission_code in self.permissions
                
                def has_any_role(self, role_codes):
                    """检查是否有任意指定角色"""
                    return any(role in self.roles for role in role_codes)
                
                def get_real_user(self):
                    """获取真实的用户对象（当需要完整数据时）"""
                    try:
                        return User.objects.get(id=self.id)
                    except User.DoesNotExist:
                        return None
                
                def __str__(self):
                    return self.username
            
            return CookieUser(user_data)
        except Exception:
            return None


class HybridAuthentication(BaseAuthentication):
    """
    混合认证：优先使用cookie，fallback到token
    """
    
    def __init__(self):
        self.cookie_auth = CookieUserAuthentication()
        self.token_auth = CookieTokenAuthentication()
    
    def authenticate(self, request):
        """混合认证"""
        # 1. 优先尝试cookie认证（快速，无数据库查询）
        result = self.cookie_auth.authenticate(request)
        if result:
            return result
        
        # 2. 如果cookie认证失败，尝试token认证
        return self.token_auth.authenticate(request)
