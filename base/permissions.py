"""
基础权限类
提供标准化的权限控制功能
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class BasePermission(permissions.BasePermission):
    """
    基础权限类
    提供通用的权限控制逻辑
    """
    
    # 权限代码
    permission_code = None
    
    # 错误消息
    message = "您没有执行此操作的权限"
    
    def has_permission(self, request, view):
        """检查用户是否有权限"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 超级用户始终有权限
        if request.user.is_superuser:
            return True
        
        # 检查用户是否激活
        if not request.user.is_active:
            return False
        
        # 检查具体权限
        if self.permission_code:
            return self.check_permission(request.user, self.permission_code)
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """检查对象级权限"""
        # 首先检查基本权限
        if not self.has_permission(request, view):
            return False
        
        # 检查对象级权限
        return self.check_object_permission(request.user, obj)
    
    def check_permission(self, user, permission_code):
        """检查用户权限"""
        if hasattr(user, 'has_permission'):
            return user.has_permission(permission_code)
        
        # 回退到Django默认权限
        return user.has_perm(permission_code)
    
    def check_object_permission(self, user, obj):
        """检查对象级权限，子类可重写"""
        return True


class IsOwnerOrReadOnly(BasePermission):
    """
    所有者权限或只读
    只有对象的所有者才能修改，其他人只能读取
    """
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        # 读权限对所有人开放
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写权限只给所有者
        return self.is_owner(request.user, obj)
    
    def is_owner(self, user, obj):
        """判断用户是否是对象的所有者"""
        # 检查常见的所有者字段
        owner_fields = ['user', 'owner', 'created_by', 'author']
        
        for field in owner_fields:
            if hasattr(obj, field):
                owner = getattr(obj, field)
                if owner == user:
                    return True
        
        return False


class IsOwnerOrAdmin(BasePermission):
    """
    所有者或管理员权限
    """
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        user = request.user
        
        # 管理员有所有权限
        if user.is_staff or user.is_superuser:
            return True
        
        # 检查是否是所有者
        return self.is_owner(user, obj)
    
    def is_owner(self, user, obj):
        """判断用户是否是对象的所有者"""
        owner_fields = ['user', 'owner', 'created_by', 'author']
        
        for field in owner_fields:
            if hasattr(obj, field):
                owner = getattr(obj, field)
                if owner == user:
                    return True
        
        return False


class RoleBasedPermission(BasePermission):
    """
    基于角色的权限
    """
    
    # 需要的角色列表
    required_roles = []
    
    def has_permission(self, request, view):
        """检查角色权限"""
        if not super().has_permission(request, view):
            return False
        
        # 检查用户角色
        user = request.user
        if hasattr(user, 'has_any_role') and self.required_roles:
            return user.has_any_role(self.required_roles)
        
        return True


class ActionBasedPermission(BasePermission):
    """
    基于动作的权限
    根据不同的动作应用不同的权限
    """
    
    # 动作权限映射
    action_permissions = {}
    
    def has_permission(self, request, view):
        """检查动作权限"""
        if not super().has_permission(request, view):
            return False
        
        # 获取当前动作
        action = getattr(view, 'action', None)
        if not action:
            return True
        
        # 检查动作权限
        permission_code = self.action_permissions.get(action)
        if permission_code:
            return self.check_permission(request.user, permission_code)
        
        return True


class TimeBasedPermission(BasePermission):
    """
    基于时间的权限
    在特定时间段内才有权限
    """
    
    # 允许的时间段（小时）
    allowed_hours = None  # 例如：[9, 10, 11, 12, 13, 14, 15, 16, 17]
    
    # 允许的星期几
    allowed_weekdays = None  # 例如：[0, 1, 2, 3, 4] (周一到周五)
    
    def has_permission(self, request, view):
        """检查时间权限"""
        if not super().has_permission(request, view):
            return False
        
        now = timezone.now()
        
        # 检查小时限制
        if self.allowed_hours and now.hour not in self.allowed_hours:
            self.message = "当前时间不允许执行此操作"
            return False
        
        # 检查星期限制
        if self.allowed_weekdays and now.weekday() not in self.allowed_weekdays:
            self.message = "当前日期不允许执行此操作"
            return False
        
        return True


