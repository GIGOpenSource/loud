"""
用户钱包序列化器
使用base基础类重构
"""

from rest_framework import serializers
from decimal import Decimal
from base.serializers import BaseModelSerializer, BaseListSerializer, BaseCreateSerializer, BaseUpdateSerializer
from .models import UserWallet, WalletTransaction


class UserWalletSerializer(BaseModelSerializer):
    """用户钱包序列化器"""
    
    total_balance = serializers.ReadOnlyField()
    available_balance = serializers.ReadOnlyField()
    formatted_balance = serializers.ReadOnlyField()
    formatted_total_balance = serializers.ReadOnlyField()
    balance_status = serializers.ReadOnlyField()
    currency_display = serializers.SerializerMethodField()
    wallet_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserWallet
        fields = [
            'id', 'user', 'currency', 'currency_display',
            'balance', 'frozen_balance', 'total_balance', 'available_balance',
            'formatted_balance', 'formatted_total_balance', 'balance_status',
            'total_income', 'total_expense', 'wallet_status', 'wallet_status_display',
            'daily_limit', 'monthly_limit', 'is_verified', 'verified_at',
            'last_transaction_at', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'total_income', 'total_expense', 'verified_at',
            'last_transaction_at', 'created_at', 'updated_at'
        ]
    
    def get_currency_display(self, obj):
        """获取货币类型显示名称"""
        return obj.get_currency_display()
    
    def get_wallet_status_display(self, obj):
        """获取钱包状态显示名称"""
        return obj.get_wallet_status_display()
    
    def validate_balance(self, value):
        """验证余额"""
        return self.validate_non_negative_number(value, '余额')
    
    def validate_frozen_balance(self, value):
        """验证冻结余额"""
        return self.validate_non_negative_number(value, '冻结余额')
    
    def validate_daily_limit(self, value):
        """验证日限额"""
        value = self.validate_positive_number(value, '日限额')
        
        # 检查是否超过合理范围
        if value > Decimal('1000000.00'):  # 100万
            raise serializers.ValidationError('日限额不能超过100万')
        
        return value
    
    def validate_monthly_limit(self, value):
        """验证月限额"""
        value = self.validate_positive_number(value, '月限额')
        
        # 检查是否超过合理范围
        if value > Decimal('10000000.00'):  # 1000万
            raise serializers.ValidationError('月限额不能超过1000万')
        
        return value
    
    def validate_business_rules(self, attrs):
        """业务规则验证"""
        # 验证限额设置合理性
        daily_limit = attrs.get('daily_limit')
        monthly_limit = attrs.get('monthly_limit')
        
        if daily_limit and monthly_limit and daily_limit > monthly_limit:
            raise serializers.ValidationError({'daily_limit': '日限额不能超过月限额'})


class UserWalletListSerializer(BaseListSerializer):
    """用户钱包列表序列化器"""
    
    formatted_balance = serializers.ReadOnlyField()
    balance_status = serializers.ReadOnlyField()
    currency_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserWallet
        fields = [
            'id', 'currency', 'currency_display', 'formatted_balance',
            'balance_status', 'wallet_status', 'is_verified', 'updated_at'
        ]
    
    def get_currency_display(self, obj):
        return obj.get_currency_display()


class UserWalletCreateSerializer(BaseCreateSerializer):
    """用户钱包创建序列化器"""
    
    class Meta:
        model = UserWallet
        fields = ['currency', 'daily_limit', 'monthly_limit']


class UserWalletUpdateSerializer(BaseUpdateSerializer):
    """用户钱包更新序列化器"""
    
    class Meta:
        model = UserWallet
        fields = ['daily_limit', 'monthly_limit']


class WalletTransactionSerializer(BaseModelSerializer):
    """钱包交易序列化器"""
    
    formatted_amount = serializers.ReadOnlyField()
    transaction_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    is_income = serializers.ReadOnlyField()
    is_expense = serializers.ReadOnlyField()
    can_refund = serializers.ReadOnlyField()
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'transaction_type', 'transaction_type_display',
            'amount', 'formatted_amount', 'balance_after', 'status', 'status_display',
            'description', 'source', 'destination', 'reference_id', 'fee',
            'metadata', 'is_income', 'is_expense', 'can_refund',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'wallet', 'balance_after', 'created_at', 'updated_at'
        ]
    
    def get_transaction_type_display(self, obj):
        """获取交易类型显示名称"""
        return obj.get_transaction_type_display()
    
    def get_status_display(self, obj):
        """获取状态显示名称"""
        return obj.get_status_display()


class WalletTransactionListSerializer(BaseListSerializer):
    """钱包交易列表序列化器"""
    
    formatted_amount = serializers.ReadOnlyField()
    transaction_type_display = serializers.SerializerMethodField()
    is_income = serializers.ReadOnlyField()
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'formatted_amount', 'is_income', 'description', 'created_at'
        ]
    
    def get_transaction_type_display(self, obj):
        return obj.get_transaction_type_display()


