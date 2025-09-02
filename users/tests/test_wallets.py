"""
用户钱包子模块测试
"""

from django.urls import reverse
from rest_framework import status
from decimal import Decimal

from .base import BaseAPITestCase, TestDataFactory


class UserWalletAPITest(BaseAPITestCase):
    """用户钱包API测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
        self.wallet_data = TestDataFactory.create_wallet_data()
    
    def test_my_wallet_get(self):
        """测试获取我的钱包"""
        url = reverse('userwallet-my-wallet')
        response = self.client.get(url)
        
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertEqual(data['user'], self.user.id)
        self.assertIn('balance', data)
        self.assertIn('currency', data)
    
    def test_wallet_deposit(self):
        """测试钱包充值"""
        from users.wallets.models import UserWallet
        
        wallet = UserWallet.objects.create(user=self.user)
        
        url = reverse('userwallet-deposit', kwargs={'pk': wallet.id})
        
        deposit_data = {
            'amount': '100.00',
            'description': '测试充值',
            'source': 'test'
        }
        
        response = self.client.post(url, deposit_data, format='json')
        self.assert_api_success(response)
        
        # 验证钱包余额
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal('100.00'))
        
        # 验证交易记录
        data = response.data['data']
        self.assertIn('wallet', data)
        self.assertIn('transaction', data)
        self.assertEqual(data['transaction']['transaction_type'], 'deposit')
    
    def test_wallet_withdraw(self):
        """测试钱包提现"""
        from users.wallets.models import UserWallet
        
        wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        wallet.set_payment_password('123456')
        
        url = reverse('userwallet-withdraw', kwargs={'pk': wallet.id})
        
        withdraw_data = {
            'amount': '50.00',
            'description': '测试提现',
            'destination': 'test',
            'password': '123456'
        }
        
        response = self.client.post(url, withdraw_data, format='json')
        self.assert_api_success(response)
        
        # 验证钱包余额
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal('50.00'))
    
    def test_wallet_transfer(self):
        """测试钱包转账"""
        from users.wallets.models import UserWallet
        
        # 创建两个钱包
        wallet1 = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00'),
            currency='CNY'
        )
        wallet1.set_payment_password('123456')
        
        wallet2 = UserWallet.objects.create(
            user=self.other_user,
            currency='CNY'
        )
        
        url = reverse('userwallet-transfer', kwargs={'pk': wallet1.id})
        
        transfer_data = {
            'amount': '30.00',
            'target_user_id': self.other_user.id,
            'description': '测试转账',
            'password': '123456'
        }
        
        response = self.client.post(url, transfer_data, format='json')
        self.assert_api_success(response)
        
        # 验证钱包余额
        wallet1.refresh_from_db()
        wallet2.refresh_from_db()
        
        self.assertEqual(wallet1.balance, Decimal('70.00'))
        self.assertEqual(wallet2.balance, Decimal('30.00'))
    
    def test_wallet_freeze_unfreeze(self):
        """测试钱包冻结解冻"""
        from users.wallets.models import UserWallet
        
        wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        
        # 冻结金额
        freeze_url = reverse('userwallet-freeze', kwargs={'pk': wallet.id})
        freeze_data = {
            'amount': '30.00',
            'reason': '测试冻结'
        }
        
        response = self.client.post(freeze_url, freeze_data, format='json')
        self.assert_api_success(response)
        
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal('70.00'))
        self.assertEqual(wallet.frozen_balance, Decimal('30.00'))
        
        # 解冻金额
        unfreeze_url = reverse('userwallet-unfreeze', kwargs={'pk': wallet.id})
        unfreeze_data = {
            'amount': '20.00',
            'reason': '测试解冻'
        }
        
        response = self.client.post(unfreeze_url, unfreeze_data, format='json')
        self.assert_api_success(response)
        
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal('90.00'))
        self.assertEqual(wallet.frozen_balance, Decimal('10.00'))
    
    def test_set_payment_password(self):
        """测试设置支付密码"""
        from users.wallets.models import UserWallet
        
        wallet = UserWallet.objects.create(user=self.user)
        
        url = reverse('userwallet-set-payment-password', kwargs={'pk': wallet.id})
        
        password_data = {
            'password': 'abc123',
            'confirm_password': 'abc123'
        }
        
        response = self.client.post(url, password_data, format='json')
        self.assert_api_success(response)
        
        wallet.refresh_from_db()
        self.assertTrue(wallet.check_payment_password('abc123'))
    
    def test_wallet_stats(self):
        """测试钱包统计"""
        from users.wallets.models import UserWallet
        
        wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00'),
            total_income=Decimal('200.00'),
            total_expense=Decimal('100.00')
        )
        
        url = reverse('userwallet-stats', kwargs={'pk': wallet.id})
        
        response = self.client.get(url)
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertIn('total_income', data)
        self.assertIn('total_expense', data)
        self.assertIn('daily_spent', data)
        self.assertIn('monthly_spent', data)
    
    def test_wallet_transactions(self):
        """测试钱包交易记录"""
        from users.wallets.models import UserWallet, WalletTransaction
        
        wallet = UserWallet.objects.create(user=self.user)
        
        # 创建一些交易记录
        for i in range(3):
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='deposit',
                amount=Decimal(f'{(i + 1) * 10}.00'),
                balance_after=Decimal(f'{(i + 1) * 10}.00'),
                description=f'测试交易 {i + 1}'
            )
        
        url = reverse('userwallet-transactions', kwargs={'pk': wallet.id})
        
        response = self.client.get(url)
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 3)


class WalletTransactionAPITest(BaseAPITestCase):
    """钱包交易API测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
        
        from users.wallets.models import UserWallet, WalletTransaction
        
        self.wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        
        self.transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='payment',
            amount=Decimal('50.00'),
            balance_after=Decimal('50.00'),
            status='completed',
            description='测试支付'
        )
    
    def test_my_transactions(self):
        """测试我的交易记录"""
        url = reverse('wallettransaction-my-transactions')
        
        response = self.client.get(url)
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertIn('results', data)
        self.assertGreaterEqual(len(data['results']), 1)
    
    def test_transaction_refund(self):
        """测试交易退款"""
        url = reverse('wallettransaction-refund', kwargs={'pk': self.transaction.id})
        
        refund_data = {
            'reason': '测试退款'
        }
        
        response = self.client.post(url, refund_data, format='json')
        self.assert_api_success(response)
        
        # 验证交易状态
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, 'refunded')
        
        # 验证钱包余额
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('150.00'))
    
    def test_transaction_summary(self):
        """测试交易摘要"""
        url = reverse('wallettransaction-transaction-summary')
        
        response = self.client.get(url)
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertIn('today', data)
        self.assertIn('this_month', data)
        
        # 验证今日统计
        today_stats = data['today']
        self.assertIn('income', today_stats)
        self.assertIn('expense', today_stats)
        self.assertIn('count', today_stats)


