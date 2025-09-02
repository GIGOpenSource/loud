"""
基础响应工具类
提供统一的API响应格式基础功能
"""

from rest_framework.response import Response
from rest_framework import status
from typing import Any, Dict, List, Optional, Union
from django.core.paginator import Paginator
from django.db.models import QuerySet


class ResponseCode:
    """响应状态码定义"""
    
    # 成功状态码 (2000-2999)
    SUCCESS = 2000
    CREATED = 2001
    UPDATED = 2002
    DELETED = 2003
    
    # 客户端错误状态码 (4000-4999)
    BAD_REQUEST = 4000
    UNAUTHORIZED = 4001
    FORBIDDEN = 4003
    NOT_FOUND = 4004
    METHOD_NOT_ALLOWED = 4005
    VALIDATION_ERROR = 4220
    
    # 服务器错误状态码 (5000-5999)
    INTERNAL_ERROR = 5000
    SERVICE_UNAVAILABLE = 5003


class ResponseMessage:
    """基础响应消息定义"""
    
    # 成功消息
    SUCCESS = "操作成功"
    CREATED = "创建成功"
    UPDATED = "更新成功"
    DELETED = "删除成功"
    
    # 错误消息
    BAD_REQUEST = "请求参数错误"
    UNAUTHORIZED = "未授权访问"
    FORBIDDEN = "禁止访问"
    NOT_FOUND = "资源不存在"
    METHOD_NOT_ALLOWED = "请求方法不允许"
    VALIDATION_ERROR = "数据验证失败"
    INTERNAL_ERROR = "服务器内部错误"
    SERVICE_UNAVAILABLE = "服务不可用"


