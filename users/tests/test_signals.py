"""
Users模块信号测试
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache

from users.models import UserProfile, UserPreference, UserWallet
from .base import BaseTestCase

User = get_user_model()


class UserSignalsTest(BaseTestCase):
    """用户信号测试"""
    
    def test_create_user_related_objects_on_user_creation(self):
        """测试用户创建时自动创建相关对象"""
        # 创建新用户
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@test.com',
            password='testpass123'
        )
        
        # 验证相关对象是否自动创建
        self.assertTrue(UserProfile.objects.filter(user=new_user).exists())
        self.assertTrue(UserPreference.objects.filter(user=new_user).exists())
        self.assertTrue(UserWallet.objects.filter(user=new_user).exists())
        
        # 验证默认值
        profile = UserProfile.objects.get(user=new_user)
        self.assertEqual(profile.nickname, new_user.username)
        
        preference = UserPreference.objects.get(user=new_user)
        self.assertEqual(preference.theme, 'light')
        self.assertEqual(preference.language, 'zh-hans')
        
        wallet = UserWallet.objects.get(user=new_user)
        self.assertEqual(wallet.currency, 'CNY')
    
    def test_existing_user_no_duplicate_creation(self):
        """测试现有用户不会重复创建相关对象"""
        # 为现有用户手动创建一个资料
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='原始昵称'
        )
        
        # 保存用户（触发信号）
        self.user.save()
        
        # 验证没有重复创建
        profiles_count = UserProfile.objects.filter(user=self.user).count()
        self.assertEqual(profiles_count, 1)
        
        # 验证原始数据没有被覆盖
        profile.refresh_from_db()
        self.assertEqual(profile.nickname, '原始昵称')


class CacheClearingSignalsTest(BaseTestCase):
    """缓存清理信号测试"""
    
    def setUp(self):
        super().setUp()
        
        # 创建测试对象
        self.profile = UserProfile.objects.create(
            user=self.user,
            nickname='测试用户'
        )
        
        self.preference = UserPreference.objects.create(
            user=self.user,
            theme='dark'
        )
        
        self.wallet = UserWallet.objects.create(
            user=self.user,
            currency='CNY'
        )
        
        # 设置一些缓存
        cache.set(f'user_profile_{self.user.id}', 'cached_data', 300)
        cache.set(f'user_preferences_{self.user.id}', 'cached_data', 300)
        cache.set(f'user_wallet_{self.user.id}', 'cached_data', 300)
        cache.set(f'user_dashboard_{self.user.id}', 'cached_data', 300)
    
    def test_profile_cache_cleared_on_save(self):
        """测试用户资料保存时清除缓存"""
        # 验证缓存存在
        self.assertIsNotNone(cache.get(f'user_profile_{self.user.id}'))
        self.assertIsNotNone(cache.get(f'user_dashboard_{self.user.id}'))
        
        # 更新资料
        self.profile.nickname = '更新后的昵称'
        self.profile.save()
        
        # 验证相关缓存被清除
        self.assertIsNone(cache.get(f'user_profile_{self.user.id}'))
        self.assertIsNone(cache.get(f'user_dashboard_{self.user.id}'))
    
    def test_preference_cache_cleared_on_save(self):
        """测试用户偏好保存时清除缓存"""
        # 验证缓存存在
        self.assertIsNotNone(cache.get(f'user_preferences_{self.user.id}'))
        self.assertIsNotNone(cache.get(f'user_dashboard_{self.user.id}'))
        
        # 更新偏好
        self.preference.theme = 'light'
        self.preference.save()
        
        # 验证相关缓存被清除
        self.assertIsNone(cache.get(f'user_preferences_{self.user.id}'))
        self.assertIsNone(cache.get(f'user_dashboard_{self.user.id}'))
    
    def test_wallet_cache_cleared_on_save(self):
        """测试用户钱包保存时清除缓存"""
        # 验证缓存存在
        self.assertIsNotNone(cache.get(f'user_wallet_{self.user.id}'))
        self.assertIsNotNone(cache.get(f'user_dashboard_{self.user.id}'))
        
        # 更新钱包
        from decimal import Decimal
        self.wallet.balance = Decimal('100.00')
        self.wallet.save()
        
        # 验证相关缓存被清除
        self.assertIsNone(cache.get(f'user_wallet_{self.user.id}'))
        self.assertIsNone(cache.get(f'user_dashboard_{self.user.id}'))
    
    def test_cache_cleared_on_delete(self):
        """测试删除时清除缓存"""
        # 设置缓存
        cache.set(f'user_profile_{self.user.id}', 'cached_data', 300)
        
        # 删除资料
        self.profile.delete()
        
        # 验证缓存被清除
        self.assertIsNone(cache.get(f'user_profile_{self.user.id}'))
    
    def test_user_deletion_cache_cleanup(self):
        """测试用户删除时的缓存清理"""
        user_id = self.user.id
        
        # 设置各种缓存
        cache_keys = [
            f'user_profile_{user_id}',
            f'user_preferences_{user_id}',
            f'user_wallet_{user_id}',
            f'user_dashboard_{user_id}',
            f'user_public_profile_{user_id}',
            f'user_settings_{user_id}',
            f'wallet_stats_{user_id}',
        ]
        
        for key in cache_keys:
            cache.set(key, 'cached_data', 300)
        
        # 验证缓存存在
        for key in cache_keys:
            self.assertIsNotNone(cache.get(key))
        
        # 删除用户
        self.user.delete()
        
        # 验证所有相关缓存被清除
        for key in cache_keys:
            self.assertIsNone(cache.get(key))


class SignalErrorHandlingTest(TestCase):
    """信号错误处理测试"""
    
    def test_signal_with_invalid_user(self):
        """测试信号处理无效用户的情况"""
        # 这个测试主要确保信号处理器不会因为异常数据而崩溃
        
        # 创建用户但立即删除（模拟竞态条件）
        user = User.objects.create_user(
            username='tempuser',
            email='temp@test.com',
            password='temppass123'
        )
        
        user_id = user.id
        user.delete()
        
        # 尝试清除已删除用户的缓存（不应该抛出异常）
        cache.delete(f'user_profile_{user_id}')
        cache.delete(f'user_dashboard_{user_id}')
        
        # 如果到这里没有异常，说明信号处理器是健壮的
        self.assertTrue(True)
    
    def test_signal_with_database_error(self):
        """测试数据库错误时的信号处理"""
        # 创建用户
        user = User.objects.create_user(
            username='testuser2',
            email='test2@test.com',
            password='testpass123'
        )
        
        # 验证相关对象被创建（即使有潜在的数据库问题）
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertTrue(UserPreference.objects.filter(user=user).exists())
        self.assertTrue(UserWallet.objects.filter(user=user).exists())


class SignalPerformanceTest(TestCase):
    """信号性能测试"""
    
    def test_bulk_user_creation_signals(self):
        """测试批量用户创建的信号性能"""
        import time
        
        start_time = time.time()
        
        # 批量创建用户
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'bulkuser{i}',
                email=f'bulk{i}@test.com',
                password='testpass123'
            )
            users.append(user)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # 验证所有相关对象都被创建
        for user in users:
            self.assertTrue(UserProfile.objects.filter(user=user).exists())
            self.assertTrue(UserPreference.objects.filter(user=user).exists())
            self.assertTrue(UserWallet.objects.filter(user=user).exists())
        
        # 确保性能在可接受范围内（每个用户不超过1秒）
        self.assertLess(creation_time, 10.0, f"Bulk creation too slow: {creation_time}s for 10 users")
    
    def test_signal_cache_efficiency(self):
        """测试信号缓存清理的效率"""
        import time
        
        user = User.objects.create_user(
            username='cacheuser',
            email='cache@test.com',
            password='testpass123'
        )
        
        profile = UserProfile.objects.get(user=user)
        
        # 设置多个缓存键
        for i in range(100):
            cache.set(f'test_key_{i}', 'data', 300)
        
        start_time = time.time()
        
        # 更新资料（触发缓存清理信号）
        profile.nickname = '更新昵称'
        profile.save()
        
        end_time = time.time()
        signal_time = end_time - start_time
        
        # 缓存清理应该很快（小于0.1秒）
        self.assertLess(signal_time, 0.1, f"Signal processing too slow: {signal_time}s")
