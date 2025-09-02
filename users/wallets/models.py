"""
用户钱包模型
使用base基础类重构
"""

from decimal import Decimal
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from base.models import BaseAuditModel
from base.validators import DecimalRangeValidator


class UserWallet(BaseAuditModel):
    """
    用户钱包模型
    继承BaseAuditModel获得审计功能
    """
    
    user = models.OneToOneField(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name=_('用户')
    )
    
    # 货币类型
    CURRENCY_CHOICES = [
        ('CNY', _('人民币')),
        ('USD', _('美元')),
        ('EUR', _('欧元')),
        ('GBP', _('英镑')),
        ('JPY', _('日元')),
        ('HKD', _('港币')),
        ('TWD', _('台币')),
    ]
    
    currency = models.CharField(
        _('货币类型'),
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='CNY',
        help_text=_('钱包使用的货币类型')
    )
    
    # 余额信息
    balance = models.DecimalField(
        _('可用余额'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            RegexValidator(
                regex=r'^\d+(\.\d{1,2})?$',
                message='金额格式不正确，最多保留2位小数'
            )
        ],
        help_text=_('用户可用余额')
    )
    
    frozen_balance = models.DecimalField(
        _('冻结余额'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('被冻结的余额，不可用于消费')
    )
    
    total_income = models.DecimalField(
        _('总收入'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('历史总收入金额')
    )
    
    total_expense = models.DecimalField(
        _('总支出'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('历史总支出金额')
    )
    
    # 支付密码
    payment_password = models.CharField(
        _('支付密码'),
        max_length=128,
        blank=True,
        help_text=_('用于大额支付的安全密码')
    )
    
    payment_password_set_at = models.DateTimeField(
        _('支付密码设置时间'),
        null=True,
        blank=True,
        help_text=_('支付密码最后设置时间')
    )
    
    # 钱包状态
    WALLET_STATUS_CHOICES = [
        ('normal', _('正常')),
        ('frozen', _('冻结')),
        ('suspended', _('暂停')),
        ('closed', _('关闭')),
    ]
    
    wallet_status = models.CharField(
        _('钱包状态'),
        max_length=20,
        choices=WALLET_STATUS_CHOICES,
        default='normal',
        help_text=_('钱包的当前状态')
    )
    
    # 风控信息
    daily_limit = models.DecimalField(
        _('日限额'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('每日消费限额')
    )
    
    monthly_limit = models.DecimalField(
        _('月限额'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('100000.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('每月消费限额')
    )
    
    # 实名认证状态
    is_verified = models.BooleanField(
        _('是否已实名认证'),
        default=False,
        help_text=_('钱包是否已完成实名认证')
    )
    
    verified_at = models.DateTimeField(
        _('认证时间'),
        null=True,
        blank=True,
        help_text=_('完成实名认证的时间')
    )
    
    # 最后操作信息
    last_transaction_at = models.DateTimeField(
        _('最后交易时间'),
        null=True,
        blank=True,
        help_text=_('最后一次交易的时间')
    )
    
    class Meta:
        verbose_name = _('用户钱包')
        verbose_name_plural = _('用户钱包')
        db_table = 'user_wallets'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'currency']),
            models.Index(fields=['wallet_status']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f'{self.user.username} 的{self.get_currency_display()}钱包'
    
    @property
    def total_balance(self):
        """总余额（可用余额 + 冻结余额）"""
        return self.balance + self.frozen_balance
    
    @property
    def available_balance(self):
        """可用余额（别名，为了向后兼容）"""
        return self.balance
    
    @property
    def formatted_balance(self):
        """格式化余额显示"""
        from base.utils import NumberUtils
        return NumberUtils.format_currency(self.balance, self.currency)
    
    @property
    def formatted_total_balance(self):
        """格式化总余额显示"""
        from base.utils import NumberUtils
        return NumberUtils.format_currency(self.total_balance, self.currency)
    
    @property
    def balance_status(self):
        """余额状态"""
        if self.balance <= 0:
            return 'empty'
        elif self.balance < Decimal('100.00'):
            return 'low'
        elif self.balance < Decimal('1000.00'):
            return 'normal'
        else:
            return 'high'
    
    def clean(self):
        """模型验证"""
        super().clean()
        
        # 验证余额不能为负数
        if self.balance < 0:
            raise ValidationError({'balance': '余额不能为负数'})
        
        if self.frozen_balance < 0:
            raise ValidationError({'frozen_balance': '冻结余额不能为负数'})
        
        # 验证限额设置合理性
        if self.daily_limit > self.monthly_limit:
            raise ValidationError({'daily_limit': '日限额不能超过月限额'})
    
    def can_spend(self, amount):
        """检查是否可以消费指定金额"""
        if self.wallet_status != 'normal':
            return False, f'钱包状态异常：{self.get_wallet_status_display()}'
        
        if not self.is_active:
            return False, '钱包已被停用'
        
        if self.balance < amount:
            return False, '余额不足'
        
        return True, '可以消费'
    
    def freeze_amount(self, amount, reason=''):
        """冻结指定金额"""
        if amount <= 0:
            raise ValueError('冻结金额必须大于0')
        
        if self.balance < amount:
            raise ValueError('可用余额不足，无法冻结')
        
        with transaction.atomic():
            self.balance -= amount
            self.frozen_balance += amount
            self.save(update_fields=['balance', 'frozen_balance', 'updated_at'])
            
            # 记录冻结操作
            self.create_transaction(
                transaction_type='freeze',
                amount=amount,
                description=f'冻结金额: {reason}' if reason else '冻结金额'
            )
    
    def unfreeze_amount(self, amount, reason=''):
        """解冻指定金额"""
        if amount <= 0:
            raise ValueError('解冻金额必须大于0')
        
        if self.frozen_balance < amount:
            raise ValueError('冻结余额不足，无法解冻')
        
        with transaction.atomic():
            self.frozen_balance -= amount
            self.balance += amount
            self.save(update_fields=['balance', 'frozen_balance', 'updated_at'])
            
            # 记录解冻操作
            self.create_transaction(
                transaction_type='unfreeze',
                amount=amount,
                description=f'解冻金额: {reason}' if reason else '解冻金额'
            )
    
    def deposit(self, amount, source='manual', description='', reference_id=''):
        """充值"""
        if amount <= 0:
            raise ValueError('充值金额必须大于0')
        
        with transaction.atomic():
            self.balance += amount
            self.total_income += amount
            self.last_transaction_at = timezone.now()
            self.save(update_fields=[
                'balance', 'total_income', 'last_transaction_at', 'updated_at'
            ])
            
            # 记录充值交易
            return self.create_transaction(
                transaction_type='deposit',
                amount=amount,
                source=source,
                description=description or '账户充值',
                reference_id=reference_id
            )
    
    def withdraw(self, amount, destination='manual', description='', reference_id=''):
        """提现"""
        if amount <= 0:
            raise ValueError('提现金额必须大于0')
        
        can_spend, reason = self.can_spend(amount)
        if not can_spend:
            raise ValueError(f'无法提现: {reason}')
        
        with transaction.atomic():
            self.balance -= amount
            self.total_expense += amount
            self.last_transaction_at = timezone.now()
            self.save(update_fields=[
                'balance', 'total_expense', 'last_transaction_at', 'updated_at'
            ])
            
            # 记录提现交易
            return self.create_transaction(
                transaction_type='withdraw',
                amount=amount,
                destination=destination,
                description=description or '账户提现',
                reference_id=reference_id
            )
    
    def transfer_to(self, target_wallet, amount, description='', reference_id=''):
        """转账到其他钱包"""
        if amount <= 0:
            raise ValueError('转账金额必须大于0')
        
        if target_wallet.currency != self.currency:
            raise ValueError('货币类型不匹配，无法转账')
        
        can_spend, reason = self.can_spend(amount)
        if not can_spend:
            raise ValueError(f'无法转账: {reason}')
        
        with transaction.atomic():
            # 从源钱包扣款
            self.balance -= amount
            self.total_expense += amount
            self.last_transaction_at = timezone.now()
            self.save(update_fields=[
                'balance', 'total_expense', 'last_transaction_at', 'updated_at'
            ])
            
            # 向目标钱包充值
            target_wallet.balance += amount
            target_wallet.total_income += amount
            target_wallet.last_transaction_at = timezone.now()
            target_wallet.save(update_fields=[
                'balance', 'total_income', 'last_transaction_at', 'updated_at'
            ])
            
            # 记录转出交易
            transfer_out = self.create_transaction(
                transaction_type='transfer_out',
                amount=amount,
                destination=f'user_{target_wallet.user.id}',
                description=description or f'转账给 {target_wallet.user.username}',
                reference_id=reference_id
            )
            
            # 记录转入交易
            transfer_in = target_wallet.create_transaction(
                transaction_type='transfer_in',
                amount=amount,
                source=f'user_{self.user.id}',
                description=description or f'来自 {self.user.username} 的转账',
                reference_id=reference_id
            )
            
            return transfer_out, transfer_in
    
    def create_transaction(self, transaction_type, amount, **kwargs):
        """创建交易记录"""
        from .models import WalletTransaction
        
        return WalletTransaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=self.balance,
            **kwargs
        )
    
    def get_daily_spent(self, date=None):
        """获取指定日期的消费金额"""
        if not date:
            date = timezone.now().date()
        
        from .models import WalletTransaction
        
        daily_transactions = WalletTransaction.objects.filter(
            wallet=self,
            transaction_type__in=['withdraw', 'transfer_out', 'payment'],
            created_at__date=date
        )
        
        return sum(t.amount for t in daily_transactions)
    
    def get_monthly_spent(self, year=None, month=None):
        """获取指定月份的消费金额"""
        now = timezone.now()
        if not year:
            year = now.year
        if not month:
            month = now.month
        
        from .models import WalletTransaction
        
        monthly_transactions = WalletTransaction.objects.filter(
            wallet=self,
            transaction_type__in=['withdraw', 'transfer_out', 'payment'],
            created_at__year=year,
            created_at__month=month
        )
        
        return sum(t.amount for t in monthly_transactions)
    
    def set_payment_password(self, password):
        """设置支付密码"""
        from django.contrib.auth.hashers import make_password
        
        self.payment_password = make_password(password)
        self.payment_password_set_at = timezone.now()
        self.save(update_fields=['payment_password', 'payment_password_set_at', 'updated_at'])
    
    def check_payment_password(self, password):
        """验证支付密码"""
        if not self.payment_password:
            return False
        
        from django.contrib.auth.hashers import check_password
        return check_password(password, self.payment_password)
    
    def verify_wallet(self):
        """完成钱包实名认证"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at', 'updated_at'])
    
    def freeze_wallet(self, reason=''):
        """冻结钱包"""
        self.wallet_status = 'frozen'
        self.save(update_fields=['wallet_status', 'updated_at'])
        
        # 记录冻结操作
        self.create_transaction(
            transaction_type='freeze_wallet',
            amount=Decimal('0.00'),
            description=f'钱包被冻结: {reason}' if reason else '钱包被冻结'
        )
    
    def unfreeze_wallet(self, reason=''):
        """解冻钱包"""
        self.wallet_status = 'normal'
        self.save(update_fields=['wallet_status', 'updated_at'])
        
        # 记录解冻操作
        self.create_transaction(
            transaction_type='unfreeze_wallet',
            amount=Decimal('0.00'),
            description=f'钱包被解冻: {reason}' if reason else '钱包被解冻'
        )


class WalletTransaction(BaseAuditModel):
    """
    钱包交易记录模型
    记录所有钱包相关的交易
    """
    
    wallet = models.ForeignKey(
        UserWallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('钱包')
    )
    
    # 交易类型
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', _('充值')),
        ('withdraw', _('提现')),
        ('transfer_in', _('转入')),
        ('transfer_out', _('转出')),
        ('payment', _('支付')),
        ('refund', _('退款')),
        ('freeze', _('冻结')),
        ('unfreeze', _('解冻')),
        ('freeze_wallet', _('冻结钱包')),
        ('unfreeze_wallet', _('解冻钱包')),
        ('adjustment', _('调账')),
        ('reward', _('奖励')),
        ('penalty', _('扣款')),
    ]
    
    transaction_type = models.CharField(
        _('交易类型'),
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text=_('交易的类型')
    )
    
    # 交易金额
    amount = models.DecimalField(
        _('交易金额'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('交易涉及的金额')
    )
    
    # 交易后余额
    balance_after = models.DecimalField(
        _('交易后余额'),
        max_digits=15,
        decimal_places=2,
        help_text=_('交易完成后的钱包余额')
    )
    
    # 交易状态
    TRANSACTION_STATUS_CHOICES = [
        ('pending', _('待处理')),
        ('processing', _('处理中')),
        ('completed', _('已完成')),
        ('failed', _('失败')),
        ('cancelled', _('已取消')),
        ('refunded', _('已退款')),
    ]
    
    status = models.CharField(
        _('交易状态'),
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='completed',
        help_text=_('交易的当前状态')
    )
    
    # 交易描述
    description = models.TextField(
        _('交易描述'),
        blank=True,
        help_text=_('交易的详细描述')
    )
    
    # 来源和目标
    source = models.CharField(
        _('交易来源'),
        max_length=100,
        blank=True,
        help_text=_('交易的来源，如支付渠道、转账用户等')
    )
    
    destination = models.CharField(
        _('交易目标'),
        max_length=100,
        blank=True,
        help_text=_('交易的目标，如提现渠道、转账用户等')
    )
    
    # 外部参考ID
    reference_id = models.CharField(
        _('外部参考ID'),
        max_length=100,
        blank=True,
        help_text=_('外部系统的交易ID或订单ID')
    )
    
    # 交易手续费
    fee = models.DecimalField(
        _('手续费'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('交易产生的手续费')
    )
    
    # 附加数据
    metadata = models.JSONField(
        _('附加数据'),
        default=dict,
        blank=True,
        help_text=_('交易相关的附加信息')
    )
    
    class Meta:
        verbose_name = _('钱包交易')
        verbose_name_plural = _('钱包交易')
        db_table = 'wallet_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'transaction_type']),
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['reference_id']),
        ]
    
    def __str__(self):
        return f'{self.wallet.user.username} - {self.get_transaction_type_display()} - {self.amount}'
    
    @property
    def formatted_amount(self):
        """格式化金额显示"""
        from base.utils import NumberUtils
        return NumberUtils.format_currency(self.amount, self.wallet.currency)
    
    @property
    def is_income(self):
        """是否是收入类交易"""
        income_types = ['deposit', 'transfer_in', 'refund', 'reward']
        return self.transaction_type in income_types
    
    @property
    def is_expense(self):
        """是否是支出类交易"""
        expense_types = ['withdraw', 'transfer_out', 'payment', 'penalty']
        return self.transaction_type in expense_types
    
    def can_refund(self):
        """检查是否可以退款"""
        refundable_types = ['payment']
        return (
            self.transaction_type in refundable_types and
            self.status == 'completed' and
            self.created_at >= timezone.now() - timezone.timedelta(days=30)  # 30天内
        )
    
    def process_refund(self, reason=''):
        """处理退款"""
        if not self.can_refund():
            raise ValueError('该交易不支持退款')
        
        with transaction.atomic():
            # 退款到原钱包
            self.wallet.balance += self.amount
            self.wallet.total_income += self.amount
            self.wallet.last_transaction_at = timezone.now()
            self.wallet.save(update_fields=[
                'balance', 'total_income', 'last_transaction_at', 'updated_at'
            ])
            
            # 更新原交易状态
            self.status = 'refunded'
            self.save(update_fields=['status', 'updated_at'])
            
            # 创建退款交易记录
            return self.wallet.create_transaction(
                transaction_type='refund',
                amount=self.amount,
                description=f'退款: {reason}' if reason else f'退款 (原交易: {self.id})',
                reference_id=str(self.id)
            )
