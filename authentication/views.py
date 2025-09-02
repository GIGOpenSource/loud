from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import User, LoginHistory, AuthToken
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    LoginSerializer, PasswordChangeSerializer, PasswordResetSerializer,
    PasswordResetConfirmSerializer, LoginHistorySerializer,
    ShortTokenSerializer
)
from .responses import AuthApiResponse, AuthBusinessResponse
from .exceptions import (
    UserNotFoundException, UserAlreadyExistsException, InvalidCredentialsException,
    TokenExpiredException
)
from .cookie_utils import cookie_manager
from .authentication import ShortTokenBackend

from utils.decorators import api_response, handle_exceptions, validate_request_data, log_api_call
from utils.response import BaseApiResponse


@extend_schema(
    tags=['Authentication'],
    summary='用户注册',
    description='注册新用户账户，支持用户名、邮箱和密码注册',
    request=UserCreateSerializer,
    responses={
        201: UserSerializer,
        400: 'Bad Request - 参数错误或用户已存在'
    }
)
class RegisterView(APIView):
    """用户注册视图"""
    permission_classes = [permissions.AllowAny]
    
    @log_api_call
    @handle_exceptions
    @validate_request_data(required_fields=['username', 'email', 'password'])
    @api_response(success_message="注册成功")
    @transaction.atomic
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            raise InvalidCredentialsException(serializer.errors)
        
        user = serializer.save()
        
        # 生成32位短token (不使用session登录，避免在API环境中产生冲突)
        device_info = {
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'platform': 'web'
        }
        
        access_token, refresh_token = AuthToken.create_token_pair(user, device_info)
        
        response_data = {
            'user': UserSerializer(user).data,
            'tokens': {
                'access': access_token.token,
                'refresh': refresh_token.token,
            }
        }
        
        # 创建响应
        response = BaseApiResponse.success(
            data=response_data,
            message="注册成功，欢迎加入！"
        )
        
        # 设置安全cookie
        remember_me = request.data.get('remember_me', False)
        max_age = 60 * 60 * 24 * 30 if remember_me else 60 * 60 * 24 * 7  # 30天或7天
        
        cookie_manager.set_user_cookie(response, user, max_age)
        cookie_manager.set_token_cookie(response, access_token.token, max_age)
        
        return response
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@extend_schema(
    tags=['Authentication'],
    summary='用户登录',
    description='用户登录，成功后返回token并设置cookie认证',
    request=LoginSerializer,
    responses={
        200: 'Login successful - 返回用户信息和token',
        401: 'Unauthorized - 用户名或密码错误'
    }
)
class LoginView(APIView):
    """用户登录视图"""
    permission_classes = [permissions.AllowAny]
    
    @log_api_call
    @handle_exceptions
    @validate_request_data(required_fields=['username', 'password'])
    @api_response(success_message="登录成功")
    @transaction.atomic
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            raise InvalidCredentialsException(serializer.errors)
        
        user = serializer.validated_data['user']
        remember_me = serializer.validated_data.get('remember_me', False)
        
        # 更新最后登录时间
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])
        
        # 生成32位短token
        device_info = {
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'platform': 'web',
            'remember_me': remember_me
        }
        
        # 清理用户的旧token（可选，保持活跃会话数量）
        old_tokens = AuthToken.objects.filter(
            user=user,
            token_type='access'
        ).order_by('-created_at')[5:]
        
        if old_tokens.exists():
            # 获取要删除的token ID列表
            old_token_ids = list(old_tokens.values_list('id', flat=True))
            AuthToken.objects.filter(id__in=old_token_ids).delete()
        
        access_token, refresh_token = AuthToken.create_token_pair(user, device_info)
        
        # 记录成功的登录历史
        LoginHistory.objects.create(
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_method='password',
            is_successful=True
        )
        
        response_data = {
            'user': UserSerializer(user).data,
            'tokens': {
                'access': access_token.token,
                'refresh': refresh_token.token,
            },
            'session_expires': remember_me
        }
        
        # 创建响应
        response = BaseApiResponse.success(
            data=response_data,
            message=f"欢迎回来，{user.display_name}！"
        )
        
        # 设置安全cookie
        max_age = 60 * 60 * 24 * 30 if remember_me else 60 * 60 * 24 * 7  # 30天或7天
        
        cookie_manager.set_user_cookie(response, user, max_age)
        cookie_manager.set_token_cookie(response, access_token.token, max_age)
        
        return response
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@extend_schema(
    tags=['Authentication'],
    summary='用户登出',
    description='用户登出，撤销token并清除cookie',
    responses={
        200: 'Logout successful - 登出成功',
        401: 'Unauthorized - 未认证'
    }
)
class LogoutView(APIView):
    """用户登出视图"""
    permission_classes = [permissions.IsAuthenticated]
    
    @log_api_call
    @handle_exceptions
    @api_response(success_message="登出成功")
    def post(self, request):
        # 撤销当前用户的所有token
        if hasattr(request.user, '_from_cookie'):
            # 如果是从cookie认证的用户，需要获取真实用户对象
            real_user = request.user.get_real_user()
            if real_user:
                AuthToken.objects.filter(user=real_user, is_active=True).update(is_active=False)
        else:
            AuthToken.objects.filter(user=request.user, is_active=True).update(is_active=False)
        
        # 登出用户
        logout(request)
        
        # 创建响应
        response = BaseApiResponse.success(
            data=None,
            message="您已成功登出，期待您的再次访问！"
        )
        
        # 清除所有认证相关的cookie
        cookie_manager.clear_cookies(response)
        
        return response


