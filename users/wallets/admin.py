"""
用户钱包管理后台
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Sum
from .models import UserWallet, WalletTransaction


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    """用户钱包管理"""
    
    list_display = [
        'user_link', 'currency', 'formatted_balance_display', 'formatted_frozen_balance',
        'wallet_status', 'balance_status_display', 'is_verified', 'is_active', 'updated_at'
    ]
    
    list_filter = [
        'currency', 'wallet_status', 'is_verified', 'is_active',
        'created_at', 'updated_at', 'last_transaction_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'user__phone'
    ]
    
    readonly_fields = [
        'user', 'total_income', 'total_expense', 'last_transaction_at',
        'verified_at', 'payment_password_set_at', 'created_by', 'updated_by',
        'created_at', 'updated_at', 'total_balance_display', 'recent_transactions'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'currency', 'wallet_status')
        }),
        ('余额信息', {
            'fields': (
                'balance', 'frozen_balance', 'total_balance_display',
                'total_income', 'total_expense'
            )
        }),
        ('限额设置', {
            'fields': ('daily_limit', 'monthly_limit')
        }),
        ('认证信息', {
            'fields': ('is_verified', 'verified_at'),
            'classes': ('collapse',)
        }),
        ('支付设置', {
            'fields': ('payment_password_set_at',),
            'classes': ('collapse',)
        }),
        ('状态信息', {
            'fields': ('is_active', 'status', 'last_transaction_at')
        }),
        ('审计信息', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('最近交易', {
            'fields': ('recent_transactions',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-updated_at']
    
    def user_link(self, obj):
        """用户链接"""
        return format_html(
            '<a href="/admin/authentication/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = '用户'
    user_link.admin_order_field = 'user__username'
    
    def formatted_balance_display(self, obj):
        """格式化余额显示"""
        color = 'green' if obj.balance > 0 else 'red' if obj.balance < 0 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.formatted_balance
        )
    formatted_balance_display.short_description = '可用余额'
    formatted_balance_display.admin_order_field = 'balance'
    
    def formatted_frozen_balance(self, obj):
        """格式化冻结余额显示"""
        if obj.frozen_balance > 0:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}</span>',
                f'{obj.frozen_balance} {obj.currency}'
            )
        return mark_safe('<span style="color: #ccc;">无冻结</span>')
    formatted_frozen_balance.short_description = '冻结余额'
    formatted_frozen_balance.admin_order_field = 'frozen_balance'
    
    def balance_status_display(self, obj):
        """余额状态显示"""
        status = obj.balance_status
        status_colors = {
            'empty': '#ccc',
            'low': 'orange',
            'normal': 'green',
            'high': 'blue',
        }
        status_labels = {
            'empty': '余额为0',
            'low': '余额较低',
            'normal': '余额正常',
            'high': '余额充足',
        }
        
        color = status_colors.get(status, '#ccc')
        label = status_labels.get(status, status)
        
        return format_html(
            '<span style="color: {};">●</span> {}',
            color,
            label
        )
    balance_status_display.short_description = '余额状态'
    
    def total_balance_display(self, obj):
        """总余额显示"""
        return f"{obj.total_balance} {obj.currency}"
    total_balance_display.short_description = '总余额'
    
    def recent_transactions(self, obj):
        """最近交易记录"""
        transactions = obj.transactions.order_by('-created_at')[:5]
        
        if not transactions:
            return mark_safe('<span style="color: #ccc;">暂无交易记录</span>')
        
        html = '<table style="width: 100%; font-size: 12px;">'
        html += '<tr><th>时间</th><th>类型</th><th>金额</th><th>描述</th></tr>'
        
        for tx in transactions:
            type_color = 'green' if tx.is_income else 'red' if tx.is_expense else 'blue'
            html += f'''
            <tr>
                <td>{tx.created_at.strftime("%m-%d %H:%M")}</td>
                <td style="color: {type_color};">{tx.get_transaction_type_display()}</td>
                <td>{tx.amount}</td>
                <td>{tx.description[:20]}...</td>
            </tr>
            '''
        
        html += '</table>'
        return mark_safe(html)
    recent_transactions.short_description = '最近5笔交易'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related(
            'user', 'created_by', 'updated_by'
        ).prefetch_related('transactions')
    
    actions = [
        'activate_wallets', 'deactivate_wallets', 'freeze_wallets',
        'unfreeze_wallets', 'verify_wallets', 'export_wallets'
    ]
    
    def activate_wallets(self, request, queryset):
        """批量激活钱包"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'成功激活 {count} 个钱包')
    activate_wallets.short_description = '激活选中的钱包'
    
    def deactivate_wallets(self, request, queryset):
        """批量停用钱包"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'成功停用 {count} 个钱包')
    deactivate_wallets.short_description = '停用选中的钱包'
    
    def freeze_wallets(self, request, queryset):
        """批量冻结钱包"""
        count = queryset.update(wallet_status='frozen')
        self.message_user(request, f'成功冻结 {count} 个钱包')
    freeze_wallets.short_description = '冻结选中的钱包'
    
    def unfreeze_wallets(self, request, queryset):
        """批量解冻钱包"""
        count = queryset.update(wallet_status='normal')
        self.message_user(request, f'成功解冻 {count} 个钱包')
    unfreeze_wallets.short_description = '解冻选中的钱包'
    
    def verify_wallets(self, request, queryset):
        """批量认证钱包"""
        from django.utils import timezone
        count = queryset.update(is_verified=True, verified_at=timezone.now())
        self.message_user(request, f'成功认证 {count} 个钱包')
    verify_wallets.short_description = '认证选中的钱包'
    
    def export_wallets(self, request, queryset):
        """导出钱包数据"""
        # 这里可以实现导出功能
        self.message_user(request, '导出功能开发中...')
    export_wallets.short_description = '导出选中的钱包数据'


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    """钱包交易管理"""
    
    list_display = [
        'id', 'wallet_user_link', 'transaction_type', 'formatted_amount_display',
        'status', 'flow_indicator', 'description_short', 'created_at'
    ]
    
    list_filter = [
        'transaction_type', 'status', 'wallet__currency',
        'created_at', 'wallet__wallet_status'
    ]
    
    search_fields = [
        'wallet__user__username', 'description', 'source',
        'destination', 'reference_id'
    ]
    
    readonly_fields = [
        'wallet', 'balance_after', 'created_by', 'updated_by',
        'created_at', 'updated_at', 'flow_type', 'formatted_metadata'
    ]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('wallet', 'transaction_type', 'status')
        }),
        ('金额信息', {
            'fields': ('amount', 'balance_after', 'fee', 'flow_type')
        }),
        ('交易详情', {
            'fields': ('description', 'source', 'destination', 'reference_id')
        }),
        ('附加信息', {
            'fields': ('metadata', 'formatted_metadata'),
            'classes': ('collapse',)
        }),
        ('审计信息', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def wallet_user_link(self, obj):
        """钱包用户链接"""
        return format_html(
            '<a href="/admin/users/wallets/userwallet/{}/change/">{}</a>',
            obj.wallet.id,
            obj.wallet.user.username
        )
    wallet_user_link.short_description = '钱包用户'
    wallet_user_link.admin_order_field = 'wallet__user__username'
    
    def formatted_amount_display(self, obj):
        """格式化金额显示"""
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            obj.formatted_amount
        )
    formatted_amount_display.short_description = '交易金额'
    formatted_amount_display.admin_order_field = 'amount'
    
    def flow_indicator(self, obj):
        """资金流向指示器"""
        if obj.is_income:
            return format_html('<span style="color: green;">↗ 收入</span>')
        elif obj.is_expense:
            return format_html('<span style="color: red;">↘ 支出</span>')
        else:
            return format_html('<span style="color: blue;">↔ 中性</span>')
    flow_indicator.short_description = '流向'
    
    def description_short(self, obj):
        """简短描述"""
        if len(obj.description) > 30:
            return f"{obj.description[:30]}..."
        return obj.description
    description_short.short_description = '描述'
    
    def flow_type(self, obj):
        """资金流向类型"""
        if obj.is_income:
            return "收入"
        elif obj.is_expense:
            return "支出"
        else:
            return "中性"
    flow_type.short_description = '流向类型'
    
    def formatted_metadata(self, obj):
        """格式化元数据显示"""
        if not obj.metadata:
            return mark_safe('<span style="color: #ccc;">无附加数据</span>')
        
        import json
        formatted = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
        return format_html('<pre style="font-size: 12px;">{}</pre>', formatted)
    formatted_metadata.short_description = '附加数据'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related(
            'wallet__user', 'created_by', 'updated_by'
        )
    
    # 添加统计信息
    def changelist_view(self, request, extra_context=None):
        """在交易列表页面添加统计信息"""
        extra_context = extra_context or {}
        
        # 获取总统计
        queryset = self.get_queryset(request)
        
        # 计算统计数据
        stats = {
            'total_transactions': queryset.count(),
            'total_amount': queryset.aggregate(total=Sum('amount'))['total'] or 0,
            'income_amount': queryset.filter(
                transaction_type__in=['deposit', 'transfer_in', 'refund', 'reward']
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'expense_amount': queryset.filter(
                transaction_type__in=['withdraw', 'transfer_out', 'payment', 'penalty']
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        extra_context['stats'] = stats
        
        return super().changelist_view(request, extra_context)
    
    actions = [
        'mark_as_completed', 'mark_as_failed', 'export_transactions'
    ]
    
    def mark_as_completed(self, request, queryset):
        """标记为已完成"""
        count = queryset.update(status='completed')
        self.message_user(request, f'成功标记 {count} 笔交易为已完成')
    mark_as_completed.short_description = '标记为已完成'
    
    def mark_as_failed(self, request, queryset):
        """标记为失败"""
        count = queryset.update(status='failed')
        self.message_user(request, f'成功标记 {count} 笔交易为失败')
    mark_as_failed.short_description = '标记为失败'
    
    def export_transactions(self, request, queryset):
        """导出交易数据"""
        # 这里可以实现导出功能
        self.message_user(request, '导出功能开发中...')
    export_transactions.short_description = '导出选中的交易记录'


# 自定义管理后台标题
admin.site.site_header = "Loud 钱包管理系统"
admin.site.site_title = "钱包管理"
admin.site.index_title = "欢迎使用钱包管理系统"
