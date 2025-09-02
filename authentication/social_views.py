"""
社交登录相关的API视图
包含Telegram等第三方登录的处理逻辑
"""

import hashlib
import hmac
import time
import logging
from urllib.parse import parse_qs, unquote

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from allauth.socialaccount.models import SocialAccount, SocialApp
from allauth.socialaccount.providers.telegram.provider import TelegramProvider
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import AuthToken
from .cookie_utils import SecureCookieManager
from .serializers import UserSerializer
from utils.decorators import log_api_call, handle_exceptions
from utils.response import BaseApiResponse

User = get_user_model()
logger = logging.getLogger('api')


class TelegramAuthView(APIView):
    """
    Telegram登录认证视图
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Social Authentication'],
        summary='Telegram登录认证',
        description="""
        通过Telegram进行用户认证登录
        
        ## 使用方法
        
        1. 前端集成Telegram Login Widget
        2. 用户授权后获取认证数据
        3. 将认证数据发送到此端点
        4. 系统验证并创建/登录用户
        
        ## 认证数据验证
        
        系统会验证Telegram返回的数据签名，确保数据未被篡改。
        """,
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'description': 'Telegram用户ID'},
                    'first_name': {'type': 'string', 'description': '用户名字'},
                    'last_name': {'type': 'string', 'description': '用户姓氏（可选）'},
                    'username': {'type': 'string', 'description': 'Telegram用户名（可选）'},
                    'photo_url': {'type': 'string', 'description': '头像URL（可选）'},
                    'auth_date': {'type': 'integer', 'description': '认证时间戳'},
                    'hash': {'type': 'string', 'description': 'Telegram签名哈希'},
                },
                'required': ['id', 'first_name', 'auth_date', 'hash']
            }
        },
        responses={
            200: {
                'description': 'Login successful',
                'content': {
                    'application/json': {
                        'type': 'object',
                        'properties': {
                            'success': {'type': 'boolean'},
                            'code': {'type': 'integer'},
                            'message': {'type': 'string'},
                            'data': {
                                'type': 'object',
                                'properties': {
                                    'message': {'type': 'string'},
                                    'user': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'integer'},
                                            'username': {'type': 'string'},
                                            'email': {'type': 'string'},
                                            'first_name': {'type': 'string'},
                                            'last_name': {'type': 'string'},
                                        }
                                    },
                                    'access_token': {'type': 'string'},
                                    'refresh_token': {'type': 'string'},
                                    'is_new_user': {'type': 'boolean'},
                                }
                            }
                        }
                    }
                }
            },
            400: 'Bad Request - 认证数据无效',
            401: 'Unauthorized - 认证失败'
        }
    )
    @method_decorator(csrf_exempt)
    @log_api_call
    @handle_exceptions
    def post(self, request):
        """
        处理Telegram登录认证
        """
        auth_data = request.data
        
        # 验证必需字段
        required_fields = ['id', 'first_name', 'auth_date', 'hash']
        for field in required_fields:
            if field not in auth_data:
                return BaseApiResponse.error(
                    message=f'缺少必需字段: {field}',
                    http_status=status.HTTP_400_BAD_REQUEST
                )
        
        # 验证Telegram数据
        if not self._verify_telegram_auth(auth_data):
            return BaseApiResponse.unauthorized(
                message='Telegram认证数据验证失败'
            )
        
        # 检查认证时间（防重放攻击）
        auth_date = int(auth_data['auth_date'])
        current_time = int(time.time())
        if current_time - auth_date > 300:  # 5分钟有效期
            return BaseApiResponse.unauthorized(
                message='认证数据已过期'
            )
        
        # 获取或创建用户
        telegram_id = str(auth_data['id'])
        user, is_new_user = self._get_or_create_user(auth_data)
        
        # 生成token对
        access_token, refresh_token = AuthToken.create_token_pair(
            user=user,
            device_info=self._get_client_ip(request)
        )
        
        # 设置安全cookie
        cookie_manager = SecureCookieManager()
        response_data = {
            'message': 'Telegram登录成功',
            'user': UserSerializer(user).data,
            'access_token': access_token.token,
            'refresh_token': refresh_token.token,
            'is_new_user': is_new_user,
        }
        
        response = BaseApiResponse.success(
            data=response_data,
            message='Telegram登录成功'
        )
        
        # 设置cookie
        cookie_manager.set_user_cookie(response, user)
        cookie_manager.set_token_cookie(response, access_token.token)
        
        logger.info(f"Telegram login successful for user: {user.username} (TG: {telegram_id})")
        
        return response
    
    def _verify_telegram_auth(self, auth_data):
        """
        验证Telegram认证数据的真实性
        """
        bot_token = settings.TELEGRAM_BOT_TOKEN
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not configured")
            return False
        
        # 移除hash字段，其他字段用于验证
        auth_hash = auth_data.pop('hash', None)
        if not auth_hash:
            return False
        
        # 构建验证字符串
        data_check_arr = []
        for key, value in sorted(auth_data.items()):
            if value is not None:
                data_check_arr.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_arr)
        
        # 使用bot token的SHA256作为密钥
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        
        # 计算HMAC-SHA256
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 恢复hash字段
        auth_data['hash'] = auth_hash
        
        return hmac.compare_digest(calculated_hash, auth_hash)
    
    def _get_or_create_user(self, auth_data):
        """
        根据Telegram数据获取或创建用户
        """
        telegram_id = str(auth_data['id'])
        
        # 首先尝试通过SocialAccount查找用户
        try:
            social_account = SocialAccount.objects.get(
                provider='telegram',
                uid=telegram_id
            )
            return social_account.user, False
        except SocialAccount.DoesNotExist:
            pass
        
        # 创建新用户
        first_name = auth_data.get('first_name', '')
        last_name = auth_data.get('last_name', '')
        username = auth_data.get('username')
        
        # 生成用户名
        if username:
            # 检查用户名是否已存在
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
        else:
            username = f"tg_{telegram_id}"
        
        # 创建用户
        user = User.objects.create_user(
            username=username,
            email=f"tg_{telegram_id}@telegram.local",
            first_name=first_name,
            last_name=last_name,
        )
        
        # 创建社交账户关联
        social_account = SocialAccount.objects.create(
            user=user,
            provider='telegram',
            uid=telegram_id,
            extra_data=auth_data
        )
        
        logger.info(f"Created new Telegram user: {username} (TG: {telegram_id})")
        
        return user, True
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TelegramCallbackView(APIView):
    """
    Telegram登录回调处理
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Social Authentication'],
        summary='Telegram登录回调',
        description='处理Telegram登录的回调，通常用于Web重定向场景',
        parameters=[
            OpenApiParameter(name='id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='first_name', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='last_name', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='username', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='auth_date', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='hash', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
        ]
    )
    def get(self, request):
        """
        处理Telegram回调（GET方式）
        """
        # 将查询参数转换为认证数据
        auth_data = dict(request.GET)
        
        # 处理单值参数
        for key, value in auth_data.items():
            if isinstance(value, list) and len(value) == 1:
                auth_data[key] = value[0]
        
        # 转换数值类型
        if 'id' in auth_data:
            auth_data['id'] = int(auth_data['id'])
        if 'auth_date' in auth_data:
            auth_data['auth_date'] = int(auth_data['auth_date'])
        
        # 使用POST方法的相同逻辑
        request.data = auth_data
        return TelegramAuthView().post(request)