class WalletOperationSerializer(BaseModelSerializer):
    """钱包操作序列化器"""
    
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text='操作金额'
    )
    description = serializers.CharField(
        max_length=200,
        required=False,
        help_text='操作描述'
    )
    password = serializers.CharField(
        max_length=128,
        write_only=True,
        required=False,
        help_text='支付密码（大额操作需要）'
    )
    
    class Meta:
        model = UserWallet
        fields = ['amount', 'description', 'password']
    
    def validate_amount(self, value):
        """验证操作金额"""
        # 检查金额精度
        if value.as_tuple().exponent < -2:
            raise serializers.ValidationError('金额最多保留2位小数')
        
        # 检查金额范围
        if value > Decimal('1000000.00'):  # 100万
            raise serializers.ValidationError('单次操作金额不能超过100万')
        
        return value


class DepositSerializer(WalletOperationSerializer):
    """充值序列化器"""
    
    source = serializers.CharField(
        max_length=100,
        required=False,
        default='manual',
        help_text='充值来源'
    )
    
    class Meta(WalletOperationSerializer.Meta):
        fields = WalletOperationSerializer.Meta.fields + ['source']


class WithdrawSerializer(WalletOperationSerializer):
    """提现序列化器"""
    
    destination = serializers.CharField(
        max_length=100,
        required=False,
        default='manual',
        help_text='提现目标'
    )
    
    class Meta(WalletOperationSerializer.Meta):
        fields = WalletOperationSerializer.Meta.fields + ['destination']
    
    def validate(self, attrs):
        """验证提现操作"""
        attrs = super().validate(attrs)
        
        # 大额提现需要支付密码
        amount = attrs.get('amount')
        password = attrs.get('password')
        
        if amount and amount > Decimal('1000.00') and not password:
            raise serializers.ValidationError('大额提现需要输入支付密码')
        
        return attrs


class TransferSerializer(WalletOperationSerializer):
    """转账序列化器"""
    
    target_user_id = serializers.IntegerField(
        help_text='目标用户ID'
    )
    
    class Meta(WalletOperationSerializer.Meta):
        fields = WalletOperationSerializer.Meta.fields + ['target_user_id']
    
    def validate_target_user_id(self, value):
        """验证目标用户"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        try:
            target_user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('目标用户不存在')
        
        # 检查是否是自己
        request = self.context.get('request')
        if request and request.user.id == value:
            raise serializers.ValidationError('不能转账给自己')
        
        return value
    
    def validate(self, attrs):
        """验证转账操作"""
        attrs = super().validate(attrs)
        
        # 转账需要支付密码
        password = attrs.get('password')
        if not password:
            raise serializers.ValidationError('转账需要输入支付密码')
        
        return attrs


class FreezeSerializer(WalletOperationSerializer):
    """冻结序列化器"""
    
    reason = serializers.CharField(
        max_length=200,
        required=False,
        help_text='冻结原因'
    )
    
    class Meta(WalletOperationSerializer.Meta):
        fields = ['amount', 'reason']


class PaymentPasswordSerializer(serializers.Serializer):
    """支付密码序列化器"""
    
    password = serializers.CharField(
        max_length=128,
        min_length=6,
        help_text='支付密码，6-20位'
    )
    confirm_password = serializers.CharField(
        max_length=128,
        help_text='确认密码'
    )
    
    def validate(self, attrs):
        """验证密码"""
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        
        if password != confirm_password:
            raise serializers.ValidationError('两次输入的密码不一致')
        
        # 密码强度验证
        if len(password) < 6:
            raise serializers.ValidationError('密码长度至少6位')
        
        if password.isdigit():
            raise serializers.ValidationError('密码不能全为数字')
        
        return attrs


class WalletStatsSerializer(BaseModelSerializer):
    """钱包统计序列化器"""
    
    daily_spent = serializers.SerializerMethodField()
    monthly_spent = serializers.SerializerMethodField()
    daily_remaining = serializers.SerializerMethodField()
    monthly_remaining = serializers.SerializerMethodField()
    recent_transactions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserWallet
        fields = [
            'total_income', 'total_expense', 'daily_limit', 'monthly_limit',
            'daily_spent', 'monthly_spent', 'daily_remaining', 'monthly_remaining',
            'recent_transactions_count'
        ]
    
    def get_daily_spent(self, obj):
        """获取今日消费"""
        return obj.get_daily_spent()
    
    def get_monthly_spent(self, obj):
        """获取本月消费"""
        return obj.get_monthly_spent()
    
    def get_daily_remaining(self, obj):
        """获取今日剩余限额"""
        return obj.daily_limit - obj.get_daily_spent()
    
    def get_monthly_remaining(self, obj):
        """获取本月剩余限额"""
        return obj.monthly_limit - obj.get_monthly_spent()
    
    def get_recent_transactions_count(self, obj):
        """获取最近7天交易次数"""
        from django.utils import timezone
        from datetime import timedelta
        
        week_ago = timezone.now() - timedelta(days=7)
        return obj.transactions.filter(created_at__gte=week_ago).count()
