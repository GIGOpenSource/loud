"""
认证模块响应工具类
提供认证相关的响应处理功能
"""

from rest_framework import status
from utils.response import BaseApiResponse, ResponseCode, ResponseMessage


class AuthResponseCode:
    """认证模块响应状态码定义"""
    
    # 认证成功状态码 (2100-2199)
    LOGIN_SUCCESS = 2100
    LOGOUT_SUCCESS = 2101
    REGISTER_SUCCESS = 2102
    PASSWORD_CHANGED = 2103
    PASSWORD_RESET_SENT = 2104
    PASSWORD_RESET_SUCCESS = 2105
    SESSION_REFRESHED = 2106
    
    # 认证错误状态码 (6100-6199)
    USER_NOT_FOUND = 6101
    USER_ALREADY_EXISTS = 6102
    INVALID_CREDENTIALS = 6103
    TOKEN_EXPIRED = 6104
    INSUFFICIENT_PERMISSIONS = 6105
    ROLE_NOT_FOUND = 6106
    ROLE_ALREADY_EXISTS = 6107
    ACCOUNT_LOCKED = 6108
    EMAIL_NOT_VERIFIED = 6109
    PASSWORD_TOO_WEAK = 6110


class AuthResponseMessage:
    """认证模块响应消息定义"""
    
    # 认证成功消息
    LOGIN_SUCCESS = "登录成功"
    LOGOUT_SUCCESS = "登出成功"
    REGISTER_SUCCESS = "注册成功"
    PASSWORD_CHANGED = "密码修改成功"
    PASSWORD_RESET_SENT = "密码重置邮件已发送"
    PASSWORD_RESET_SUCCESS = "密码重置成功"
    SESSION_REFRESHED = "会话已刷新"
    
    # 认证错误消息
    USER_NOT_FOUND = "用户不存在"
    USER_ALREADY_EXISTS = "用户已存在"
    INVALID_CREDENTIALS = "用户名或密码错误"
    TOKEN_EXPIRED = "令牌已过期"
    INSUFFICIENT_PERMISSIONS = "权限不足"
    ROLE_NOT_FOUND = "角色不存在"
    ROLE_ALREADY_EXISTS = "角色已存在"
    ACCOUNT_LOCKED = "账户已被锁定"
    EMAIL_NOT_VERIFIED = "邮箱未验证"
    PASSWORD_TOO_WEAK = "密码强度不足"


class AuthApiResponse(BaseApiResponse):
    """认证模块API响应工具类"""
    
    @staticmethod
    def login_success(user_data, tokens=None, **kwargs):
        """登录成功响应"""
        data = {'user': user_data}
        if tokens:
            data['tokens'] = tokens
        
        return AuthApiResponse.success(
            data=data,
            message=AuthResponseMessage.LOGIN_SUCCESS,
            code=AuthResponseCode.LOGIN_SUCCESS,
            **kwargs
        )
    
    @staticmethod
    def logout_success(**kwargs):
        """登出成功响应"""
        return AuthApiResponse.success(
            data=None,
            message=AuthResponseMessage.LOGOUT_SUCCESS,
            code=AuthResponseCode.LOGOUT_SUCCESS,
            **kwargs
        )
    
    @staticmethod
    def register_success(user_data, tokens=None, **kwargs):
        """注册成功响应"""
        data = {'user': user_data}
        if tokens:
            data['tokens'] = tokens
        
        return AuthApiResponse.created(
            data=data,
            message=AuthResponseMessage.REGISTER_SUCCESS,
            code=AuthResponseCode.REGISTER_SUCCESS,
            **kwargs
        )
    
    @staticmethod
    def password_changed(**kwargs):
        """密码修改成功响应"""
        return AuthApiResponse.success(
            data=None,
            message=AuthResponseMessage.PASSWORD_CHANGED,
            code=AuthResponseCode.PASSWORD_CHANGED,
            **kwargs
        )
    
    @staticmethod
    def password_reset_sent(email, **kwargs):
        """密码重置邮件发送成功响应"""
        return AuthApiResponse.success(
            data={'email': email},
            message=AuthResponseMessage.PASSWORD_RESET_SENT,
            code=AuthResponseCode.PASSWORD_RESET_SENT,
            **kwargs
        )
    
    @staticmethod
    def password_reset_success(**kwargs):
        """密码重置成功响应"""
        return AuthApiResponse.success(
            data=None,
            message=AuthResponseMessage.PASSWORD_RESET_SUCCESS,
            code=AuthResponseCode.PASSWORD_RESET_SUCCESS,
            **kwargs
        )
    
    @staticmethod
    def session_refreshed(user_data, **kwargs):
        """会话刷新成功响应"""
        return AuthApiResponse.success(
            data={'user': user_data},
            message=AuthResponseMessage.SESSION_REFRESHED,
            code=AuthResponseCode.SESSION_REFRESHED,
            **kwargs
        )


