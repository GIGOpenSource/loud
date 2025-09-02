"""
Users模块管理后台测试
"""

from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from decimal import Decimal

from users.models import UserProfile, UserPreference, UserWallet, WalletTransaction
from .base import BaseTestCase

User = get_user_model()


class MockRequest:
    """模拟请求对象"""
    def __init__(self, user=None):
        self.user = user


class UserProfileAdminTest(BaseTestCase):
    """用户资料管理后台测试"""
    
    def setUp(self):
        super().setUp()
        from users.profiles.admin import UserProfileAdmin
        
        self.site = AdminSite()
        self.admin = UserProfileAdmin(UserProfile, self.site)
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            nickname='测试用户',
            bio='测试简介',
            gender='male',
            country='中国',
            city='北京'
        )
    
    def test_list_display(self):
        """测试列表显示"""
        # 验证list_display字段
        expected_fields = [
            'user_link', 'nickname', 'gender', 'city', 'country',
            'profile_visibility', 'avatar_preview', 'is_active', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)
    
    def test_user_link_method(self):
        """测试用户链接方法"""
        user_link = self.admin.user_link(self.profile)
        
        self.assertIn(str(self.user.id), user_link)
        self.assertIn(self.user.username, user_link)
        self.assertIn('<a href=', user_link)
    
    def test_avatar_preview_method(self):
        """测试头像预览方法"""
        # 无头像情况
        avatar_preview = self.admin.avatar_preview(self.profile)
        self.assertIn('无头像', avatar_preview)
    
    def test_display_name_method(self):
        """测试显示名称方法"""
        display_name = self.admin.display_name(self.profile)
        self.assertEqual(display_name, '测试用户')
    
    def test_age_method(self):
        """测试年龄方法"""
        from datetime import date
        
        # 无出生日期
        age_display = self.admin.age(self.profile)
        self.assertEqual(age_display, '未设置')
        
        # 有出生日期
        self.profile.birth_date = date(1990, 1, 1)
        self.profile.save()
        
        age_display = self.admin.age(self.profile)
        self.assertIn('岁', age_display)
    
    def test_admin_actions(self):
        """测试管理员操作"""
        request = MockRequest(self.admin_user)
        queryset = UserProfile.objects.filter(id=self.profile.id)
        
        # 测试激活操作
        self.admin.activate_profiles(request, queryset)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_active)
        
        # 测试停用操作
        self.admin.deactivate_profiles(request, queryset)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_active)
        
        # 测试设置公开
        self.admin.set_public(request, queryset)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.profile_visibility, 'public')
        
        # 测试设置私密
        self.admin.set_private(request, queryset)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.profile_visibility, 'private')


class UserPreferenceAdminTest(BaseTestCase):
    """用户偏好管理后台测试"""
    
    def setUp(self):
        super().setUp()
        from users.preferences.admin import UserPreferenceAdmin
        
        self.site = AdminSite()
        self.admin = UserPreferenceAdmin(UserPreference, self.site)
        
        self.preference = UserPreference.objects.create(
            user=self.user,
            theme='dark',
            language='en',
            email_notifications=True,
            push_notifications=False,
            notification_types={'messages': True, 'likes': False}
        )
    
    def test_list_display(self):
        """测试列表显示"""
        expected_fields = [
            'user_link', 'theme', 'language', 'timezone',
            'notifications_status', 'privacy_status', 'is_active', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)
    
    def test_notifications_status_method(self):
        """测试通知状态方法"""
        status = self.admin.notifications_status(self.preference)
        
        # 应该包含邮件通知图标
        self.assertIn('📧', status)
        # 不应该包含推送通知图标（因为关闭了）
        self.assertNotIn('🔔', status)
    
    def test_privacy_status_method(self):
        """测试隐私状态方法"""
        status = self.admin.privacy_status(self.preference)
        
        # 默认设置应该包含某些隐私选项
        self.assertIsInstance(status, str)
    
    def test_formatted_notification_types_method(self):
        """测试格式化通知类型方法"""
        formatted = self.admin.formatted_notification_types(self.preference)
        
        self.assertIn('messages', formatted)
        self.assertIn('likes', formatted)
        self.assertIn('<pre', formatted)
    
    def test_admin_actions(self):
        """测试管理员操作"""
        request = MockRequest(self.admin_user)
        queryset = UserPreference.objects.filter(id=self.preference.id)
        
        # 测试启用所有通知
        self.admin.enable_all_notifications(request, queryset)
        self.preference.refresh_from_db()
        self.assertTrue(self.preference.email_notifications)
        self.assertTrue(self.preference.push_notifications)
        self.assertTrue(self.preference.sms_notifications)
        
        # 测试禁用所有通知
        self.admin.disable_all_notifications(request, queryset)
        self.preference.refresh_from_db()
        self.assertFalse(self.preference.email_notifications)
        self.assertFalse(self.preference.push_notifications)
        self.assertFalse(self.preference.sms_notifications)
        
        # 测试重置为默认设置
        original_theme = self.preference.theme
        self.admin.reset_to_defaults(request, queryset)
        self.preference.refresh_from_db()
        # 重置后应该是默认主题
        self.assertEqual(self.preference.theme, 'light')


