"""
Users模块集成测试
测试各个组件之间的协作
"""

from django.urls import reverse
from rest_framework import status
from decimal import Decimal

from .base import BaseAPITestCase, TestDataFactory


class UserModuleIntegrationTest(BaseAPITestCase):
    """用户模块集成测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
    
    def test_complete_user_flow(self):
        """测试完整的用户流程"""
        # 1. 获取仪表板（初始状态）
        response = self.client.get(reverse('user-dashboard'))
        self.assert_api_success(response)
        
        dashboard_data = response.data['data']
        self.assertIn('user', dashboard_data)
        self.assertIn('profile', dashboard_data)
        self.assertIn('preferences', dashboard_data)
        self.assertIn('wallet', dashboard_data)
        
        # 2. 更新用户资料
        profile_data = TestDataFactory.create_profile_data()
        response = self.client.put(
            reverse('userprofile-update-my-profile'),
            profile_data,
            format='json'
        )
        self.assert_api_success(response)
        
        # 3. 更新用户偏好
        preference_data = TestDataFactory.create_preference_data()
        response = self.client.put(
            reverse('userpreference-update-my-preferences'),
            preference_data,
            format='json'
        )
        self.assert_api_success(response)
        
        # 4. 钱包充值
        from users.wallets.models import UserWallet
        wallet = UserWallet.objects.get(user=self.user)
        
        deposit_data = {
            'amount': '100.00',
            'description': '测试充值',
            'source': 'integration_test'
        }
        
        response = self.client.post(
            reverse('userwallet-deposit', kwargs={'pk': wallet.id}),
            deposit_data,
            format='json'
        )
        self.assert_api_success(response)
        
        # 5. 再次获取仪表板（验证所有更新）
        response = self.client.get(reverse('user-dashboard'))
        self.assert_api_success(response)
        
        updated_dashboard = response.data['data']
        
        # 验证资料已更新
        profile = updated_dashboard['profile']
        self.assertEqual(profile['nickname'], profile_data['nickname'])
        
        # 验证偏好已更新
        preferences = updated_dashboard['preferences']
        self.assertEqual(preferences['theme'], preference_data['theme'])
        
        # 验证钱包余额已更新
        wallet_data = updated_dashboard['wallet']
        self.assertEqual(Decimal(wallet_data['balance']), Decimal('100.00'))
    
    def test_cross_module_data_consistency(self):
        """测试跨模块数据一致性"""
        from users.profiles.models import UserProfile
        from users.preferences.models import UserPreference
        from users.wallets.models import UserWallet
        
        # 创建数据
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='一致性测试用户'
        )
        
        preference = UserPreference.objects.create(
            user=self.user,
            theme='dark'
        )
        
        wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('50.00')
        )
        
        # 通过不同接口获取数据
        dashboard_response = self.client.get(reverse('user-dashboard'))
        overview_response = self.client.get(reverse('user-overview'))
        
        self.assert_api_success(dashboard_response)
        self.assert_api_success(overview_response)
        
        # 验证数据一致性
        dashboard_data = dashboard_response.data['data']
        overview_data = overview_response.data['data']
        
        # 用户信息应该一致
        self.assertEqual(
            dashboard_data['user']['username'],
            overview_data['username']
        )
        
        # 资料信息应该一致
        self.assertEqual(
            dashboard_data['profile']['nickname'],
            '一致性测试用户'
        )
        
        # 钱包余额应该一致
        self.assertEqual(
            Decimal(dashboard_data['wallet']['balance']),
            Decimal('50.00')
        )


class UserPermissionIntegrationTest(BaseAPITestCase):
    """用户权限集成测试"""
    
    def setUp(self):
        super().setUp()
        from users.profiles.models import UserProfile
        from users.preferences.models import UserPreference
        from users.wallets.models import UserWallet
        
        # 为不同用户创建数据
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            nickname='用户1',
            profile_visibility='private'
        )
        
        self.other_profile = UserProfile.objects.create(
            user=self.other_user,
            nickname='用户2',
            profile_visibility='public'
        )
        
        self.user_preference = UserPreference.objects.create(user=self.user)
        self.other_preference = UserPreference.objects.create(user=self.other_user)
        
        self.user_wallet = UserWallet.objects.create(user=self.user)
        self.other_wallet = UserWallet.objects.create(user=self.other_user)
    
    def test_user_can_only_access_own_data(self):
        """测试用户只能访问自己的数据"""
        self.authenticate_user(self.user)
        
        # 可以访问自己的数据
        response = self.client.get(
            reverse('profiles-detail', kwargs={'pk': self.user_profile.id})
        )
        self.assert_api_success(response)
        
        response = self.client.get(
            reverse('preferences-detail', kwargs={'pk': self.user_preference.id})
        )
        self.assert_api_success(response)
        
        response = self.client.get(
            reverse('wallets-detail', kwargs={'pk': self.user_wallet.id})
        )
        self.assert_api_success(response)
        
        # 不能访问他人的私密数据
        response = self.client.get(
            reverse('preferences-detail', kwargs={'pk': self.other_preference.id})
        )
        self.assert_api_forbidden(response)
        
        response = self.client.get(
            reverse('wallets-detail', kwargs={'pk': self.other_wallet.id})
        )
        self.assert_api_forbidden(response)
    
    def test_admin_can_access_all_data(self):
        """测试管理员可以访问所有数据"""
        self.authenticate_user(self.admin_user)
        
        # 管理员可以访问任何用户的数据
        response = self.client.get(
            reverse('profiles-detail', kwargs={'pk': self.user_profile.id})
        )
        self.assert_api_success(response)
        
        response = self.client.get(
            reverse('profiles-detail', kwargs={'pk': self.other_profile.id})
        )
        self.assert_api_success(response)
        
        response = self.client.get(
            reverse('preferences-detail', kwargs={'pk': self.user_preference.id})
        )
        self.assert_api_success(response)
        
        response = self.client.get(
            reverse('wallets-detail', kwargs={'pk': self.user_wallet.id})
        )
        self.assert_api_success(response)
    
    def test_public_data_access(self):
        """测试公开数据访问"""
        # 无需认证即可访问公开资料
        self.logout_user()
        
        response = self.client.get(
            reverse('public-profile', kwargs={'user_id': self.other_user.id})
        )
        self.assert_api_success(response)
        
        # 不能访问私密资料
        response = self.client.get(
            reverse('public-profile', kwargs={'user_id': self.user.id})
        )
        # 根据实际实现，可能返回部分信息或404
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])


class WalletTransactionIntegrationTest(BaseAPITestCase):
    """钱包交易集成测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
        
        from users.wallets.models import UserWallet
        
        self.wallet = UserWallet.objects.create(
            user=self.user,
            balance=Decimal('100.00'),
            currency='CNY'
        )
        self.wallet.set_payment_password('123456')
        
        self.other_wallet = UserWallet.objects.create(
            user=self.other_user,
            balance=Decimal('50.00'),
            currency='CNY'
        )
    
    def test_complete_transaction_flow(self):
        """测试完整的交易流程"""
        # 1. 充值
        deposit_data = {
            'amount': '50.00',
            'description': '集成测试充值',
            'source': 'test'
        }
        
        response = self.client.post(
            reverse('wallets-deposit', kwargs={'pk': self.wallet.id}),
            deposit_data,
            format='json'
        )
        self.assert_api_success(response)
        
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('150.00'))
        
        # 2. 转账
        transfer_data = {
            'amount': '30.00',
            'target_user_id': self.other_user.id,
            'description': '集成测试转账',
            'password': '123456'
        }
        
        response = self.client.post(
            reverse('userwallet-transfer', kwargs={'pk': self.wallet.id}),
            transfer_data,
            format='json'
        )
        self.assert_api_success(response)
        
        self.wallet.refresh_from_db()
        self.other_wallet.refresh_from_db()
        
        self.assertEqual(self.wallet.balance, Decimal('120.00'))
        self.assertEqual(self.other_wallet.balance, Decimal('80.00'))
        
        # 3. 提现
        withdraw_data = {
            'amount': '20.00',
            'description': '集成测试提现',
            'destination': 'test_bank',
            'password': '123456'
        }
        
        response = self.client.post(
            reverse('userwallet-withdraw', kwargs={'pk': self.wallet.id}),
            withdraw_data,
            format='json'
        )
        self.assert_api_success(response)
        
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100.00'))
        
        # 4. 查看交易记录
        response = self.client.get(reverse('wallettransaction-my-transactions'))
        self.assert_api_success(response)
        
        transactions = response.data['data']['results']
        self.assertGreaterEqual(len(transactions), 3)  # 至少有3笔交易
        
        # 验证交易类型
        transaction_types = [t['transaction_type'] for t in transactions]
        self.assertIn('deposit', transaction_types)
        self.assertIn('transfer_out', transaction_types)
        self.assertIn('withdraw', transaction_types)
    
    def test_transaction_rollback_scenario(self):
        """测试交易回滚场景"""
        # 测试余额不足的情况
        insufficient_data = {
            'amount': '200.00',  # 超过余额
            'description': '余额不足测试',
            'destination': 'test',
            'password': '123456'
        }
        
        original_balance = self.wallet.balance
        
        response = self.client.post(
            reverse('userwallet-withdraw', kwargs={'pk': self.wallet.id}),
            insufficient_data,
            format='json'
        )
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
        
        # 验证余额没有变化
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, original_balance)


