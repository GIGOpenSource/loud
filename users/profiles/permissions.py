"""
用户资料权限
使用base基础类重构
"""

from base.permissions import BasePermission, IsOwnerOrReadOnly


class UserProfilePermission(IsOwnerOrReadOnly):
    """
    用户资料权限
    用户只能管理自己的资料
    """
    
    def has_permission(self, request, view):
        """检查基础权限"""
        # 必须是认证用户
        if not request.user or not request.user.is_authenticated:
            return False
        
        return super().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        # 读权限：根据资料可见性判断
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return self.check_read_permission(request, obj)
        
        # 写权限：只有本人或管理员
        return self.is_owner(request.user, obj) or request.user.is_staff
    
    def check_read_permission(self, request, profile):
        """检查读权限"""
        # 本人和管理员可以查看任何资料
        if request.user == profile.user or request.user.is_staff:
            return True
        
        # 根据资料可见性判断
        if profile.profile_visibility == 'public':
            return True
        elif profile.profile_visibility == 'friends':
            # TODO: 这里可以集成好友系统
            return False
        else:  # private
            return False
    
    def is_owner(self, user, obj):
        """判断是否是资料所有者"""
        return obj.user == user


class UserProfileReadOnlyPermission(BasePermission):
    """
    用户资料只读权限
    用于公开资料接口
    """
    
    def has_permission(self, request, view):
        """任何人都可以查看公开资料"""
        return True
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        # 只允许读操作
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            return False
        
        # 检查资料可见性
        if obj.profile_visibility == 'public':
            return True
        elif obj.profile_visibility == 'friends':
            # 如果是认证用户且是好友
            if request.user.is_authenticated:
                # TODO: 集成好友系统
                return False
            return False
        else:  # private
            # 只有本人可以查看
            return request.user.is_authenticated and request.user == obj.user


class UserAvatarPermission(BasePermission):
    """
    用户头像权限
    """
    
    def has_permission(self, request, view):
        """必须是认证用户"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """只有本人可以管理头像"""
        return obj.user == request.user or request.user.is_staff
