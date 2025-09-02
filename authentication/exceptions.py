"""
认证模块异常类
提供认证相关的异常处理
"""

from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from .responses import AuthResponseCode, AuthResponseMessage


class AuthBusinessException(APIException):
    """认证业务异常基类"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('认证业务处理异常')
    default_code = 4000  # 使用基础响应码


class UserNotFoundException(AuthBusinessException):
    """用户不存在异常"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = AuthResponseMessage.USER_NOT_FOUND
    default_code = AuthResponseCode.USER_NOT_FOUND


class UserAlreadyExistsException(AuthBusinessException):
    """用户已存在异常"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = AuthResponseMessage.USER_ALREADY_EXISTS
    default_code = AuthResponseCode.USER_ALREADY_EXISTS


class InvalidCredentialsException(AuthBusinessException):
    """无效凭据异常"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = AuthResponseMessage.INVALID_CREDENTIALS
    default_code = AuthResponseCode.INVALID_CREDENTIALS


class TokenExpiredException(AuthBusinessException):
    """令牌过期异常"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = AuthResponseMessage.TOKEN_EXPIRED
    default_code = AuthResponseCode.TOKEN_EXPIRED


class InsufficientPermissionsException(AuthBusinessException):
    """权限不足异常"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = AuthResponseMessage.INSUFFICIENT_PERMISSIONS
    default_code = AuthResponseCode.INSUFFICIENT_PERMISSIONS


class RoleNotFoundException(AuthBusinessException):
    """角色不存在异常"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = AuthResponseMessage.ROLE_NOT_FOUND
    default_code = AuthResponseCode.ROLE_NOT_FOUND


class RoleAlreadyExistsException(AuthBusinessException):
    """角色已存在异常"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = AuthResponseMessage.ROLE_ALREADY_EXISTS
    default_code = AuthResponseCode.ROLE_ALREADY_EXISTS


class AccountLockedException(AuthBusinessException):
    """账户锁定异常"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = AuthResponseMessage.ACCOUNT_LOCKED
    default_code = AuthResponseCode.ACCOUNT_LOCKED


class EmailNotVerifiedException(AuthBusinessException):
    """邮箱未验证异常"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = AuthResponseMessage.EMAIL_NOT_VERIFIED
    default_code = AuthResponseCode.EMAIL_NOT_VERIFIED


class PasswordTooWeakException(AuthBusinessException):
    """密码强度不足异常"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = AuthResponseMessage.PASSWORD_TOO_WEAK
    default_code = AuthResponseCode.PASSWORD_TOO_WEAK
