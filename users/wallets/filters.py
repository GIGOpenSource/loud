"""
用户钱包过滤器
使用base基础类重构
"""

import django_filters
from decimal import Decimal
from base.filters import BaseFilterSet, TimestampFilterSet
from .models import UserWallet, WalletTransaction


class UserWalletFilterSet(TimestampFilterSet):
    """用户钱包过滤器"""
    
    # 基本过滤
    currency = django_filters.ChoiceFilter(
        choices=UserWallet.CURRENCY_CHOICES,
        help_text='货币类型过滤'
    )
    
    wallet_status = django_filters.ChoiceFilter(
        choices=UserWallet.WALLET_STATUS_CHOICES,
        help_text='钱包状态过滤'
    )
    
    is_verified = django_filters.BooleanFilter(
        help_text='是否已实名认证'
    )
    
    # 余额范围过滤
    balance_min = django_filters.NumberFilter(
        field_name='balance',
        lookup_expr='gte',
        help_text='最小余额'
    )
    
    balance_max = django_filters.NumberFilter(
        field_name='balance',
        lookup_expr='lte',
        help_text='最大余额'
    )
    
    # 余额状态过滤
    balance_status = django_filters.ChoiceFilter(
        method='filter_balance_status',
        choices=[
            ('empty', '余额为0'),
            ('low', '余额较低'),
            ('normal', '余额正常'),
            ('high', '余额较高'),
        ],
        help_text='余额状态过滤'
    )
    
    # 是否有冻结余额
    has_frozen_balance = django_filters.BooleanFilter(
        method='filter_has_frozen_balance',
        help_text='是否有冻结余额'
    )
    
    # 最近活跃过滤
    recently_active = django_filters.ChoiceFilter(
        method='filter_recently_active',
        choices=[
            ('1d', '最近1天'),
            ('1w', '最近1周'),
            ('1m', '最近1月'),
        ],
        help_text='最近活跃时间'
    )
    
    # 用户相关过滤
    user_id = django_filters.NumberFilter(
        field_name='user__id',
        help_text='用户ID'
    )
    
    username = django_filters.CharFilter(
        field_name='user__username',
        lookup_expr='icontains',
        help_text='用户名'
    )
    
    class Meta:
        model = UserWallet
        fields = ['currency', 'wallet_status', 'is_verified', 'is_active']
        search_fields = ['user__username', 'user__email', 'currency']
    
    def filter_balance_status(self, queryset, name, value):
        """按余额状态过滤"""
        if value == 'empty':
            return queryset.filter(balance=0)
        elif value == 'low':
            return queryset.filter(balance__gt=0, balance__lt=100)
        elif value == 'normal':
            return queryset.filter(balance__gte=100, balance__lt=1000)
        elif value == 'high':
            return queryset.filter(balance__gte=1000)
        return queryset
    
    def filter_has_frozen_balance(self, queryset, name, value):
        """按是否有冻结余额过滤"""
        if value:
            return queryset.filter(frozen_balance__gt=0)
        else:
            return queryset.filter(frozen_balance=0)
    
    def filter_recently_active(self, queryset, name, value):
        """按最近活跃时间过滤"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        if value == '1d':
            since = now - timedelta(days=1)
        elif value == '1w':
            since = now - timedelta(weeks=1)
        elif value == '1m':
            since = now - timedelta(days=30)
        else:
            return queryset
        
        return queryset.filter(last_transaction_at__gte=since)


class WalletTransactionFilterSet(TimestampFilterSet):
    """钱包交易过滤器"""
    
    # 基本过滤
    transaction_type = django_filters.ChoiceFilter(
        choices=WalletTransaction.TRANSACTION_TYPE_CHOICES,
        help_text='交易类型过滤'
    )
    
    status = django_filters.ChoiceFilter(
        choices=WalletTransaction.TRANSACTION_STATUS_CHOICES,
        help_text='交易状态过滤'
    )
    
    # 金额范围过滤
    amount_min = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='gte',
        help_text='最小金额'
    )
    
    amount_max = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='lte',
        help_text='最大金额'
    )
    
    # 收支类型过滤
    flow_type = django_filters.ChoiceFilter(
        method='filter_flow_type',
        choices=[
            ('income', '收入'),
            ('expense', '支出'),
            ('neutral', '中性'),
        ],
        help_text='资金流向过滤'
    )
    
    # 来源和目标过滤
    source = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='交易来源'
    )
    
    destination = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='交易目标'
    )
    
    reference_id = django_filters.CharFilter(
        lookup_expr='exact',
        help_text='外部参考ID'
    )
    
    # 钱包相关过滤
    wallet_id = django_filters.NumberFilter(
        field_name='wallet__id',
        help_text='钱包ID'
    )
    
    wallet_user = django_filters.CharFilter(
        field_name='wallet__user__username',
        lookup_expr='icontains',
        help_text='钱包所有者'
    )
    
    currency = django_filters.ChoiceFilter(
        field_name='wallet__currency',
        choices=UserWallet.CURRENCY_CHOICES,
        help_text='货币类型'
    )
    
    # 时间范围过滤（更细粒度）
    date_range = django_filters.ChoiceFilter(
        method='filter_date_range',
        choices=[
            ('today', '今天'),
            ('yesterday', '昨天'),
            ('this_week', '本周'),
            ('last_week', '上周'),
            ('this_month', '本月'),
            ('last_month', '上月'),
            ('this_year', '今年'),
        ],
        help_text='时间范围过滤'
    )
    
    # 是否可退款
    can_refund = django_filters.BooleanFilter(
        method='filter_can_refund',
        help_text='是否可退款'
    )
    
    class Meta:
        model = WalletTransaction
        fields = ['transaction_type', 'status', 'wallet']
        search_fields = ['description', 'source', 'destination', 'reference_id']
    
    def filter_flow_type(self, queryset, name, value):
        """按资金流向过滤"""
        if value == 'income':
            income_types = ['deposit', 'transfer_in', 'refund', 'reward']
            return queryset.filter(transaction_type__in=income_types)
        elif value == 'expense':
            expense_types = ['withdraw', 'transfer_out', 'payment', 'penalty']
            return queryset.filter(transaction_type__in=expense_types)
        elif value == 'neutral':
            neutral_types = ['freeze', 'unfreeze', 'freeze_wallet', 'unfreeze_wallet', 'adjustment']
            return queryset.filter(transaction_type__in=neutral_types)
        return queryset
    
    def filter_date_range(self, queryset, name, value):
        """按时间范围过滤"""
        from base.utils import DateUtils
        from django.utils import timezone
        
        today = timezone.now().date()
        
        if value == 'today':
            return queryset.filter(created_at__date=today)
        elif value == 'yesterday':
            yesterday = today - timezone.timedelta(days=1)
            return queryset.filter(created_at__date=yesterday)
        elif value in ['this_week', 'last_week', 'this_month', 'last_month']:
            start_date, end_date = DateUtils.get_date_range(value, today)
            return queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
        elif value == 'this_year':
            year_start = today.replace(month=1, day=1)
            return queryset.filter(created_at__date__gte=year_start)
        
        return queryset
    
    def filter_can_refund(self, queryset, name, value):
        """按是否可退款过滤"""
        if value:
            from django.utils import timezone
            refundable_types = ['payment']
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            
            return queryset.filter(
                transaction_type__in=refundable_types,
                status='completed',
                created_at__gte=thirty_days_ago
            )
        else:
            return queryset.exclude(
                transaction_type='payment',
                status='completed'
            )


class WalletStatisticsFilterSet(django_filters.FilterSet):
    """钱包统计过滤器"""
    
    period = django_filters.ChoiceFilter(
        method='filter_period',
        choices=[
            ('daily', '按日统计'),
            ('weekly', '按周统计'),
            ('monthly', '按月统计'),
            ('yearly', '按年统计'),
        ],
        help_text='统计周期'
    )
    
    start_date = django_filters.DateFilter(
        method='filter_start_date',
        help_text='开始日期'
    )
    
    end_date = django_filters.DateFilter(
        method='filter_end_date',
        help_text='结束日期'
    )
    
    def filter_period(self, queryset, name, value):
        """按统计周期过滤"""
        # 这里可以根据需要实现不同的统计逻辑
        return queryset
    
    def filter_start_date(self, queryset, name, value):
        """按开始日期过滤"""
        return queryset.filter(created_at__date__gte=value)
    
    def filter_end_date(self, queryset, name, value):
        """按结束日期过滤"""
        return queryset.filter(created_at__date__lte=value)
