"""
用户钱包权限
使用base基础类重构
"""

from base.permissions import BasePermission, IsOwnerOrReadOnly


class UserWalletPermission(IsOwnerOrReadOnly):
    """
    用户钱包权限
    用户只能管理自己的钱包
    """
    
    def has_permission(self, request, view):
        """检查基础权限"""
        # 必须是认证用户
        if not request.user or not request.user.is_authenticated:
            return False
        
        return super().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        # 只有本人或管理员可以管理钱包
        return self.is_owner(request.user, obj) or request.user.is_staff
    
    def is_owner(self, user, obj):
        """判断是否是钱包所有者"""
        return obj.user == user


class WalletTransactionPermission(BasePermission):
    """
    钱包交易权限
    控制交易记录的访问权限
    """
    
    def has_permission(self, request, view):
        """检查基础权限"""
        # 必须是认证用户
        if not request.user or not request.user.is_authenticated:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        # 只有钱包所有者或管理员可以查看交易记录
        if request.user.is_staff:
            return True
        
        return obj.wallet.user == request.user


class WalletOperationPermission(BasePermission):
    """
    钱包操作权限
    控制充值、提现、转账等操作的权限
    """
    
    def has_permission(self, request, view):
        """检查基础权限"""
        # 必须是认证用户
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 检查用户账户状态
        if not request.user.is_active:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        # 只有钱包所有者可以进行操作
        if obj.user != request.user:
            return False
        
        # 检查钱包状态
        if obj.wallet_status != 'normal':
            return False
        
        # 检查钱包是否激活
        if not obj.is_active:
            return False
        
        return True


class HighAmountOperationPermission(WalletOperationPermission):
    """
    大额操作权限
    对大额操作进行额外的权限控制
    """
    
    # 大额操作阈值
    HIGH_AMOUNT_THRESHOLD = 10000.00
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        if not super().has_object_permission(request, view, obj):
            return False
        
        # 检查是否是大额操作
        amount = request.data.get('amount', 0)
        if float(amount) >= self.HIGH_AMOUNT_THRESHOLD:
            # 大额操作需要实名认证
            if not obj.is_verified:
                return False
            
            # 大额操作需要支付密码
            if not obj.payment_password:
                return False
        
        return True


class AdminWalletPermission(BasePermission):
    """
    管理员钱包权限
    管理员可以管理所有钱包
    """
    
    def has_permission(self, request, view):
        """只有管理员有权限"""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )
    
    def has_object_permission(self, request, view, obj):
        """管理员有所有权限"""
        return request.user.is_staff


class RefundPermission(BasePermission):
    """
    退款权限
    控制退款操作的权限
    """
    
    def has_permission(self, request, view):
        """检查基础权限"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        # 只有交易相关的用户可以申请退款
        if obj.wallet.user != request.user:
            return False
        
        # 检查交易是否支持退款
        if not obj.can_refund():
            return False
        
        return True
