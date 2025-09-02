"""
响应处理装饰器
用于简化视图中的响应处理，提供统一的响应格式
"""

import functools
from typing import Callable, Any, Optional
from rest_framework.response import Response
from rest_framework import status
from .response import BaseApiResponse, ResponseCode, ResponseMessage, BasePaginatedResponse


def api_response(
    success_message: str = None,
    error_message: str = None,
    success_code: int = None,
    error_code: int = None
):
    """
    API响应装饰器
    自动处理视图的响应格式
    
    Args:
        success_message: 成功时的消息
        error_message: 错误时的消息
        success_code: 成功时的状态码
        error_code: 错误时的状态码
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # 如果返回的是Response对象，直接返回
                if isinstance(result, Response):
                    return result
                
                # 如果返回的是元组 (data, message, code)
                if isinstance(result, tuple) and len(result) >= 1:
                    data = result[0]
                    message = result[1] if len(result) > 1 else (success_message or ResponseMessage.SUCCESS)
                    code = result[2] if len(result) > 2 else (success_code or ResponseCode.SUCCESS)
                    
                    return BaseApiResponse.success(
                        data=data,
                        message=message,
                        code=code
                    )
                
                # 如果返回的是数据，包装成成功响应
                return BaseApiResponse.success(
                    data=result,
                    message=success_message or ResponseMessage.SUCCESS,
                    code=success_code or ResponseCode.SUCCESS
                )
                
            except Exception as e:
                # 处理异常
                return BaseApiResponse.error(
                    message=error_message or str(e),
                    code=error_code or ResponseCode.BAD_REQUEST
                )
        
        return wrapper
    return decorator


def paginated_api_response(
    page_size: int = 10,
    message: str = None,
    code: int = None,
    serializer_class=None
):
    """
    分页API响应装饰器
    自动处理分页视图的响应格式
    
    Args:
        page_size: 每页大小
        message: 响应消息
        code: 状态码
        serializer_class: 序列化器类
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # 如果返回的是Response对象，直接返回
                if isinstance(result, Response):
                    return result
                
                # 如果返回的是元组 (queryset, page, page_size, message, code)
                if isinstance(result, tuple) and len(result) >= 1:
                    queryset = result[0]
                    page = result[1] if len(result) > 1 else 1
                    size = result[2] if len(result) > 2 else page_size
                    msg = result[3] if len(result) > 3 else (message or ResponseMessage.SUCCESS)
                    c = result[4] if len(result) > 4 else (code or ResponseCode.SUCCESS)
                    
                    return BasePaginatedResponse.paginate(
                        queryset=queryset,
                        page=page,
                        page_size=size,
                        message=msg,
                        code=c,
                        serializer_class=serializer_class
                    )
                
                # 如果返回的是查询集，使用默认参数
                return BasePaginatedResponse.paginate(
                    queryset=result,
                    page=1,
                    page_size=page_size,
                    message=message or ResponseMessage.SUCCESS,
                    code=code or ResponseCode.SUCCESS,
                    serializer_class=serializer_class
                )
                
            except Exception as e:
                # 处理异常
                return BaseApiResponse.error(
                    message=str(e),
                    code=ResponseCode.BAD_REQUEST
                )
        
        return wrapper
    return decorator


def handle_exceptions(func: Callable) -> Callable:
    """
    异常处理装饰器
    统一处理视图中的异常
    
    Args:
        func: 被装饰的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 导入Django和DRF异常类型
            from django.core.exceptions import ValidationError, ObjectDoesNotExist, PermissionDenied
            from django.http import Http404
            from rest_framework.exceptions import APIException
            from .exceptions import BusinessException
            
            # 根据异常类型返回不同的响应
            if isinstance(e, Http404):
                return BaseApiResponse.not_found("请求的资源不存在")
            elif isinstance(e, ObjectDoesNotExist):
                return BaseApiResponse.not_found("请求的对象不存在")
            elif isinstance(e, PermissionDenied):
                return BaseApiResponse.forbidden("权限不足")
            elif isinstance(e, ValidationError):
                return BaseApiResponse.validation_error(
                    errors=e.message_dict if hasattr(e, 'message_dict') else e.messages,
                    message="数据验证失败"
                )
            elif isinstance(e, BusinessException):
                return BaseApiResponse.error(
                    message=str(e.detail),
                    code=e.default_code,
                    http_status=e.status_code
                )
            elif isinstance(e, APIException):
                return BaseApiResponse.error(
                    message=str(e.detail),
                    code=getattr(e, 'default_code', ResponseCode.BAD_REQUEST),
                    http_status=e.status_code
                )
            else:
                # 其他异常
                return BaseApiResponse.internal_error(str(e))
    
    return wrapper


def validate_request_data(required_fields: list = None, optional_fields: list = None):
    """
    请求数据验证装饰器
    验证请求中是否包含必需的字段
    
    Args:
        required_fields: 必需字段列表
        optional_fields: 可选字段列表
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if hasattr(arg, 'data'):
                    request = arg
                    break
            
            if request and hasattr(request, 'data'):
                data = request.data
                
                # 检查必需字段
                if required_fields:
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        return BaseApiResponse.validation_error(
                            errors={'missing_fields': missing_fields},
                            message=f"缺少必需字段: {', '.join(missing_fields)}"
                        )
                
                # 检查字段类型（可选）
                if optional_fields:
                    # 这里可以添加字段类型验证逻辑
                    pass
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_api_call(func: Callable) -> Callable:
    """
    API调用日志装饰器
    记录API调用的基本信息
    
    Args:
        func: 被装饰的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import logging
        logger = logging.getLogger('api')
        
        # 获取请求信息
        request = None
        for arg in args:
            if hasattr(arg, 'method') and hasattr(arg, 'path'):
                request = arg
                break
        
        if request:
            logger.info(f"API调用: {request.method} {request.path} - 用户: {getattr(request.user, 'username', 'anonymous')}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"API调用成功: {request.method} {request.path}")
            return result
        except Exception as e:
            logger.error(f"API调用失败: {request.method} {request.path} - 错误: {str(e)}")
            raise
        
        return func(*args, **kwargs)
    
    return wrapper
