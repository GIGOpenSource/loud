"""
用户模块统一视图
重构后的用户模块主要视图
"""

from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema

from utils.response import BaseApiResponse
from utils.decorators import log_api_call, handle_exceptions

from .dashboard import UserDashboardView, UserOverviewView

User = get_user_model()


@extend_schema(
    tags=['User Dashboard'],
    summary='用户仪表板',
    description='获取用户仪表板数据，包含用户基本信息、资料、偏好设置、钱包数据和统计信息',
    responses={
        200: 'Success - 返回完整的仪表板数据',
        401: 'Unauthorized - 未认证'
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@log_api_call
@handle_exceptions
def user_dashboard(request):
    """
    用户仪表板接口
    整合所有用户数据的统一入口
    """
    view = UserDashboardView()
    view.request = request
    return view.get(request)


@extend_schema(
    tags=['User Dashboard'],
    summary='用户概览',
    description='获取用户概览信息，包含基本信息和各模块的状态概览',
    responses={
        200: 'Success - 返回用户概览数据',
        401: 'Unauthorized - 未认证'
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@log_api_call
@handle_exceptions
def user_overview(request):
    """
    用户概览接口
    提供用户基本信息和模块状态
    """
    view = UserOverviewView()
    view.request = request
    return view.get(request)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@log_api_call
@handle_exceptions
def verify_user(request):
    """
    验证用户接口
    检查用户状态和权限
    """
    user = request.user
    
    verification_data = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'permissions': list(user.get_all_permissions()),
        'groups': [group.name for group in user.groups.all()],
    }
    
    return BaseApiResponse.success(
        data=verification_data,
        message="用户验证成功"
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def module_info(request):
    """
    模块信息接口
    返回users模块的结构和功能信息
    """
    module_info = {
        'name': 'users',
        'version': '2.0.0',
        'description': '用户管理模块，提供用户资料、偏好设置和钱包管理功能',
        'architecture': 'modular',
        'submodules': {
            'profiles': {
                'name': '用户资料',
                'description': '管理用户个人信息、头像、联系方式等',
                'endpoints': [
                    '/api/users/profiles/',
                    '/api/users/profiles/my_profile/',
                    '/api/users/public/<user_id>/',
                ],
                'features': [
                    '个人资料管理', '头像上传', '隐私设置', '公开资料查看'
                ]
            },
            'preferences': {
                'name': '用户偏好',
                'description': '管理用户的个性化设置和偏好配置',
                'endpoints': [
                    '/api/users/preferences/',
                    '/api/users/preferences/my_preferences/',
                ],
                'features': [
                    '主题设置', '语言切换', '通知配置', '隐私控制'
                ]
            },
            'wallets': {
                'name': '用户钱包',
                'description': '管理用户余额、交易记录和钱包操作',
                'endpoints': [
                    '/api/users/wallets/',
                    '/api/users/wallets/{id}/deposit/',
                    '/api/users/wallets/{id}/withdraw/',
                    '/api/users/wallets/{id}/transfer/',
                ],
                'features': [
                    '余额管理', '充值提现', '转账功能', '交易记录', '支付密码'
                ]
            }
        },
        'base_classes_used': [
            'BaseAuditModel', 'BaseModelSerializer', 'BaseModelViewSet',
            'BasePermission', 'BaseFilterSet', 'BasePagination'
        ],
        'standards': [
            '统一的API响应格式', '标准化的错误处理', '完整的权限控制',
            '丰富的过滤和搜索', '自动缓存管理', '审计日志记录'
        ]
    }
    
    return BaseApiResponse.success(
        data=module_info,
        message="获取模块信息成功"
    )