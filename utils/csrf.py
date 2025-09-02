"""
自定义CSRF中间件
为API端点提供CSRF豁免
"""

import re
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware


class CustomCsrfViewMiddleware(CsrfViewMiddleware):
    """自定义CSRF中间件，为API端点提供豁免"""
    
    def process_request(self, request):
        # 检查是否是API端点
        if self._is_api_endpoint(request.path):
            # 为API端点设置CSRF豁免标记
            request._dont_enforce_csrf_checks = True
            return None
        
        # 对于非API端点，使用默认的CSRF处理
        return super().process_request(request)
    
    def _is_api_endpoint(self, path):
        """检查是否是API端点"""
        # 检查路径是否以/api/开头
        if path.startswith('/api/'):
            return True
        
        # 检查是否匹配CSRF豁免URL模式
        if hasattr(settings, 'CSRF_EXEMPT_URLS'):
            for pattern in settings.CSRF_EXEMPT_URLS:
                if re.match(pattern, path):
                    return True
        
        return False
