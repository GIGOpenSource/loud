"""
Users模块模型测试
测试所有模型的导入和基本功能
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal

from users.models import UserProfile, UserPreference, UserWallet, WalletTransaction
from .base import BaseTestCase, TestDataFactory

User = get_user_model()


class UserModelsImportTest(TestCase):
    """用户模型导入测试"""
    
    def test_import_user_profile(self):
        """测试UserProfile模型导入"""
        from users.models import UserProfile as ImportedProfile
        from users.profiles.models import UserProfile as OriginalProfile
        
        self.assertEqual(ImportedProfile, OriginalProfile)
    
    def test_import_user_preference(self):
        """测试UserPreference模型导入"""
        from users.models import UserPreference as ImportedPreference
        from users.preferences.models import UserPreference as OriginalPreference
        
        self.assertEqual(ImportedPreference, OriginalPreference)
    
    def test_import_user_wallet(self):
        """测试UserWallet模型导入"""
        from users.models import UserWallet as ImportedWallet
        from users.wallets.models import UserWallet as OriginalWallet
        
        self.assertEqual(ImportedWallet, OriginalWallet)
    
    def test_import_wallet_transaction(self):
        """测试WalletTransaction模型导入"""
        from users.models import WalletTransaction as ImportedTransaction
        from users.wallets.models import WalletTransaction as OriginalTransaction
        
        self.assertEqual(ImportedTransaction, OriginalTransaction)
    
    def test_all_exports(self):
        """测试__all__导出"""
        from users import models
        
        expected_exports = [
            'UserProfile',
            'UserPreference',
            'UserWallet',
            'WalletTransaction'
        ]
        
        self.assertEqual(set(models.__all__), set(expected_exports))
        
        # 验证所有导出的模型都可以正常访问
        for model_name in expected_exports:
            self.assertTrue(hasattr(models, model_name))


class UserProfileModelTest(BaseTestCase):
    """用户资料模型测试"""
    
    def setUp(self):
        super().setUp()
        self.profile_data = TestDataFactory.create_profile_data()
    
    def test_create_user_profile(self):
        """测试创建用户资料"""
        profile = UserProfile.objects.create(
            user=self.user,
            **self.profile_data
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.nickname, '测试昵称')
        self.assertEqual(profile.bio, '这是一个测试用户的个人简介')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.country, '中国')
        self.assertEqual(profile.city, '北京')
    
    def test_profile_str_representation(self):
        """测试资料字符串表示"""
        profile = UserProfile.objects.create(user=self.user)
        expected = f'{self.user.username} 的资料'
        self.assertEqual(str(profile), expected)
    
    def test_display_name_property(self):
        """测试显示名称属性"""
        # 有昵称时返回昵称
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='测试昵称'
        )
        self.assertEqual(profile.display_name, '测试昵称')
        
        # 无昵称时返回用户名
        profile.nickname = ''
        profile.save()
        self.assertEqual(profile.display_name, self.user.username)
    
    def test_age_property(self):
        """测试年龄属性"""
        from datetime import date
        
        # 设置出生日期
        profile = UserProfile.objects.create(
            user=self.user,
            birth_date=date(1990, 1, 1)
        )
        
        age = profile.age
        self.assertIsInstance(age, int)
        self.assertGreaterEqual(age, 30)  # 假设当前年份大于2020
        
        # 无出生日期时返回None
        profile.birth_date = None
        profile.save()
        self.assertIsNone(profile.age)
    
    def test_avatar_url_property(self):
        """测试头像URL属性"""
        profile = UserProfile.objects.create(user=self.user)
        
        # 无头像时返回None
        self.assertIsNone(profile.avatar_url)
    
    def test_clean_method(self):
        """测试模型验证方法"""
        from datetime import date, timedelta
        
        profile = UserProfile(user=self.user)
        
        # 正常情况下不应该抛出异常
        profile.clean()
        
        # 出生日期为未来日期时应该抛出异常
        profile.birth_date = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            profile.clean()
        
        # 网站URL格式错误时应该抛出异常
        profile.birth_date = None
        profile.website = 'invalid-url'
        with self.assertRaises(ValidationError):
            profile.clean()
    
    def test_get_public_data(self):
        """测试获取公开数据"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='测试昵称',
            bio='个人简介',
            gender='male',
            country='中国',
            city='北京',
            profile_visibility='public',
            show_email=True
        )
        
        public_data = profile.get_public_data()
        
        self.assertIn('id', public_data)
        self.assertIn('user_id', public_data)
        self.assertIn('display_name', public_data)
        self.assertIn('bio', public_data)
        self.assertIn('gender', public_data)
        self.assertIn('country', public_data)
        self.assertIn('city', public_data)
        
        # 当show_email为True时应该包含邮箱
        self.assertIn('email', public_data)
        
        # 测试私密资料
        profile.profile_visibility = 'private'
        profile.save()
        
        private_data = profile.get_public_data()
        self.assertNotIn('gender', private_data)
        self.assertNotIn('country', private_data)