class UserWalletAdminTest(BaseTestCase):
    """用户钱包管理后台测试"""
    
    def setUp(self):
        super().setUp()
        from users.wallets.admin import UserWalletAdmin
        
        self.site = AdminSite()
        self.admin = UserWalletAdmin(UserWallet, self.site)
        
        self.wallet = UserWallet.objects.create(
            user=self.user,
            currency='CNY',
            balance=Decimal('100.00'),
            frozen_balance=Decimal('20.00'),
            total_income=Decimal('200.00'),
            total_expense=Decimal('80.00'),
            is_verified=True
        )
    
    def test_list_display(self):
        """测试列表显示"""
        expected_fields = [
            'user_link', 'currency', 'formatted_balance_display', 'formatted_frozen_balance',
            'wallet_status', 'balance_status_display', 'is_verified', 'is_active', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)
    
    def test_formatted_balance_display_method(self):
        """测试格式化余额显示方法"""
        balance_display = self.admin.formatted_balance_display(self.wallet)
        
        self.assertIn('100.00', balance_display)
        self.assertIn('CNY', balance_display)
        self.assertIn('color: green', balance_display)  # 正余额应该是绿色
    
    def test_formatted_frozen_balance_method(self):
        """测试格式化冻结余额方法"""
        frozen_display = self.admin.formatted_frozen_balance(self.wallet)
        
        self.assertIn('20.00', frozen_display)
        self.assertIn('color: orange', frozen_display)
    
    def test_balance_status_display_method(self):
        """测试余额状态显示方法"""
        status_display = self.admin.balance_status_display(self.wallet)
        
        self.assertIn('●', status_display)
        self.assertIn('余额正常', status_display)
    
    def test_total_balance_display_method(self):
        """测试总余额显示方法"""
        total_display = self.admin.total_balance_display(self.wallet)
        
        self.assertIn('120.00', total_display)  # 100 + 20
        self.assertIn('CNY', total_display)
    
    def test_recent_transactions_method(self):
        """测试最近交易方法"""
        # 创建一些交易记录
        WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            balance_after=Decimal('50.00'),
            description='测试充值'
        )
        
        transactions_display = self.admin.recent_transactions(self.wallet)
        
        self.assertIn('<table', transactions_display)
        self.assertIn('测试充值', transactions_display)
    
    def test_admin_actions(self):
        """测试管理员操作"""
        request = MockRequest(self.admin_user)
        queryset = UserWallet.objects.filter(id=self.wallet.id)
        
        # 测试冻结钱包
        self.admin.freeze_wallets(request, queryset)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.wallet_status, 'frozen')
        
        # 测试解冻钱包
        self.admin.unfreeze_wallets(request, queryset)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.wallet_status, 'normal')
        
        # 测试认证钱包
        self.wallet.is_verified = False
        self.wallet.save()
        
        self.admin.verify_wallets(request, queryset)
        self.wallet.refresh_from_db()
        self.assertTrue(self.wallet.is_verified)