class RateLimitPermission(BasePermission):
    """
    基于频率限制的权限
    限制用户在一定时间内的操作次数
    """
    
    # 限制配置
    rate_limit = '100/hour'  # 格式：次数/时间单位
    
    def has_permission(self, request, view):
        """检查频率限制"""
        if not super().has_permission(request, view):
            return False
        
        # 这里可以集成Redis或其他缓存来实现频率限制
        # 简单示例，实际项目中建议使用专门的限流库
        return self.check_rate_limit(request.user)
    
    def check_rate_limit(self, user):
        """检查频率限制"""
        # 实现频率限制逻辑
        # 这里只是示例，实际需要根据项目需求实现
        return True


class IPBasedPermission(BasePermission):
    """
    基于IP的权限
    只允许特定IP访问
    """
    
    # 允许的IP列表
    allowed_ips = []
    
    # 禁止的IP列表
    blocked_ips = []
    
    def has_permission(self, request, view):
        """检查IP权限"""
        if not super().has_permission(request, view):
            return False
        
        ip = self.get_client_ip(request)
        
        # 检查禁止IP
        if self.blocked_ips and ip in self.blocked_ips:
            self.message = "您的IP地址被禁止访问"
            return False
        
        # 检查允许IP
        if self.allowed_ips and ip not in self.allowed_ips:
            self.message = "您的IP地址没有访问权限"
            return False
        
        return True
    
    def get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CRUDPermission(BasePermission):
    """
    CRUD操作权限
    为不同的CRUD操作设置不同的权限
    """
    
    # CRUD权限映射
    permission_map = {
        'GET': None,      # 读权限
        'POST': None,     # 创建权限
        'PUT': None,      # 更新权限
        'PATCH': None,    # 部分更新权限
        'DELETE': None,   # 删除权限
    }
    
    def has_permission(self, request, view):
        """检查CRUD权限"""
        if not super().has_permission(request, view):
            return False
        
        # 获取请求方法对应的权限
        permission_code = self.permission_map.get(request.method)
        if permission_code:
            return self.check_permission(request.user, permission_code)
        
        return True


class DjangoModelPermission(permissions.DjangoModelPermissions):
    """
    增强的Django模型权限
    """
    
    # 权限映射
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
    
    def has_permission(self, request, view):
        """检查Django模型权限"""
        # 添加读权限检查
        if request.method == 'GET':
            model_cls = getattr(view, 'queryset', None)
            if model_cls is None:
                model_cls = getattr(view, 'model', None)
            
            if model_cls:
                app_label = model_cls._meta.app_label
                model_name = model_cls._meta.model_name
                view_perm = f"{app_label}.view_{model_name}"
                
                if not request.user.has_perm(view_perm):
                    return False
        
        return super().has_permission(request, view)


class CompositePermission(BasePermission):
    """
    复合权限
    组合多个权限类
    """
    
    # 权限类列表
    permission_classes = []
    
    # 权限逻辑：'and' 或 'or'
    permission_logic = 'and'
    
    def has_permission(self, request, view):
        """检查复合权限"""
        if not self.permission_classes:
            return True
        
        permissions = [perm() for perm in self.permission_classes]
        results = [perm.has_permission(request, view) for perm in permissions]
        
        if self.permission_logic == 'and':
            return all(results)
        else:  # or
            return any(results)
    
    def has_object_permission(self, request, view, obj):
        """检查对象复合权限"""
        if not self.permission_classes:
            return True
        
        permissions = [perm() for perm in self.permission_classes]
        results = [perm.has_object_permission(request, view, obj) for perm in permissions]
        
        if self.permission_logic == 'and':
            return all(results)
        else:  # or
            return any(results)