class UserPreferenceModelTest(BaseTestCase):
    """用户偏好模型测试"""
    
    def setUp(self):
        super().setUp()
        self.preference_data = TestDataFactory.create_preference_data()
    
    def test_create_user_preference(self):
        """测试创建用户偏好"""
        preference = UserPreference.objects.create(
            user=self.user,
            **self.preference_data
        )
        
        self.assertEqual(preference.user, self.user)
        self.assertEqual(preference.theme, 'dark')
        self.assertEqual(preference.language, 'en')
        self.assertEqual(preference.timezone, 'America/New_York')
        self.assertTrue(preference.email_notifications)
        self.assertFalse(preference.push_notifications)
    
    def test_preference_str_representation(self):
        """测试偏好字符串表示"""
        preference = UserPreference.objects.create(user=self.user)
        expected = f'{self.user.username} 的偏好设置'
        self.assertEqual(str(preference), expected)
    
    def test_default_notification_types(self):
        """测试默认通知类型"""
        preference = UserPreference(user=self.user)
        default_types = preference.default_notification_types
        
        self.assertIsInstance(default_types, dict)
        self.assertIn('system_updates', default_types)
        self.assertIn('security_alerts', default_types)
        self.assertTrue(default_types['system_updates'])
        self.assertTrue(default_types['security_alerts'])
    
    def test_get_notification_setting(self):
        """测试获取通知设置"""
        preference = UserPreference.objects.create(
            user=self.user,
            notification_types={'messages': True, 'likes': False}
        )
        
        # 已设置的类型
        self.assertTrue(preference.get_notification_setting('messages'))
        self.assertFalse(preference.get_notification_setting('likes'))
        
        # 未设置的类型，应该返回默认值
        default_value = preference.default_notification_types.get('system_updates', False)
        self.assertEqual(
            preference.get_notification_setting('system_updates'),
            default_value
        )
    
    def test_set_notification_setting(self):
        """测试设置通知类型"""
        preference = UserPreference.objects.create(user=self.user)
        
        preference.set_notification_setting('messages', True)
        self.assertTrue(preference.get_notification_setting('messages'))
        
        preference.set_notification_setting('messages', False)
        self.assertFalse(preference.get_notification_setting('messages'))
    
    def test_custom_settings(self):
        """测试自定义设置"""
        preference = UserPreference.objects.create(user=self.user)
        
        # 获取不存在的设置
        self.assertIsNone(preference.get_custom_setting('nonexistent'))
        self.assertEqual(
            preference.get_custom_setting('nonexistent', 'default'),
            'default'
        )
        
        # 设置自定义设置
        preference.set_custom_setting('test_key', 'test_value')
        self.assertEqual(preference.get_custom_setting('test_key'), 'test_value')
    
    def test_reset_to_defaults(self):
        """测试重置为默认设置"""
        preference = UserPreference.objects.create(
            user=self.user,
            theme='dark',
            language='en',
            email_notifications=False
        )
        
        preference.reset_to_defaults()
        
        self.assertEqual(preference.theme, 'light')
        self.assertEqual(preference.language, 'zh-hans')
        self.assertTrue(preference.email_notifications)
    
    def test_export_import_settings(self):
        """测试设置导入导出"""
        preference = UserPreference.objects.create(
            user=self.user,
            **self.preference_data
        )
        
        # 导出设置
        exported_data = preference.export_settings()
        self.assertIsInstance(exported_data, dict)
        self.assertEqual(exported_data['theme'], 'dark')
        self.assertEqual(exported_data['language'], 'en')
        
        # 导入设置
        new_settings = {
            'theme': 'light',
            'language': 'zh-hans',
            'email_notifications': False
        }
        preference.import_settings(new_settings)
        
        self.assertEqual(preference.theme, 'light')
        self.assertEqual(preference.language, 'zh-hans')
        self.assertFalse(preference.email_notifications)
    
    def test_clean_method(self):
        """测试模型验证"""
        preference = UserPreference(
            user=self.user,
            items_per_page=50
        )
        
        # 正常情况
        preference.clean()
        
        # 每页显示条数超出范围
        preference.items_per_page = 200
        with self.assertRaises(ValidationError):
            preference.clean()
        
        preference.items_per_page = 2
        with self.assertRaises(ValidationError):
            preference.clean()