class ConnectedAccountsView(APIView):
    """
    已连接的社交账户管理
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Social Authentication'],
        summary='获取已连接的社交账户',
        description='获取当前用户已连接的所有社交账户列表',
        responses={
            200: {
                'description': 'Success',
                'content': {
                    'application/json': {
                        'type': 'object',
                        'properties': {
                            'accounts': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'provider': {'type': 'string'},
                                        'uid': {'type': 'string'},
                                        'username': {'type': 'string'},
                                        'connected_at': {'type': 'string'},
                                        'extra_data': {'type': 'object'},
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    @log_api_call
    @handle_exceptions
    def get(self, request):
        """
        获取用户的社交账户连接列表
        """
        social_accounts = SocialAccount.objects.filter(user=request.user)
        
        accounts_data = []
        for account in social_accounts:
            account_info = {
                'provider': account.provider,
                'uid': account.uid,
                'username': account.extra_data.get('username', ''),
                'connected_at': account.date_joined.isoformat(),
                'extra_data': {
                    'first_name': account.extra_data.get('first_name', ''),
                    'last_name': account.extra_data.get('last_name', ''),
                }
            }
            
            # Telegram特殊处理
            if account.provider == 'telegram':
                account_info['display_name'] = (
                    f"{account.extra_data.get('first_name', '')} "
                    f"{account.extra_data.get('last_name', '')}".strip()
                )
                account_info['photo_url'] = account.extra_data.get('photo_url', '')
            
            accounts_data.append(account_info)
        
        return BaseApiResponse.success(
            data={'accounts': accounts_data},
            message=f'找到 {len(accounts_data)} 个已连接的社交账户'
        )


class DisconnectSocialView(APIView):
    """
    断开社交账户连接
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Social Authentication'],
        summary='断开社交账户连接',
        description='断开指定的社交账户连接',
        parameters=[
            OpenApiParameter(
                name='provider', 
                type=OpenApiTypes.STR, 
                location=OpenApiParameter.PATH,
                description='社交平台名称（如: telegram）'
            )
        ],
        responses={
            200: 'Success - 社交账户已断开',
            404: 'Not Found - 未找到指定的社交账户',
            400: 'Bad Request - 不能断开最后一个登录方式'
        }
    )
    @log_api_call
    @handle_exceptions
    def delete(self, request, provider):
        """
        断开指定的社交账户连接
        """
        try:
            social_account = SocialAccount.objects.get(
                user=request.user,
                provider=provider
            )
        except SocialAccount.DoesNotExist:
            return BaseApiResponse.not_found(
                message=f'未找到 {provider} 社交账户'
            )
        
        # 检查是否是唯一的登录方式
        user_social_accounts = SocialAccount.objects.filter(user=request.user)
        has_password = request.user.has_usable_password()
        
        if user_social_accounts.count() == 1 and not has_password:
            return BaseApiResponse.error(
                message='不能断开最后一个登录方式，请先设置密码',
                http_status=status.HTTP_400_BAD_REQUEST
            )
        
        # 删除社交账户连接
        provider_display = social_account.get_provider().name
        social_account.delete()
        
        logger.info(f"User {request.user.username} disconnected {provider} account")
        
        return BaseApiResponse.success(
            message=f'{provider_display} 账户连接已断开'
        )


class SocialAuthCheckView(APIView):
    """
    社交登录状态检查
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Social Authentication'],
        summary='社交登录状态检查',
        description='检查社交登录的可用性和配置状态',
        responses={
            200: {
                'description': 'Success',
                'content': {
                    'application/json': {
                        'type': 'object',
                        'properties': {
                            'providers': {
                                'type': 'object',
                                'properties': {
                                    'telegram': {
                                        'type': 'object',
                                        'properties': {
                                            'enabled': {'type': 'boolean'},
                                            'configured': {'type': 'boolean'},
                                            'bot_name': {'type': 'string'},
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    @log_api_call
    def get(self, request):
        """
        检查社交登录提供商的状态
        """
        providers_status = {
            'telegram': {
                'enabled': True,
                'configured': bool(settings.TELEGRAM_BOT_TOKEN),
                'bot_name': settings.TELEGRAM_BOT_NAME,
            }
        }
        
        return BaseApiResponse.success(
            data={'providers': providers_status},
            message='社交登录状态检查完成'
        )
