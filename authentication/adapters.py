"""
Django Allauth 自定义适配器
处理社交登录和账户管理的自定义逻辑
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import AuthToken
from .cookie_utils import SecureCookieManager
import logging

User = get_user_model()
logger = logging.getLogger('api')


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    自定义社交账户适配器
    处理Telegram等第三方登录的逻辑
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        社交登录前的处理
        检查用户是否已存在，处理账户关联
        """
        user = sociallogin.user
        
        # 如果是新用户，设置一些默认值
        if not user.pk:
            # 从社交账户获取用户信息
            extra_data = sociallogin.account.extra_data
            
            # Telegram特殊处理
            if sociallogin.account.provider == 'telegram':
                self._handle_telegram_user(user, extra_data)
        
        # 检查是否有相同邮箱的已存在用户
        if user.email:
            try:
                existing_user = User.objects.get(email=user.email)
                if not existing_user.pk == user.pk:
                    # 关联现有用户到社交账户
                    sociallogin.user = existing_user
                    logger.info(f"Social login linked to existing user: {existing_user.username}")
            except User.DoesNotExist:
                pass
    
    def _handle_telegram_user(self, user, extra_data):
        """
        处理Telegram用户数据
        """
        # 从Telegram数据中提取用户信息
        telegram_id = extra_data.get('id')
        first_name = extra_data.get('first_name', '')
        last_name = extra_data.get('last_name', '')
        username = extra_data.get('username')
        
        # 设置用户名（优先使用Telegram username）
        if username:
            # 检查用户名是否已存在
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            user.username = username
        else:
            # 如果没有username，使用telegram_id生成
            user.username = f"tg_{telegram_id}"
        
        # 设置姓名
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        
        # 设置邮箱（Telegram通常不提供邮箱）
        if not user.email:
            user.email = f"tg_{telegram_id}@telegram.local"
        
        logger.info(f"Prepared Telegram user: {user.username} (TG: {telegram_id})")
    
    def save_user(self, request, sociallogin, form=None):
        """
        保存社交登录用户
        """
        user = super().save_user(request, sociallogin, form)
        
        # 记录社交登录
        logger.info(f"Social user saved: {user.username} via {sociallogin.account.provider}")
        
        return user
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        处理认证错误
        在API模式下返回JSON错误
        """
        if getattr(settings, 'ALLAUTH_API_ONLY', False):
            error_data = {
                'error': 'social_auth_failed',
                'message': f'社交登录失败: {provider_id}',
                'provider': provider_id
            }
            if error:
                error_data['details'] = str(error)
            
            response = JsonResponse(error_data, status=400)
            raise ImmediateHttpResponse(response)
        
        return super().authentication_error(request, provider_id, error, exception, extra_context)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    自定义账户适配器
    处理普通账户注册和登录的自定义逻辑
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        保存用户时的自定义逻辑
        """
        user = super().save_user(request, user, form, commit=False)
        
        # 在这里可以添加额外的用户字段处理
        # 例如：设置默认头像、创建用户配置等
        
        if commit:
            user.save()
        
        return user
    
    def respond_user_authenticated(self, request, user):
        """
        用户认证成功后的响应处理
        在API模式下返回JSON响应而不是重定向
        """
        if getattr(settings, 'ALLAUTH_API_ONLY', False):
            # 生成我们的自定义token
            from .views import LoginView
            
            login_view = LoginView()
            login_view.request = request
            
            # 生成token对
            access_token, refresh_token = AuthToken.create_token_pair(
                user=user,
                device_info=login_view.get_client_ip()
            )
            
            # 设置cookie
            cookie_manager = SecureCookieManager()
            response_data = {
                'message': '社交登录成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'access_token': access_token.token,
                'refresh_token': refresh_token.token,
            }
            
            response = JsonResponse(response_data)
            
            # 设置安全cookie
            cookie_manager.set_user_cookie(response, user)
            cookie_manager.set_token_cookie(response, access_token.token)
            
            logger.info(f"Social login successful for user: {user.username}")
            
            raise ImmediateHttpResponse(response)
        
        return super().respond_user_authenticated(request, user)
