"""
用户偏好权限
使用base基础类重构
"""

from base.permissions import BasePermission, IsOwnerOrReadOnly


class UserPreferencePermission(IsOwnerOrReadOnly):
    """
    用户偏好权限
    用户只能管理自己的偏好设置
    """
    
    def has_permission(self, request, view):
        """检查基础权限"""
        # 必须是认证用户
        if not request.user or not request.user.is_authenticated:
            return False
        
        return super().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        # 只有本人或管理员可以管理偏好设置
        return self.is_owner(request.user, obj) or request.user.is_staff
    
    def is_owner(self, user, obj):
        """判断是否是偏好设置的所有者"""
        return obj.user == user


class PreferenceReadOnlyPermission(BasePermission):
    """
    偏好设置只读权限
    用于管理员查看用户偏好设置
    """
    
    def has_permission(self, request, view):
        """只有管理员可以查看其他用户的偏好设置"""
        return request.user and request.user.is_authenticated and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        """只允许读操作"""
        return request.method in ['GET', 'HEAD', 'OPTIONS']


class NotificationPermission(BasePermission):
    """
    通知设置权限
    控制通知设置的修改权限
    """
    
    def has_permission(self, request, view):
        """必须是认证用户"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """只有本人可以修改通知设置"""
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            # 读权限：本人或管理员
            return obj.user == request.user or request.user.is_staff
        else:
            # 写权限：只有本人
            return obj.user == request.user
