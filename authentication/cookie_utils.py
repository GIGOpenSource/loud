"""
Cookie安全工具类
提供安全的用户信息cookie管理功能
"""

import json
import hashlib
import hmac
from django.conf import settings
from django.core.signing import Signer, BadSignature
from django.utils import timezone
from datetime import timedelta
import base64


class SecureCookieManager:
    """安全Cookie管理器"""
    
    # Cookie名称
    USER_INFO_COOKIE = 'user_info'
    TOKEN_COOKIE = 'auth_token'
    
    # Cookie配置
    DEFAULT_MAX_AGE = 60 * 60 * 24 * 7  # 7天
    
    def __init__(self):
        self.signer = Signer()
        self.secret_key = getattr(settings, 'SECRET_KEY', 'default-secret-key')
    
    def create_user_cookie_data(self, user):
        """创建用户信息cookie数据"""
        try:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nickname': user.nickname or '',
                'display_name': user.display_name,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'roles': [role.code for role in user.roles.filter(is_active=True)],
                'permissions': [perm.codename for perm in user.get_all_permissions()],
                'last_login': user.last_login_at.isoformat() if user.last_login_at else None,
                'created_at': timezone.now().isoformat(),  # cookie创建时间
            }
            
            # 添加数据完整性校验
            user_data['signature'] = self._generate_signature(user_data)
            
            return user_data
        except Exception:
            return None
    
    def _generate_signature(self, data):
        """生成数据签名"""
        # 创建数据的哈希值用于验证完整性
        data_copy = data.copy()
        data_copy.pop('signature', None)  # 移除signature字段
        data_copy.pop('created_at', None)  # 移除时间戳避免签名不一致
        
        # 按键排序确保一致性
        sorted_data = json.dumps(data_copy, sort_keys=True, separators=(',', ':'))
        
        # 生成HMAC签名
        signature = hmac.new(
            self.secret_key.encode(),
            sorted_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, data):
        """验证数据签名"""
        if not isinstance(data, dict) or 'signature' not in data:
            return False
        
        stored_signature = data.get('signature')
        calculated_signature = self._generate_signature(data)
        
        # 使用常量时间比较防止时序攻击
        return hmac.compare_digest(stored_signature, calculated_signature)
    
    def encode_cookie_value(self, data):
        """编码cookie值"""
        try:
            # 转换为JSON字符串
            json_data = json.dumps(data, separators=(',', ':'))
            
            # Base64编码
            encoded_data = base64.b64encode(json_data.encode()).decode()
            
            # 使用Django的签名机制签名
            signed_data = self.signer.sign(encoded_data)
            
            return signed_data
        except Exception:
            return None
    
    def decode_cookie_value(self, cookie_value):
        """解码cookie值"""
        try:
            if not cookie_value:
                return None
            
            # 验证签名并获取数据
            unsigned_data = self.signer.unsign(cookie_value)
            
            # Base64解码
            decoded_data = base64.b64decode(unsigned_data.encode()).decode()
            
            # 解析JSON
            data = json.loads(decoded_data)
            
            # 验证数据完整性
            if not self.verify_signature(data):
                return None
            
            # 检查cookie是否过期（基于创建时间）
            if self._is_cookie_expired(data):
                return None
            
            return data
        except (BadSignature, json.JSONDecodeError, Exception):
            return None
    
    def _is_cookie_expired(self, data):
        """检查cookie是否过期"""
        try:
            created_at_str = data.get('created_at')
            if not created_at_str:
                return True
            
            created_at = timezone.datetime.fromisoformat(
                created_at_str.replace('Z', '+00:00')
            )
            
            # 检查是否超过7天
            expiry_time = created_at + timedelta(days=7)
            return timezone.now() > expiry_time
        except Exception:
            return True
    
    def set_user_cookie(self, response, user, max_age=None):
        """设置用户信息cookie"""
        try:
            user_data = self.create_user_cookie_data(user)
            if not user_data:
                return False
            
            cookie_value = self.encode_cookie_value(user_data)
            if not cookie_value:
                return False
            
            response.set_cookie(
                self.USER_INFO_COOKIE,
                cookie_value,
                max_age=max_age or self.DEFAULT_MAX_AGE,
                httponly=True,
                secure=getattr(settings, 'SECURE_SSL_REDIRECT', False),
                samesite='Lax'
            )
            return True
        except Exception:
            return False
    
    def set_token_cookie(self, response, token, max_age=None):
        """设置token cookie"""
        try:
            response.set_cookie(
                self.TOKEN_COOKIE,
                token,
                max_age=max_age or self.DEFAULT_MAX_AGE,
                httponly=True,
                secure=getattr(settings, 'SECURE_SSL_REDIRECT', False),
                samesite='Lax'
            )
            return True
        except Exception:
            return False
    
    def get_user_from_cookie(self, request):
        """从cookie获取用户信息"""
        try:
            cookie_value = request.COOKIES.get(self.USER_INFO_COOKIE)
            if not cookie_value:
                return None
            
            user_data = self.decode_cookie_value(cookie_value)
            return user_data
        except Exception:
            return None
    
    def get_token_from_cookie(self, request):
        """从cookie获取token"""
        try:
            return request.COOKIES.get(self.TOKEN_COOKIE)
        except Exception:
            return None
    
    def clear_cookies(self, response):
        """清除所有认证相关的cookie"""
        response.delete_cookie(self.USER_INFO_COOKIE)
        response.delete_cookie(self.TOKEN_COOKIE)
    
    def refresh_user_cookie(self, response, user):
        """刷新用户cookie（更新时间戳）"""
        return self.set_user_cookie(response, user)


# 全局实例
cookie_manager = SecureCookieManager()
