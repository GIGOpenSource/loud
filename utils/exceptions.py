"""
自定义异常类和异常处理中间件
用于统一处理各种异常并返回标准化的错误响应
"""

from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.core.exceptions import ValidationError, ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from .response import BaseApiResponse, ResponseCode, ResponseMessage


class BusinessException(APIException):
    """业务异常基类"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('业务处理异常')
    default_code = ResponseCode.BAD_REQUEST


def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    统一处理各种异常并返回标准化的错误响应
    """
    
    # 调用DRF默认的异常处理器
    response = exception_handler(exc, context)
    
    if response is not None:
        # 处理DRF已知的异常
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                # 字段验证错误
                return BaseApiResponse.validation_error(
                    errors=exc.detail,
                    message="数据验证失败"
                )
            else:
                # 其他DRF异常
                return BaseApiResponse.error(
                    message=str(exc.detail),
                    code=getattr(exc, 'default_code', ResponseCode.BAD_REQUEST),
                    http_status=response.status_code
                )
    
    # 处理Django原生异常
    if isinstance(exc, Http404):
        return BaseApiResponse.not_found("请求的资源不存在")
    
    elif isinstance(exc, ValidationError):
        if hasattr(exc, 'message_dict'):
            # 字段验证错误
            return BaseApiResponse.validation_error(
                errors=exc.message_dict,
                message="数据验证失败"
            )
        else:
            # 非字段验证错误
            return BaseApiResponse.validation_error(
                errors={'non_field_errors': exc.messages},
                message="数据验证失败"
            )
    
    elif isinstance(exc, ObjectDoesNotExist):
        return BaseApiResponse.not_found("请求的对象不存在")
    
    elif isinstance(exc, PermissionDenied):
        return BaseApiResponse.forbidden("权限不足")
    
    # 处理自定义业务异常
    elif isinstance(exc, BusinessException):
        return BaseApiResponse.error(
            message=str(exc.detail),
            code=exc.default_code,
            http_status=exc.status_code
        )
    
    # 处理其他未捕获的异常
    else:
        # 在开发环境中返回详细错误信息
        import os
        if os.getenv('DEBUG', 'False').lower() == 'true':
            return BaseApiResponse.internal_error(
                message=f"服务器内部错误: {str(exc)}",
                data={'exception_type': type(exc).__name__}
            )
        else:
            # 在生产环境中返回通用错误信息
            return BaseApiResponse.internal_error(
                message="服务器内部错误，请稍后重试"
            )


class ExceptionMiddleware:
    """异常处理中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """处理异常"""
        # 只处理API请求的异常
        if request.path.startswith('/api/'):
            from rest_framework.response import Response
            from rest_framework import status
            
            # 使用自定义异常处理器
            response = custom_exception_handler(exception, {'request': request})
            if response:
                return response
        
        # 对于非API请求，返回None让Django处理
        return None