class CacheIntegrationTest(BaseAPITestCase):
    """缓存集成测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
        
        from django.core.cache import cache
        cache.clear()  # 清空缓存
    
    def test_dashboard_caching_behavior(self):
        """测试仪表板缓存行为"""
        from django.core.cache import cache
        
        # 首次访问
        response1 = self.client.get(reverse('user-dashboard'))
        self.assert_api_success(response1)
        
        # 验证缓存被创建
        cache_key = f'user_dashboard_{self.user.id}'
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        
        # 第二次访问应该从缓存获取
        response2 = self.client.get(reverse('user-dashboard'))
        self.assert_api_success(response2)
        
        # 更新资料应该清空缓存
        from users.profiles.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.nickname = '更新昵称'
        profile.save()
        
        # 验证缓存被清空
        cached_data = cache.get(cache_key)
        self.assertIsNone(cached_data)
    
    def test_profile_cache_invalidation(self):
        """测试资料缓存失效"""
        from django.core.cache import cache
        from users.profiles.models import UserProfile
        
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='原始昵称'
        )
        
        cache_key = f'user_profile_{self.user.id}'
        cache.set(cache_key, 'cached_profile_data', 300)
        
        # 更新资料应该清空相关缓存
        profile.nickname = '新昵称'
        profile.save()
        
        # 验证缓存被清空
        self.assertIsNone(cache.get(cache_key))
        self.assertIsNone(cache.get(f'user_dashboard_{self.user.id}'))


class ErrorHandlingIntegrationTest(BaseAPITestCase):
    """错误处理集成测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
    
    def test_cascade_error_handling(self):
        """测试级联错误处理"""
        # 测试删除用户时相关数据的处理
        from users.profiles.models import UserProfile
        from users.preferences.models import UserPreference
        from users.wallets.models import UserWallet
        
        # 创建相关数据
        profile = UserProfile.objects.create(user=self.user)
        preference = UserPreference.objects.create(user=self.user)
        wallet = UserWallet.objects.create(user=self.user)
        
        user_id = self.user.id
        
        # 删除用户
        self.user.delete()
        
        # 验证相关数据也被删除（级联删除）
        self.assertFalse(UserProfile.objects.filter(user_id=user_id).exists())
        self.assertFalse(UserPreference.objects.filter(user_id=user_id).exists())
        self.assertFalse(UserWallet.objects.filter(user_id=user_id).exists())
    
    def test_api_error_consistency(self):
        """测试API错误响应一致性"""
        # 测试不同模块的错误响应格式是否一致
        
        # 1. 访问不存在的资料
        response = self.client.get(
            reverse('profiles-detail', kwargs={'pk': 99999})
        )
        self.assert_api_not_found(response)
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
        
        # 2. 访问不存在的偏好
        response = self.client.get(
            reverse('preferences-detail', kwargs={'pk': 99999})
        )
        self.assert_api_not_found(response)
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
        
        # 3. 访问不存在的钱包
        response = self.client.get(
            reverse('wallets-detail', kwargs={'pk': 99999})
        )
        self.assert_api_not_found(response)
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
    
    def test_validation_error_consistency(self):
        """测试验证错误一致性"""
        # 测试不同模块的验证错误格式是否一致
        
        # 1. 资料验证错误
        invalid_profile_data = {
            'birth_date': '2030-01-01'  # 未来日期
        }
        
        response = self.client.patch(
            reverse('profiles-update-my-profile'),
            invalid_profile_data,
            format='json'
        )
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
        
        # 2. 偏好验证错误
        invalid_preference_data = {
            'theme': 'invalid_theme'
        }
        
        response = self.client.patch(
            reverse('preferences-update-my-preferences'),
            invalid_preference_data,
            format='json'
        )
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