@extend_schema(
    tags=['Authentication'],
    summary='修改密码',
    description='用户修改登录密码',
    request=PasswordChangeSerializer,
    responses={
        200: 'Password changed successfully - 密码修改成功',
        400: 'Bad Request - 参数错误',
        401: 'Unauthorized - 未认证'
    }
)
class PasswordChangeView(APIView):
    """密码修改视图"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # 密码修改后不需要重新登录，保持现有session
            
            return Response({'message': '密码修改成功'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='密码重置',
    description='发送密码重置邮件',
    request=PasswordResetSerializer,
    responses={
        200: 'Password reset email sent - 重置邮件已发送',
        400: 'Bad Request - 参数错误'
    }
)
class PasswordResetView(APIView):
    """密码重置视图"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            # 这里应该发送重置邮件，暂时只返回成功消息
            return Response({
                'message': f'重置密码邮件已发送到 {email}'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='确认密码重置',
    description='通过重置token确认并设置新密码',
    request=PasswordResetConfirmSerializer,
    responses={
        200: 'Password reset successful - 密码重置成功',
        400: 'Bad Request - token无效或参数错误'
    }
)
class PasswordResetConfirmView(APIView):
    """密码重置确认视图"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            # 这里应该验证token并重置密码，暂时只返回成功消息
            return Response({'message': '密码重置成功'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='检查认证状态',
    description='检查当前用户的认证状态和基本信息',
    responses={
        200: UserSerializer,
        401: 'Unauthorized - 未认证'
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@log_api_call
@handle_exceptions
def check_auth(request):
    """检查用户认证状态"""
    # 如果是从cookie认证的用户，返回cookie数据
    if hasattr(request.user, '_from_cookie'):
        user_data = {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'nickname': request.user.nickname,
            'display_name': request.user.display_name,
            'is_active': request.user.is_active,
            'is_verified': request.user.is_verified,
            'roles': request.user.roles,
            'permissions': request.user.permissions,
            'from_cookie': True
        }
    else:
        user_data = UserSerializer(request.user).data
        user_data['from_cookie'] = False
    
    return BaseApiResponse.success(
        data={
            'authenticated': True,
            'user': user_data
        },
        message="认证状态检查成功"
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@log_api_call
@handle_exceptions
def refresh_session(request):
    """刷新session（延长登录时间）"""
    # 延长session时间
    request.session.set_expiry(60 * 60 * 24 * 7)  # 7天
    
    # 获取用户对象
    user = request.user
    if hasattr(request.user, '_from_cookie'):
        user = request.user.get_real_user()
        if not user:
            raise UserNotFoundException()
    
    # 刷新用户cookie
    response = BaseApiResponse.success(
        data={'user': UserSerializer(user).data},
        message="Session已刷新"
    )
    
    cookie_manager.refresh_user_cookie(response, user)
    
    return response


@extend_schema(
    tags=['Authentication'],
    summary='刷新访问令牌',
    description='使用refresh token获取新的access token',
    request=ShortTokenSerializer,
    responses={
        200: 'Token refreshed successfully - token刷新成功',
        400: 'Bad Request - refresh token无效或已过期',
        401: 'Unauthorized - refresh token不存在'
    }
)
class TokenRefreshView(APIView):
    """Token刷新视图"""
    permission_classes = [permissions.AllowAny]
    
    @log_api_call
    @handle_exceptions
    @validate_request_data(required_fields=['refresh_token'])
    @api_response(success_message="Token刷新成功")
    @transaction.atomic
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        try:
            # 验证refresh token
            auth_token = AuthToken.objects.select_related('user').get(
                token=refresh_token,
                token_type='refresh'
            )
            
            if not auth_token.is_valid():
                raise TokenExpiredException()
            
            user = auth_token.user
            
            # 生成新的access token
            device_info = auth_token.device_info
            access_token = AuthToken.objects.create(
                user=user,
                token=AuthToken.generate_token(),
                token_type='access',
                device_info=device_info,
                expires_at=timezone.now() + timezone.timedelta(hours=1)
            )
            
            # 刷新refresh token的过期时间
            auth_token.refresh()
            
            response_data = {
                'access': access_token.token,
                'refresh': auth_token.token,
                'user': UserSerializer(user).data
            }
            
            # 创建响应
            response = BaseApiResponse.success(
                data=response_data,
                message="Token刷新成功"
            )
            
            # 更新token cookie
            cookie_manager.set_token_cookie(response, access_token.token)
            cookie_manager.refresh_user_cookie(response, user)
            
            return response
            
        except AuthToken.DoesNotExist:
            raise InvalidCredentialsException("无效的refresh token")


@extend_schema(
    tags=['Authentication'],
    summary='我的登录历史',
    description='获取当前用户的登录历史记录',
    responses={
        200: LoginHistorySerializer(many=True),
        401: 'Unauthorized - 未认证'
    }
)
class UserLoginHistoryView(generics.ListAPIView):
    """用户登录历史视图"""
    serializer_class = LoginHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LoginHistory.objects.filter(user=self.request.user).order_by('-login_time')