class AuthBusinessResponse:
    """认证模块业务响应工具类"""
    
    @staticmethod
    def user_not_found(username: str = None):
        """用户不存在响应"""
        message = f"用户 {username} 不存在" if username else AuthResponseMessage.USER_NOT_FOUND
        return AuthApiResponse.not_found(message, AuthResponseCode.USER_NOT_FOUND)
    
    @staticmethod
    def user_already_exists(username: str = None):
        """用户已存在响应"""
        message = f"用户 {username} 已存在" if username else AuthResponseMessage.USER_ALREADY_EXISTS
        return AuthApiResponse.error(message, AuthResponseCode.USER_ALREADY_EXISTS)
    
    @staticmethod
    def invalid_credentials():
        """无效凭据响应"""
        return AuthApiResponse.error(
            AuthResponseMessage.INVALID_CREDENTIALS,
            AuthResponseCode.INVALID_CREDENTIALS,
            http_status=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def token_expired():
        """令牌过期响应"""
        return AuthApiResponse.unauthorized(AuthResponseMessage.TOKEN_EXPIRED, AuthResponseCode.TOKEN_EXPIRED)
    
    @staticmethod
    def insufficient_permissions():
        """权限不足响应"""
        return AuthApiResponse.forbidden(AuthResponseMessage.INSUFFICIENT_PERMISSIONS, AuthResponseCode.INSUFFICIENT_PERMISSIONS)
    
    @staticmethod
    def role_not_found(role_name: str = None):
        """角色不存在响应"""
        message = f"角色 {role_name} 不存在" if role_name else AuthResponseMessage.ROLE_NOT_FOUND
        return AuthApiResponse.not_found(message, AuthResponseCode.ROLE_NOT_FOUND)
    
    @staticmethod
    def role_already_exists(role_name: str = None):
        """角色已存在响应"""
        message = f"角色 {role_name} 已存在" if role_name else AuthResponseMessage.ROLE_ALREADY_EXISTS
        return AuthApiResponse.error(message, AuthResponseCode.ROLE_ALREADY_EXISTS)
    
    @staticmethod
    def account_locked():
        """账户锁定响应"""
        return AuthApiResponse.forbidden(AuthResponseMessage.ACCOUNT_LOCKED, AuthResponseCode.ACCOUNT_LOCKED)
    
    @staticmethod
    def email_not_verified():
        """邮箱未验证响应"""
        return AuthApiResponse.forbidden(AuthResponseMessage.EMAIL_NOT_VERIFIED, AuthResponseCode.EMAIL_NOT_VERIFIED)
    
    @staticmethod
    def password_too_weak():
        """密码强度不足响应"""
        return AuthApiResponse.validation_error(
            {'password': [AuthResponseMessage.PASSWORD_TOO_WEAK]},
            AuthResponseMessage.PASSWORD_TOO_WEAK,
            AuthResponseCode.PASSWORD_TOO_WEAK
        )


# 便捷的响应函数
def auth_success_response(data=None, message=None, code=None, **kwargs):
    """认证成功响应快捷函数"""
    return AuthApiResponse.success(data=data, message=message, code=code, **kwargs)


def auth_error_response(message=None, code=None, http_status=None, **kwargs):
    """认证错误响应快捷函数"""
    return AuthApiResponse.error(
        message=message or AuthResponseMessage.INVALID_CREDENTIALS,
        code=code or AuthResponseCode.INVALID_CREDENTIALS,
        http_status=http_status or status.HTTP_401_UNAUTHORIZED,
        **kwargs
    )