class BaseApiResponse:
    """基础API响应工具类"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = ResponseMessage.SUCCESS,
        code: int = ResponseCode.SUCCESS,
        http_status: int = status.HTTP_200_OK,
        **kwargs
    ) -> Response:
        """
        成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            code: 自定义状态码
            http_status: HTTP状态码
            **kwargs: 额外参数
            
        Returns:
            Response: 标准化的响应对象
        """
        response_data = {
            'success': True,
            'code': code,
            'message': message,
            'data': data,
            **kwargs
        }
        return Response(response_data, status=http_status)
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = ResponseMessage.CREATED,
        code: int = ResponseCode.CREATED,
        **kwargs
    ) -> Response:
        """创建成功响应"""
        return BaseApiResponse.success(
            data=data,
            message=message,
            code=code,
            http_status=status.HTTP_201_CREATED,
            **kwargs
        )
    
    @staticmethod
    def updated(
        data: Any = None,
        message: str = ResponseMessage.UPDATED,
        code: int = ResponseCode.UPDATED,
        **kwargs
    ) -> Response:
        """更新成功响应"""
        return BaseApiResponse.success(
            data=data,
            message=message,
            code=code,
            **kwargs
        )
    
    @staticmethod
    def deleted(
        message: str = ResponseMessage.DELETED,
        code: int = ResponseCode.DELETED,
        **kwargs
    ) -> Response:
        """删除成功响应"""
        return BaseApiResponse.success(
            data=None,
            message=message,
            code=code,
            http_status=status.HTTP_204_NO_CONTENT,
            **kwargs
        )
    
    @staticmethod
    def error(
        message: str = ResponseMessage.BAD_REQUEST,
        code: int = ResponseCode.BAD_REQUEST,
        http_status: int = status.HTTP_400_BAD_REQUEST,
        data: Any = None,
        **kwargs
    ) -> Response:
        """
        错误响应
        
        Args:
            message: 错误消息
            code: 自定义错误码
            http_status: HTTP状态码
            data: 错误详情数据
            **kwargs: 额外参数
            
        Returns:
            Response: 标准化的错误响应对象
        """
        response_data = {
            'success': False,
            'code': code,
            'message': message,
            'data': data,
            **kwargs
        }
        return Response(response_data, status=http_status)
    
    @staticmethod
    def not_found(
        message: str = ResponseMessage.NOT_FOUND,
        code: int = ResponseCode.NOT_FOUND,
        **kwargs
    ) -> Response:
        """资源不存在响应"""
        return BaseApiResponse.error(
            message=message,
            code=code,
            http_status=status.HTTP_404_NOT_FOUND,
            **kwargs
        )
    
    @staticmethod
    def unauthorized(
        message: str = ResponseMessage.UNAUTHORIZED,
        code: int = ResponseCode.UNAUTHORIZED,
        **kwargs
    ) -> Response:
        """未授权响应"""
        return BaseApiResponse.error(
            message=message,
            code=code,
            http_status=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )
    
    @staticmethod
    def forbidden(
        message: str = ResponseMessage.FORBIDDEN,
        code: int = ResponseCode.FORBIDDEN,
        **kwargs
    ) -> Response:
        """禁止访问响应"""
        return BaseApiResponse.error(
            message=message,
            code=code,
            http_status=status.HTTP_403_FORBIDDEN,
            **kwargs
        )
    
    @staticmethod
    def validation_error(
        errors: Any,
        message: str = ResponseMessage.VALIDATION_ERROR,
        code: int = ResponseCode.VALIDATION_ERROR,
        **kwargs
    ) -> Response:
        """数据验证错误响应"""
        return BaseApiResponse.error(
            message=message,
            code=code,
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            data=errors,
            **kwargs
        )
    
    @staticmethod
    def internal_error(
        message: str = ResponseMessage.INTERNAL_ERROR,
        code: int = ResponseCode.INTERNAL_ERROR,
        **kwargs
    ) -> Response:
        """服务器内部错误响应"""
        return BaseApiResponse.error(
            message=message,
            code=code,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            **kwargs
        )


class BasePaginatedResponse:
    """基础分页响应工具类"""
    
    @staticmethod
    def paginate(
        queryset: QuerySet,
        page: int = 1,
        page_size: int = 10,
        message: str = ResponseMessage.SUCCESS,
        code: int = ResponseCode.SUCCESS,
        serializer_class=None,
        **kwargs
    ) -> Response:
        """
        分页响应
        
        Args:
            queryset: 查询集
            page: 页码
            page_size: 每页大小
            message: 响应消息
            code: 自定义状态码
            serializer_class: 序列化器类
            **kwargs: 额外参数
            
        Returns:
            Response: 分页响应对象
        """
        paginator = Paginator(queryset, page_size)
        
        try:
            page_obj = paginator.page(page)
        except Exception:
            return BaseApiResponse.not_found("页码超出范围")
        
        # 序列化数据
        if serializer_class:
            data = serializer_class(page_obj.object_list, many=True).data
        else:
            data = list(page_obj.object_list)
        
        # 构建分页信息
        pagination_info = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
        
        if page_obj.has_next():
            pagination_info['next_page'] = page_obj.next_page_number()
        if page_obj.has_previous():
            pagination_info['previous_page'] = page_obj.previous_page_number()
        
        response_data = {
            'success': True,
            'code': code,
            'message': message,
            'data': data,
            'pagination': pagination_info,
            **kwargs
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


# 便捷的响应函数
def success_response(data=None, message=None, code=None, **kwargs):
    """成功响应快捷函数"""
    return BaseApiResponse.success(data=data, message=message, code=code, **kwargs)


def error_response(message=None, code=None, http_status=None, **kwargs):
    """错误响应快捷函数"""
    return BaseApiResponse.error(
        message=message or ResponseMessage.BAD_REQUEST,
        code=code or ResponseCode.BAD_REQUEST,
        http_status=http_status or status.HTTP_400_BAD_REQUEST,
        **kwargs
    )


def paginated_response(queryset, page=1, page_size=10, serializer_class=None, **kwargs):
    """分页响应快捷函数"""
    return BasePaginatedResponse.paginate(
        queryset=queryset,
        page=page,
        page_size=page_size,
        serializer_class=serializer_class,
        **kwargs
    )