class UserWalletModelTest(BaseTestCase):
    """用户钱包模型测试"""
    
    def setUp(self):
        super().setUp()
        self.wallet_data = TestDataFactory.create_wallet_data()
    
    def test_create_user_wallet(self):
        """测试创建用户钱包"""
        wallet = UserWallet.objects.create(
            user=self.user,
            **self.wallet_data
        )
        
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.currency, 'USD')
        self.assertEqual(wallet.balance, Decimal('0.00'))
        self.assertEqual(wallet.frozen_balance, Decimal('0.00'))
        self.assertEqual(str(wallet.daily_limit), '5000.00')
        self.assertEqual(str(wallet.monthly_limit), '50000.00')
    
    def test_wallet_str_representation(self):
        """测试钱包字符串表示"""
        wallet = UserWallet.objects.create(user=self.user, currency='CNY')
        expected = f'{self.user.username} 的人民币钱包'
        self.assertEqual(str(wallet), expected)
    
    def test_balance_properties(self):
        """测试余额属性"""
        wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00'),
            frozen_balance=Decimal('50.00')
        )
        
        self.assertEqual(wallet.total_balance, Decimal('150.00'))
        self.assertEqual(wallet.available_balance, Decimal('100.00'))
    
    def test_balance_status_property(self):
        """测试余额状态"""
        wallet = UserWallet.objects.create(user=self.user)
        
        # 余额为0
        wallet.balance = Decimal('0.00')
        self.assertEqual(wallet.balance_status, 'empty')
        
        # 余额较低
        wallet.balance = Decimal('50.00')
        self.assertEqual(wallet.balance_status, 'low')
        
        # 余额正常
        wallet.balance = Decimal('500.00')
        self.assertEqual(wallet.balance_status, 'normal')
        
        # 余额较高
        wallet.balance = Decimal('5000.00')
        self.assertEqual(wallet.balance_status, 'high')
    
    def test_can_spend(self):
        """测试是否可以消费"""
        wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00'),
            wallet_status='normal',
            is_active=True
        )
        
        # 正常情况可以消费
        can_spend, reason = wallet.can_spend(Decimal('50.00'))
        self.assertTrue(can_spend)
        
        # 余额不足
        can_spend, reason = wallet.can_spend(Decimal('150.00'))
        self.assertFalse(can_spend)
        self.assertIn('余额不足', reason)
        
        # 钱包被冻结
        wallet.wallet_status = 'frozen'
        wallet.save()
        can_spend, reason = wallet.can_spend(Decimal('50.00'))
        self.assertFalse(can_spend)
        self.assertIn('钱包状态异常', reason)
        
        # 钱包被停用
        wallet.wallet_status = 'normal'
        wallet.is_active = False
        wallet.save()
        can_spend, reason = wallet.can_spend(Decimal('50.00'))
        self.assertFalse(can_spend)
        self.assertIn('钱包已被停用', reason)
    
    def test_freeze_unfreeze_amount(self):
        """测试冻结和解冻金额"""
        wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        
        # 冻结金额
        wallet.freeze_amount(Decimal('30.00'), '测试冻结')
        wallet.refresh_from_db()
        
        self.assertEqual(wallet.balance, Decimal('70.00'))
        self.assertEqual(wallet.frozen_balance, Decimal('30.00'))
        
        # 解冻金额
        wallet.unfreeze_amount(Decimal('20.00'), '测试解冻')
        wallet.refresh_from_db()
        
        self.assertEqual(wallet.balance, Decimal('90.00'))
        self.assertEqual(wallet.frozen_balance, Decimal('10.00'))
        
        # 冻结金额超过可用余额
        with self.assertRaises(ValueError):
            wallet.freeze_amount(Decimal('100.00'))
        
        # 解冻金额超过冻结余额
        with self.assertRaises(ValueError):
            wallet.unfreeze_amount(Decimal('20.00'))
    
    def test_deposit(self):
        """测试充值"""
        wallet = UserWallet.objects.create(user=self.user)
        
        transaction = wallet.deposit(
            amount=Decimal('100.00'),
            source='test',
            description='测试充值'
        )
        
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal('100.00'))
        self.assertEqual(wallet.total_income, Decimal('100.00'))
        self.assertIsNotNone(wallet.last_transaction_at)
        
        # 验证交易记录
        self.assertEqual(transaction.transaction_type, 'deposit')
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.description, '测试充值')
    
    def test_withdraw(self):
        """测试提现"""
        wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        
        transaction = wallet.withdraw(
            amount=Decimal('50.00'),
            destination='test',
            description='测试提现'
        )
        
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal('50.00'))
        self.assertEqual(wallet.total_expense, Decimal('50.00'))
        
        # 验证交易记录
        self.assertEqual(transaction.transaction_type, 'withdraw')
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.description, '测试提现')
        
        # 余额不足时应该抛出异常
        with self.assertRaises(ValueError):
            wallet.withdraw(Decimal('100.00'))
    
    def test_transfer_to(self):
        """测试转账"""
        wallet1, created = UserWallet.objects.get_or_create(
            user=self.user,
            defaults={
                'balance': Decimal('100.00'),
                'currency': 'CNY'
            }
        )
        
        wallet2, created = UserWallet.objects.get_or_create(
            user=self.other_user,
            defaults={
                'balance': Decimal('50.00'),
                'currency': 'CNY'
            }
        )
        # 如果wallet2已经存在，设置其余额为50.00
        if not created:
            wallet2.balance = Decimal('50.00')
            wallet2.save()
        
        transfer_out, transfer_in = wallet1.transfer_to(
            target_wallet=wallet2,
            amount=Decimal('30.00'),
            description='测试转账'
        )
        
        wallet1.refresh_from_db()
        wallet2.refresh_from_db()
        
        self.assertEqual(wallet1.balance, Decimal('70.00'))
        # 转账后：wallet2初始余额50 + 转账30 = 80，但由于get_or_create可能改变了初始余额
        # 检查转账是否正确执行：wallet2余额应该增加30
        self.assertEqual(wallet2.balance, Decimal('50.00') + Decimal('30.00'))
        
        # 验证交易记录
        self.assertEqual(transfer_out.transaction_type, 'transfer_out')
        self.assertEqual(transfer_in.transaction_type, 'transfer_in')
        self.assertEqual(transfer_out.amount, Decimal('30.00'))
        self.assertEqual(transfer_in.amount, Decimal('30.00'))
        
        # 货币类型不匹配 - 创建一个新用户避免约束冲突
        from django.contrib.auth import get_user_model
        User = get_user_model()
        test_user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com'
        )
        wallet3, created = UserWallet.objects.get_or_create(
            user=test_user3,
            defaults={
                'currency': 'USD',
                'balance': Decimal('0.00')
            }
        )
        # 确保钱包3的货币类型为USD以测试货币不匹配的情况
        if not created:
            wallet3.currency = 'USD'
            wallet3.save()
        
        # 检查货币类型不匹配的情况
        with self.assertRaises(ValueError):
            wallet1.transfer_to(wallet3, Decimal('10.00'))
    
    def test_payment_password(self):
        """测试支付密码"""
        wallet = UserWallet.objects.create(user=self.user)
        
        # 设置支付密码
        wallet.set_payment_password('123456')
        self.assertIsNotNone(wallet.payment_password)
        self.assertIsNotNone(wallet.payment_password_set_at)
        
        # 验证支付密码
        self.assertTrue(wallet.check_payment_password('123456'))
        self.assertFalse(wallet.check_payment_password('wrong'))
        
        # 无密码时验证
        wallet.payment_password = ''
        wallet.save()
        self.assertFalse(wallet.check_payment_password('123456'))
    
    def test_wallet_verification(self):
        """测试钱包认证"""
        wallet = UserWallet.objects.create(user=self.user)
        
        self.assertFalse(wallet.is_verified)
        self.assertIsNone(wallet.verified_at)
        
        wallet.verify_wallet()
        
        self.assertTrue(wallet.is_verified)
        self.assertIsNotNone(wallet.verified_at)
    
    def test_freeze_unfreeze_wallet(self):
        """测试冻结和解冻钱包"""
        wallet = UserWallet.objects.create(user=self.user)
        
        self.assertEqual(wallet.wallet_status, 'normal')
        
        wallet.freeze_wallet('测试冻结')
        self.assertEqual(wallet.wallet_status, 'frozen')
        
        wallet.unfreeze_wallet('测试解冻')
        self.assertEqual(wallet.wallet_status, 'normal')
    
    def test_clean_method(self):
        """测试模型验证"""
        wallet = UserWallet(
            user=self.user,
            balance=Decimal('100.00'),
            frozen_balance=Decimal('50.00'),
            daily_limit=Decimal('1000.00'),
            monthly_limit=Decimal('10000.00')
        )
        
        # 正常情况
        wallet.clean()
        
        # 余额为负数
        wallet.balance = Decimal('-10.00')
        with self.assertRaises(ValidationError):
            wallet.clean()
        
        # 日限额超过月限额
        wallet.balance = Decimal('100.00')
        wallet.daily_limit = Decimal('20000.00')
        with self.assertRaises(ValidationError):
            wallet.clean()