class UserWalletValidationTest(BaseAPITestCase):
    """用户钱包验证测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
        
        from users.wallets.models import UserWallet
        
        self.wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
    
    def test_invalid_deposit_amount(self):
        """测试无效充值金额"""
        url = reverse('userwallet-deposit', kwargs={'pk': self.wallet.id})
        
        data = {'amount': '-10.00'}  # 负数金额
        
        response = self.client.post(url, data, format='json')
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_insufficient_balance_withdraw(self):
        """测试余额不足提现"""
        self.wallet.set_payment_password('123456')
        
        url = reverse('wallets-withdraw', kwargs={'pk': self.wallet.id})
        
        data = {
            'amount': '200.00',  # 超过余额
            'password': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_wrong_payment_password(self):
        """测试错误支付密码"""
        self.wallet.set_payment_password('123456')
        
        url = reverse('wallets-withdraw', kwargs={'pk': self.wallet.id})
        
        data = {
            'amount': '50.00',
            'password': 'wrong_password'
        }
        
        response = self.client.post(url, data, format='json')
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_transfer_to_self(self):
        """测试转账给自己"""
        self.wallet.set_payment_password('123456')
        
        url = reverse('wallets-transfer', kwargs={'pk': self.wallet.id})
        
        data = {
            'amount': '50.00',
            'target_user_id': self.user.id,  # 转给自己
            'password': '123456'
        }
        
        response = self.client.post(url, data, format='json')
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_freeze_insufficient_balance(self):
        """测试冻结金额超过可用余额"""
        url = reverse('userwallet-freeze', kwargs={'pk': self.wallet.id})
        
        data = {'amount': '200.00'}  # 超过可用余额
        
        response = self.client.post(url, data, format='json')
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)


class UserWalletPermissionTest(BaseAPITestCase):
    """用户钱包权限测试"""
    
    def setUp(self):
        super().setUp()
        from users.wallets.models import UserWallet
        
        self.wallet = UserWallet.objects.create(user=self.user)
        self.other_wallet = UserWallet.objects.create(user=self.other_user)
    
    def test_owner_access(self):
        """测试所有者访问权限"""
        self.authenticate_user(self.user)
        
        url = reverse('userwallet-detail', kwargs={'pk': self.wallet.id})
        response = self.client.get(url)
        
        self.assert_api_success(response)
    
    def test_other_user_access(self):
        """测试其他用户访问权限"""
        self.authenticate_user(self.other_user)
        
        url = reverse('userwallet-detail', kwargs={'pk': self.wallet.id})
        response = self.client.get(url)
        
        self.assert_api_forbidden(response)
    
    def test_admin_access(self):
        """测试管理员访问权限"""
        self.authenticate_user(self.admin_user)
        
        url = reverse('userwallet-detail', kwargs={'pk': self.wallet.id})
        response = self.client.get(url)
        
        self.assert_api_success(response)
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        url = reverse('userwallet-detail', kwargs={'pk': self.wallet.id})
        response = self.client.get(url)
        
        self.assert_api_unauthorized(response)


class UserWalletFilterTest(BaseAPITestCase):
    """用户钱包过滤器测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user(self.admin_user)  # 使用管理员测试过滤
        
        from users.wallets.models import UserWallet
        
        # 创建测试数据
        self.wallet1 = UserWallet.objects.create(
            user=self.user,
            currency='CNY',
            balance=Decimal('100.00'),
            is_verified=True
        )
        
        self.wallet2 = UserWallet.objects.create(
            user=self.other_user,
            currency='USD',
            balance=Decimal('50.00'),
            is_verified=False
        )
    
    def test_currency_filter(self):
        """测试货币类型过滤"""
        url = reverse('userwallet-list')
        response = self.client.get(url, {'currency': 'CNY'})
        
        self.assert_api_success(response)
        
        results = response.data['data']['results']
        for result in results:
            self.assertEqual(result['currency'], 'CNY')
    
    def test_verification_filter(self):
        """测试认证状态过滤"""
        url = reverse('userwallet-list')
        response = self.client.get(url, {'is_verified': 'true'})
        
        self.assert_api_success(response)
        
        results = response.data['data']['results']
        for result in results:
            self.assertTrue(result['is_verified'])
    
    def test_balance_range_filter(self):
        """测试余额范围过滤"""
        url = reverse('userwallet-list')
        response = self.client.get(url, {'balance_min': '75'})
        
        self.assert_api_success(response)
        
        results = response.data['data']['results']
        for result in results:
            self.assertGreaterEqual(Decimal(result['balance']), Decimal('75.00'))