class WalletTransactionAdminTest(BaseTestCase):
    """钱包交易管理后台测试"""
    
    def setUp(self):
        super().setUp()
        from users.wallets.admin import WalletTransactionAdmin
        
        self.site = AdminSite()
        self.admin = WalletTransactionAdmin(WalletTransaction, self.site)
        
        self.wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00')
        )
        
        self.transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('50.00'),
            balance_after=Decimal('150.00'),
            status='completed',
            description='测试充值交易',
            metadata={'source': 'test', 'method': 'bank_transfer'}
        )
    
    def test_list_display(self):
        """测试列表显示"""
        expected_fields = [
            'id', 'wallet_user_link', 'transaction_type', 'formatted_amount_display',
            'status', 'flow_indicator', 'description_short', 'created_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)
    
    def test_wallet_user_link_method(self):
        """测试钱包用户链接方法"""
        user_link = self.admin.wallet_user_link(self.transaction)
        
        self.assertIn(str(self.wallet.id), user_link)
        self.assertIn(self.user.username, user_link)
        self.assertIn('<a href=', user_link)
    
    def test_formatted_amount_display_method(self):
        """测试格式化金额显示方法"""
        amount_display = self.admin.formatted_amount_display(self.transaction)
        
        self.assertIn('50.00', amount_display)
        self.assertIn('font-weight: bold', amount_display)
    
    def test_flow_indicator_method(self):
        """测试资金流向指示器方法"""
        flow = self.admin.flow_indicator(self.transaction)
        
        # 充值应该是收入（绿色向上箭头）
        self.assertIn('color: green', flow)
        self.assertIn('↗', flow)
        self.assertIn('收入', flow)
    
    def test_description_short_method(self):
        """测试简短描述方法"""
        # 测试正常长度描述
        short_desc = self.admin.description_short(self.transaction)
        self.assertEqual(short_desc, '测试充值交易')
        
        # 测试过长描述
        self.transaction.description = 'a' * 50
        self.transaction.save()
        
        short_desc = self.admin.description_short(self.transaction)
        self.assertTrue(short_desc.endswith('...'))
        self.assertEqual(len(short_desc), 33)  # 30 + '...'
    
    def test_flow_type_method(self):
        """测试资金流向类型方法"""
        flow_type = self.admin.flow_type(self.transaction)
        self.assertEqual(flow_type, '收入')
        
        # 测试支出类型
        self.transaction.transaction_type = 'withdraw'
        flow_type = self.admin.flow_type(self.transaction)
        self.assertEqual(flow_type, '支出')
        
        # 测试中性类型
        self.transaction.transaction_type = 'freeze'
        flow_type = self.admin.flow_type(self.transaction)
        self.assertEqual(flow_type, '中性')
    
    def test_formatted_metadata_method(self):
        """测试格式化元数据方法"""
        metadata_display = self.admin.formatted_metadata(self.transaction)
        
        self.assertIn('<pre', metadata_display)
        self.assertIn('source', metadata_display)
        self.assertIn('test', metadata_display)
    
    def test_admin_actions(self):
        """测试管理员操作"""
        request = MockRequest(self.admin_user)
        queryset = WalletTransaction.objects.filter(id=self.transaction.id)
        
        # 测试标记为已完成
        self.transaction.status = 'pending'
        self.transaction.save()
        
        self.admin.mark_as_completed(request, queryset)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, 'completed')
        
        # 测试标记为失败
        self.admin.mark_as_failed(request, queryset)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, 'failed')


class AdminIntegrationTest(TestCase):
    """管理后台集成测试"""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')
    
    def test_admin_site_access(self):
        """测试管理后台访问"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_profile_admin_access(self):
        """测试用户资料管理页面访问"""
        response = self.client.get('/admin/users/userprofile/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_preference_admin_access(self):
        """测试用户偏好管理页面访问"""
        response = self.client.get('/admin/users/userpreference/')
        self.assertEqual(response.status_code, 200)
    
    def test_user_wallet_admin_access(self):
        """测试用户钱包管理页面访问"""
        response = self.client.get('/admin/users/userwallet/')
        self.assertEqual(response.status_code, 200)
    
    def test_wallet_transaction_admin_access(self):
        """测试钱包交易管理页面访问"""
        response = self.client.get('/admin/users/wallettransaction/')
        self.assertEqual(response.status_code, 200)