class WalletTransactionModelTest(BaseTestCase):
    """钱包交易模型测试"""
    
    def setUp(self):
        super().setUp()
        self.wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
    
    def test_create_transaction(self):
        """测试创建交易记录"""
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            balance_after=Decimal('150.00'),
            description='测试充值',
            source='test'
        )
        
        self.assertEqual(transaction.wallet, self.wallet)
        self.assertEqual(transaction.transaction_type, 'deposit')
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.balance_after, Decimal('150.00'))
        self.assertEqual(transaction.status, 'completed')
    
    def test_transaction_str_representation(self):
        """测试交易字符串表示"""
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            balance_after=Decimal('150.00')
        )
        
        expected = f'{self.user.username} - 充值 - 50.00'
        self.assertEqual(str(transaction), expected)
    
    def test_is_income_property(self):
        """测试是否是收入类交易"""
        # 收入类交易
        for tx_type in ['deposit', 'transfer_in', 'refund', 'reward']:
            transaction = WalletTransaction(
                wallet=self.wallet,
                transaction_type=tx_type,
                amount=Decimal('50.00'),
                balance_after=Decimal('150.00')
            )
            self.assertTrue(transaction.is_income)
    
    def test_is_expense_property(self):
        """测试是否是支出类交易"""
        # 支出类交易
        for tx_type in ['withdraw', 'transfer_out', 'payment', 'penalty']:
            transaction = WalletTransaction(
                wallet=self.wallet,
                transaction_type=tx_type,
                amount=Decimal('50.00'),
                balance_after=Decimal('50.00')
            )
            self.assertTrue(transaction.is_expense)
    
    def test_can_refund(self):
        """测试是否可以退款"""
        from django.utils import timezone
        from datetime import timedelta
        
        # 可以退款的交易
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='payment',
            amount=Decimal('50.00'),
            balance_after=Decimal('50.00'),
            status='completed'
        )
        self.assertTrue(transaction.can_refund())
        
        # 不可退款的交易类型
        transaction.transaction_type = 'deposit'
        transaction.save()
        self.assertFalse(transaction.can_refund())
        
        # 状态不是completed
        transaction.transaction_type = 'payment'
        transaction.status = 'failed'
        transaction.save()
        self.assertFalse(transaction.can_refund())
        
        # 超过30天
        transaction.status = 'completed'
        transaction.created_at = timezone.now() - timedelta(days=31)
        transaction.save()
        self.assertFalse(transaction.can_refund())
    
    def test_process_refund(self):
        """测试处理退款"""
        # 先进行一次支付
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='payment',
            amount=Decimal('50.00'),
            balance_after=Decimal('50.00'),
            status='completed'
        )
        
        # 更新钱包余额以反映支付
        self.wallet.balance = Decimal('50.00')
        self.wallet.save()
        
        # 处理退款
        refund_transaction = transaction.process_refund('测试退款')
        
        # 验证原交易状态
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'refunded')
        
        # 验证钱包余额
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100.00'))
        
        # 验证退款交易
        self.assertEqual(refund_transaction.transaction_type, 'refund')
        self.assertEqual(refund_transaction.amount, Decimal('50.00'))
        self.assertIn('测试退款', refund_transaction.description)
        
        # 尝试退款不可退款的交易
        with self.assertRaises(ValueError):
            transaction.process_refund()
