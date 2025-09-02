"""
用户钱包视图
使用base基础类重构
"""

from rest_framework import status, permissions
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction

from base.views import BaseModelViewSet, BaseRetrieveUpdateAPIView
from base.pagination import BasePagination
from base.permissions import IsOwnerOrReadOnly
from utils.response import BaseApiResponse
from utils.decorators import log_api_call, handle_exceptions

from .models import UserWallet, WalletTransaction
from .serializers import (
    UserWalletSerializer, UserWalletListSerializer,
    UserWalletCreateSerializer, UserWalletUpdateSerializer,
    WalletTransactionSerializer, WalletTransactionListSerializer,
    DepositSerializer, WithdrawSerializer, TransferSerializer,
    FreezeSerializer, PaymentPasswordSerializer, WalletStatsSerializer
)
from .permissions import UserWalletPermission, WalletTransactionPermission
from .filters import UserWalletFilterSet, WalletTransactionFilterSet

User = get_user_model()


class UserWalletViewSet(BaseModelViewSet):
    """
    用户钱包视图集
    提供完整的钱包管理功能
    """
    queryset = UserWallet.objects.select_related('user').all()
    serializer_class = UserWalletSerializer
    list_serializer_class = UserWalletListSerializer
    create_serializer_class = UserWalletCreateSerializer
    update_serializer_class = UserWalletUpdateSerializer
    
    permission_classes = [permissions.IsAuthenticated, UserWalletPermission]
    pagination_class = BasePagination
    filterset_class = UserWalletFilterSet
    
    search_fields = ['user__username', 'user__email', 'currency']
    ordering_fields = ['created_at', 'updated_at', 'balance', 'last_transaction_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 普通用户只能管理自己的钱包
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def perform_create_pre(self, serializer):
        """创建前设置用户"""
        serializer.validated_data['user'] = self.request.user
    
    def perform_create_post(self, instance, serializer):
        """创建后的业务逻辑"""
        # 清除用户相关缓存
        self.clear_user_cache(instance.user)
        
        # 记录日志
        self.log_wallet_action('created', instance)
    
    def perform_update_post(self, instance, serializer):
        """更新后的业务逻辑"""
        # 清除用户相关缓存
        self.clear_user_cache(instance.user)
        
        # 记录更新的字段
        updated_fields = list(serializer.validated_data.keys())
        self.log_wallet_action('updated', instance, extra_data={'fields': updated_fields})
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """获取当前用户的钱包"""
        wallet, created = UserWallet.objects.get_or_create(
            user=request.user,
            defaults={'currency': 'CNY'}
        )
        
        serializer = self.get_serializer(wallet)
        message = '获取钱包信息成功'
        if created:
            message = '首次创建钱包成功'
        
        return BaseApiResponse.success(
            data=serializer.data,
            message=message
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def deposit(self, request, pk=None):
        """充值"""
        wallet = self.get_object()
        serializer = DepositSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            source = serializer.validated_data.get('source', 'manual')
            description = serializer.validated_data.get('description', '')
            
            try:
                transaction_record = wallet.deposit(
                    amount=amount,
                    source=source,
                    description=description
                )
                
                # 返回更新后的钱包信息和交易记录
                wallet_serializer = self.get_serializer(wallet)
                transaction_serializer = WalletTransactionSerializer(transaction_record)
                
                return BaseApiResponse.success(
                    data={
                        'wallet': wallet_serializer.data,
                        'transaction': transaction_serializer.data
                    },
                    message=f'充值成功，金额：{amount}'
                )
            
            except ValueError as e:
                return BaseApiResponse.error(message=str(e))
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='充值失败'
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def withdraw(self, request, pk=None):
        """提现"""
        wallet = self.get_object()
        serializer = WithdrawSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            destination = serializer.validated_data.get('destination', 'manual')
            description = serializer.validated_data.get('description', '')
            password = serializer.validated_data.get('password')
            
            # 验证支付密码（如果需要）
            if password and not wallet.check_payment_password(password):
                return BaseApiResponse.error(message='支付密码错误')
            
            try:
                transaction_record = wallet.withdraw(
                    amount=amount,
                    destination=destination,
                    description=description
                )
                
                wallet_serializer = self.get_serializer(wallet)
                transaction_serializer = WalletTransactionSerializer(transaction_record)
                
                return BaseApiResponse.success(
                    data={
                        'wallet': wallet_serializer.data,
                        'transaction': transaction_serializer.data
                    },
                    message=f'提现成功，金额：{amount}'
                )
            
            except ValueError as e:
                return BaseApiResponse.error(message=str(e))
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='提现失败'
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def transfer(self, request, pk=None):
        """转账"""
        wallet = self.get_object()
        serializer = TransferSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            target_user_id = serializer.validated_data['target_user_id']
            description = serializer.validated_data.get('description', '')
            password = serializer.validated_data['password']
            
            # 验证支付密码
            if not wallet.check_payment_password(password):
                return BaseApiResponse.error(message='支付密码错误')
            
            try:
                # 获取目标用户的钱包
                target_user = get_object_or_404(User, id=target_user_id)
                target_wallet, created = UserWallet.objects.get_or_create(
                    user=target_user,
                    defaults={'currency': wallet.currency}
                )
                
                if target_wallet.currency != wallet.currency:
                    return BaseApiResponse.error(message='货币类型不匹配')
                
                # 执行转账
                transfer_out, transfer_in = wallet.transfer_to(
                    target_wallet=target_wallet,
                    amount=amount,
                    description=description
                )
                
                wallet_serializer = self.get_serializer(wallet)
                transfer_out_serializer = WalletTransactionSerializer(transfer_out)
                
                return BaseApiResponse.success(
                    data={
                        'wallet': wallet_serializer.data,
                        'transaction': transfer_out_serializer.data,
                        'target_user': target_user.username
                    },
                    message=f'转账成功，金额：{amount}，收款人：{target_user.username}'
                )
            
            except ValueError as e:
                return BaseApiResponse.error(message=str(e))
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='转账失败'
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def freeze(self, request, pk=None):
        """冻结金额"""
        wallet = self.get_object()
        serializer = FreezeSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            reason = serializer.validated_data.get('reason', '')
            
            try:
                wallet.freeze_amount(amount=amount, reason=reason)
                
                wallet_serializer = self.get_serializer(wallet)
                return BaseApiResponse.success(
                    data=wallet_serializer.data,
                    message=f'冻结成功，金额：{amount}'
                )
            
            except ValueError as e:
                return BaseApiResponse.error(message=str(e))
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='冻结失败'
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def unfreeze(self, request, pk=None):
        """解冻金额"""
        wallet = self.get_object()
        serializer = FreezeSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            reason = serializer.validated_data.get('reason', '')
            
            try:
                wallet.unfreeze_amount(amount=amount, reason=reason)
                
                wallet_serializer = self.get_serializer(wallet)
                return BaseApiResponse.success(
                    data=wallet_serializer.data,
                    message=f'解冻成功，金额：{amount}'
                )
            
            except ValueError as e:
                return BaseApiResponse.error(message=str(e))
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='解冻失败'
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    def set_payment_password(self, request, pk=None):
        """设置支付密码"""
        wallet = self.get_object()
        serializer = PaymentPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            password = serializer.validated_data['password']
            wallet.set_payment_password(password)
            
            return BaseApiResponse.success(
                data=None,
                message='支付密码设置成功'
            )
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='支付密码设置失败'
        )
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    def verify_wallet(self, request, pk=None):
        """完成钱包实名认证"""
        wallet = self.get_object()
        
        # 这里应该集成实名认证流程
        # 目前只是简单标记为已认证
        wallet.verify_wallet()
        
        wallet_serializer = self.get_serializer(wallet)
        return BaseApiResponse.success(
            data=wallet_serializer.data,
            message='钱包实名认证成功'
        )
    
    @action(detail=True, methods=['get'])
    @method_decorator(cache_page(60 * 2))  # 缓存2分钟
    def stats(self, request, pk=None):
        """获取钱包统计信息"""
        wallet = self.get_object()
        serializer = WalletStatsSerializer(wallet)
        
        return BaseApiResponse.success(
            data=serializer.data,
            message='获取统计信息成功'
        )
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """获取钱包交易记录"""
        wallet = self.get_object()
        
        # 应用过滤和分页
        queryset = wallet.transactions.all()
        
        # 应用过滤器
        filterset = WalletTransactionFilterSet(
            request.GET,
            queryset=queryset,
            request=request
        )
        queryset = filterset.qs
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = WalletTransactionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = WalletTransactionListSerializer(queryset, many=True)
        return BaseApiResponse.success(
            data=serializer.data,
            message='获取交易记录成功'
        )
    
    @action(detail=False, methods=['get'])
    def available_currencies(self, request):
        """获取支持的货币类型"""
        currencies = [
            {'value': choice[0], 'label': choice[1]}
            for choice in UserWallet.CURRENCY_CHOICES
        ]
        
        return BaseApiResponse.success(
            data=currencies,
            message='获取货币类型成功'
        )
    
    def clear_user_cache(self, user):
        """清除用户相关缓存"""
        from django.core.cache import cache
        cache_keys = [
            f'user_wallet_{user.id}',
            f'user_dashboard_{user.id}',
            f'wallet_stats_{user.id}',
        ]
        for key in cache_keys:
            cache.delete(key)
    
    def log_wallet_action(self, action, wallet, extra_data=None):
        """记录钱包操作日志"""
        import logging
        logger = logging.getLogger('business')
        
        log_data = {
            'action': action,
            'user_id': wallet.user.id,
            'wallet_id': wallet.id,
            'currency': wallet.currency,
            'balance': str(wallet.balance),
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        logger.info(f'Wallet {action}', extra=log_data)


class WalletTransactionViewSet(BaseModelViewSet):
    """
    钱包交易视图集
    提供交易记录的查询和管理
    """
    queryset = WalletTransaction.objects.select_related('wallet__user').all()
    serializer_class = WalletTransactionSerializer
    list_serializer_class = WalletTransactionListSerializer
    
    permission_classes = [permissions.IsAuthenticated, WalletTransactionPermission]
    pagination_class = BasePagination
    filterset_class = WalletTransactionFilterSet
    
    search_fields = ['description', 'source', 'destination', 'reference_id']
    ordering_fields = ['created_at', 'amount', 'transaction_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 普通用户只能查看自己的交易记录
        if not self.request.user.is_staff:
            queryset = queryset.filter(wallet__user=self.request.user)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def refund(self, request, pk=None):
        """申请退款"""
        transaction_record = self.get_object()
        
        reason = request.data.get('reason', '')
        
        try:
            refund_record = transaction_record.process_refund(reason=reason)
            
            refund_serializer = self.get_serializer(refund_record)
            return BaseApiResponse.success(
                data=refund_serializer.data,
                message='退款处理成功'
            )
        
        except ValueError as e:
            return BaseApiResponse.error(message=str(e))
    
    @action(detail=False, methods=['get'])
    def my_transactions(self, request):
        """获取当前用户的交易记录"""
        queryset = self.get_queryset().filter(wallet__user=request.user)
        
        # 应用过滤和分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return BaseApiResponse.success(
            data=serializer.data,
            message='获取交易记录成功'
        )
    
    @action(detail=False, methods=['get'])
    def transaction_summary(self, request):
        """获取交易摘要统计"""
        from django.db.models import Sum, Count
        from datetime import datetime, timedelta
        
        queryset = self.get_queryset().filter(wallet__user=request.user)
        
        # 今日交易统计
        today = datetime.now().date()
        today_transactions = queryset.filter(created_at__date=today)
        
        # 本月交易统计
        this_month = datetime.now().replace(day=1).date()
        month_transactions = queryset.filter(created_at__date__gte=this_month)
        
        summary = {
            'today': {
                'income': today_transactions.filter(
                    transaction_type__in=['deposit', 'transfer_in', 'refund']
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'expense': today_transactions.filter(
                    transaction_type__in=['withdraw', 'transfer_out', 'payment']
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'count': today_transactions.count()
            },
            'this_month': {
                'income': month_transactions.filter(
                    transaction_type__in=['deposit', 'transfer_in', 'refund']
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'expense': month_transactions.filter(
                    transaction_type__in=['withdraw', 'transfer_out', 'payment']
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'count': month_transactions.count()
            }
        }
        
        return BaseApiResponse.success(
            data=summary,
            message='获取交易摘要成功'
        )
