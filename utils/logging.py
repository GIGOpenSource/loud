"""
日志工具类
提供统一的日志记录功能，包括入参日志和返回日志
"""

import json
import logging
import time
from typing import Any, Dict, Optional
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from rest_framework.response import Response
from rest_framework import status


class APILogger:
    """API日志记录器"""
    
    def __init__(self, name: str = 'api'):
        self.logger = logging.getLogger(name)
    
    def log_request(self, request, view_name: str = None, **kwargs):
        """
        记录请求日志
        
        Args:
            request: HTTP请求对象
            view_name: 视图名称
            **kwargs: 额外参数
        """
        try:
            # 获取请求信息
            method = request.method
            path = request.path
            user = getattr(request.user, 'username', 'anonymous')
            ip = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # 获取请求数据
            request_data = self._get_request_data(request)
            
            # 构建日志消息
            log_data = {
                'type': 'request',
                'method': method,
                'path': path,
                'user': user,
                'ip': ip,
                'user_agent': user_agent,
                'data': request_data,
                'view_name': view_name,
                'timestamp': time.time(),
                **kwargs
            }
            
            # 记录日志
            self.logger.info(f"API请求: {json.dumps(log_data, ensure_ascii=False, default=str)}")
            
        except Exception as e:
            self.logger.error(f"记录请求日志失败: {str(e)}")
    
    def log_response(self, request, response, view_name: str = None, duration: float = None, **kwargs):
        """
        记录响应日志
        
        Args:
            request: HTTP请求对象
            response: HTTP响应对象
            view_name: 视图名称
            duration: 请求处理时长
            **kwargs: 额外参数
        """
        try:
            # 获取请求信息
            method = request.method
            path = request.path
            user = getattr(request.user, 'username', 'anonymous')
            ip = self._get_client_ip(request)
            
            # 获取响应数据
            response_data = self._get_response_data(response)
            
            # 构建日志消息
            log_data = {
                'type': 'response',
                'method': method,
                'path': path,
                'user': user,
                'ip': ip,
                'status_code': response.status_code,
                'data': response_data,
                'view_name': view_name,
                'duration': duration,
                'timestamp': time.time(),
                **kwargs
            }
            
            # 根据状态码选择日志级别
            if response.status_code >= 400:
                self.logger.warning(f"API响应错误: {json.dumps(log_data, ensure_ascii=False, default=str)}")
            else:
                self.logger.info(f"API响应: {json.dumps(log_data, ensure_ascii=False, default=str)}")
                
        except Exception as e:
            self.logger.error(f"记录响应日志失败: {str(e)}")
    
    def log_error(self, request, error, view_name: str = None, **kwargs):
        """
        记录错误日志
        
        Args:
            request: HTTP请求对象
            error: 错误对象
            view_name: 视图名称
            **kwargs: 额外参数
        """
        try:
            # 获取请求信息
            method = request.method
            path = request.path
            user = getattr(request.user, 'username', 'anonymous')
            ip = self._get_client_ip(request)
            
            # 构建日志消息
            log_data = {
                'type': 'error',
                'method': method,
                'path': path,
                'user': user,
                'ip': ip,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'view_name': view_name,
                'timestamp': time.time(),
                **kwargs
            }
            
            # 记录错误日志
            self.logger.error(f"API错误: {json.dumps(log_data, ensure_ascii=False, default=str)}")
            
        except Exception as e:
            self.logger.error(f"记录错误日志失败: {str(e)}")
    
    def _get_client_ip(self, request) -> str:
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_request_data(self, request) -> Dict[str, Any]:
        """获取请求数据"""
        data = {}
        
        # GET参数
        if request.GET:
            data['query_params'] = dict(request.GET)
        
        # POST/PUT/PATCH数据
        if hasattr(request, 'data') and request.data:
            # 过滤敏感信息
            filtered_data = self._filter_sensitive_data(request.data)
            data['body'] = filtered_data
        
        # 文件上传
        if request.FILES:
            data['files'] = {
                name: {
                    'name': file.name,
                    'size': file.size,
                    'content_type': file.content_type
                }
                for name, file in request.FILES.items()
            }
        
        return data
    
    def _get_response_data(self, response) -> Dict[str, Any]:
        """获取响应数据"""
        data = {}
        
        if hasattr(response, 'data') and response.data:
            # 过滤敏感信息
            filtered_data = self._filter_sensitive_data(response.data)
            data['body'] = filtered_data
        
        return data
    
    def _filter_sensitive_data(self, data: Any) -> Any:
        """过滤敏感信息"""
        if isinstance(data, dict):
            filtered = {}
            sensitive_fields = {'password', 'token', 'access', 'refresh', 'secret', 'key'}
            
            for key, value in data.items():
                if key.lower() in sensitive_fields:
                    filtered[key] = '***'
                elif isinstance(value, (dict, list)):
                    filtered[key] = self._filter_sensitive_data(value)
                else:
                    filtered[key] = value
            
            return filtered
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item) for item in data]
        else:
            return data


class APILoggingMiddleware(MiddlewareMixin):
    """API日志中间件"""
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.logger = APILogger()
    
    def process_request(self, request):
        """处理请求"""
        # 只记录API请求
        if request.path.startswith('/api/'):
            # 记录请求开始时间
            request.start_time = time.time()
            
            # 记录请求日志
            self.logger.log_request(request)
        
        return None
    
    def process_response(self, request, response):
        """处理响应"""
        # 只记录API响应
        if request.path.startswith('/api/'):
            # 计算请求处理时长
            duration = None
            if hasattr(request, 'start_time'):
                duration = time.time() - request.start_time
            
            # 记录响应日志
            self.logger.log_response(request, response, duration=duration)
        
        return response
    
    def process_exception(self, request, exception):
        """处理异常"""
        # 只记录API异常
        if request.path.startswith('/api/'):
            self.logger.log_error(request, exception)
        
        return None


# 全局日志记录器实例
api_logger = APILogger()


def log_api_call(func=None, *, log_request=True, log_response=True, log_error=True):
    """
    API调用日志装饰器
    
    Args:
        func: 被装饰的函数
        log_request: 是否记录请求日志
        log_response: 是否记录响应日志
        log_error: 是否记录错误日志
    """
    def decorator(view_func):
        def wrapper(*args, **kwargs):
            # 获取请求对象
            request = None
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'path'):
                    request = arg
                    break
            
            if not request:
                return view_func(*args, **kwargs)
            
            # 获取视图名称
            view_name = view_func.__name__
            
            try:
                # 记录请求日志
                if log_request:
                    api_logger.log_request(request, view_name=view_name)
                
                # 记录开始时间
                start_time = time.time()
                
                # 执行视图函数
                response = view_func(*args, **kwargs)
                
                # 计算处理时长
                duration = time.time() - start_time
                
                # 记录响应日志
                if log_response:
                    api_logger.log_response(request, response, view_name=view_name, duration=duration)
                
                return response
                
            except Exception as e:
                # 记录错误日志
                if log_error:
                    api_logger.log_error(request, e, view_name=view_name)
                raise
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)
