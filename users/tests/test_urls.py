"""
Users模块URL配置测试
"""

from django.test import TestCase
from django.urls import reverse, resolve
from django.conf import settings

class UserURLsTest(TestCase):
    """用户URL测试"""
    
    def test_main_user_urls(self):
        """测试主要用户URL"""
        # 测试用户仪表板
        url = reverse('user-dashboard')
        self.assertEqual(url, '/api/users/dashboard/')
        
        # 测试用户概览
        url = reverse('user-overview')
        self.assertEqual(url, '/api/users/overview/')
        
        # 测试用户验证
        url = reverse('verify-user')
        self.assertEqual(url, '/api/users/verify/')
        
        # 测试模块信息
        url = reverse('module-info')
        self.assertEqual(url, '/api/users/module-info/')
    
    def test_profile_urls(self):
        """测试用户资料URL"""
        # 测试资料列表
        url = reverse('profiles-list')
        self.assertEqual(url, '/api/users/profiles/')
        
        # 测试我的资料
        url = reverse('profiles-my-profile')
        self.assertEqual(url, '/api/users/profiles/my_profile/')
        
        # 测试更新我的资料
        url = reverse('profiles-update-my-profile')
        self.assertEqual(url, '/api/users/profiles/update_my_profile/')
        
        # 测试公开资料
        url = reverse('public-profile', kwargs={'user_id': 1})
        self.assertEqual(url, '/api/users/public/1/')
    
    def test_preference_urls(self):
        """测试用户偏好URL"""
        # 测试偏好列表
        url = reverse('preferences-list')
        self.assertEqual(url, '/api/users/preferences/')
        
        # 测试我的偏好
        url = reverse('preferences-my-preferences')
        self.assertEqual(url, '/api/users/preferences/my_preferences/')
        
        # 测试更新我的偏好
        url = reverse('preferences-update-my-preferences')
        self.assertEqual(url, '/api/users/preferences/update_my_preferences/')
    
    def test_wallet_urls(self):
        """测试用户钱包URL"""
        # 测试钱包列表
        url = reverse('wallets-list')
        self.assertEqual(url, '/api/users/wallets/')
        
        # 测试我的钱包
        url = reverse('wallets-my-wallet')
        self.assertEqual(url, '/api/users/wallets/my_wallet/')
        
        # 测试钱包操作
        url = reverse('wallets-deposit', kwargs={'pk': 1})
        self.assertEqual(url, '/api/users/wallets/1/deposit/')
        
        url = reverse('wallets-withdraw', kwargs={'pk': 1})
        self.assertEqual(url, '/api/users/wallets/1/withdraw/')
        
        url = reverse('wallets-transfer', kwargs={'pk': 1})
        self.assertEqual(url, '/api/users/wallets/1/transfer/')
    
    def test_transaction_urls(self):
        """测试交易URL"""
        # 测试交易列表
        url = reverse('transactions-list')
        self.assertEqual(url, '/api/users/transactions/')
        
        # 测试我的交易
        url = reverse('transactions-my-transactions')
        self.assertEqual(url, '/api/users/transactions/my_transactions/')
        
        # 测试交易摘要
        url = reverse('transactions-transaction-summary')
        self.assertEqual(url, '/api/users/transactions/transaction_summary/')


class URLResolutionTest(TestCase):
    """URL解析测试"""
    
    def test_user_dashboard_resolution(self):
        """测试用户仪表板URL解析"""
        resolved = resolve('/api/users/dashboard/')
        self.assertEqual(resolved.view_name, 'users:user-dashboard')
    
    def test_user_overview_resolution(self):
        """测试用户概览URL解析"""
        resolved = resolve('/api/users/overview/')
        self.assertEqual(resolved.view_name, 'users:user-overview')
    
    def test_verify_user_resolution(self):
        """测试用户验证URL解析"""
        resolved = resolve('/api/users/verify/')
        self.assertEqual(resolved.view_name, 'users:verify-user')
    
    def test_module_info_resolution(self):
        """测试模块信息URL解析"""
        resolved = resolve('/api/users/module-info/')
        self.assertEqual(resolved.view_name, 'users:module-info')
    
    def test_profile_urls_resolution(self):
        """测试用户资料URL解析"""
        # 资料列表
        resolved = resolve('/api/users/profiles/')
        self.assertEqual(resolved.view_name, 'profiles-list')
        
        # 我的资料
        resolved = resolve('/api/users/profiles/my_profile/')
        self.assertEqual(resolved.view_name, 'profiles-my-profile')
        
        # 公开资料
        resolved = resolve('/api/users/public/123/')
        self.assertEqual(resolved.view_name, 'public-profile')
        self.assertEqual(resolved.kwargs['user_id'], '123')
    
    def test_preference_urls_resolution(self):
        """测试用户偏好URL解析"""
        # 偏好列表
        resolved = resolve('/api/users/preferences/')
        self.assertEqual(resolved.view_name, 'preferences-list')
        
        # 我的偏好
        resolved = resolve('/api/users/preferences/my_preferences/')
        self.assertEqual(resolved.view_name, 'preferences-my-preferences')
    
    def test_wallet_urls_resolution(self):
        """测试用户钱包URL解析"""
        # 钱包列表
        resolved = resolve('/api/users/wallets/')
        self.assertEqual(resolved.view_name, 'wallets-list')
        
        # 我的钱包
        resolved = resolve('/api/users/wallets/my_wallet/')
        self.assertEqual(resolved.view_name, 'wallets-my-wallet')
        
        # 钱包操作
        resolved = resolve('/api/users/wallets/123/deposit/')
        self.assertEqual(resolved.view_name, 'wallets-deposit')
        self.assertEqual(resolved.kwargs['pk'], '123')
        
        resolved = resolve('/api/users/wallets/456/withdraw/')
        self.assertEqual(resolved.view_name, 'wallets-withdraw')
        self.assertEqual(resolved.kwargs['pk'], '456')
    
    def test_transaction_urls_resolution(self):
        """测试交易URL解析"""
        # 交易列表
        resolved = resolve('/api/users/transactions/')
        self.assertEqual(resolved.view_name, 'transactions-list')
        
        # 我的交易
        resolved = resolve('/api/users/transactions/my_transactions/')
        self.assertEqual(resolved.view_name, 'transactions-my-transactions')
        
        # 退款
        resolved = resolve('/api/users/transactions/789/refund/')
        self.assertEqual(resolved.view_name, 'transactions-refund')
        self.assertEqual(resolved.kwargs['pk'], '789')


class URLNamespaceTest(TestCase):
    """URL命名空间测试"""
    
    def test_users_namespace(self):
        """测试users命名空间"""
        # 验证命名空间存在
        try:
            url = reverse('user-dashboard')
            self.assertTrue(url.startswith('/api/users/'))
        except Exception:
            self.fail("users namespace not properly configured")
    
    def test_profile_namespace(self):
        """测试profile相关URL命名"""
        # 验证profile相关的URL都能正确解析
        profile_urls = [
            'profiles-list',
            'profiles-my-profile',
            'profiles-update-my-profile',
            'public-profile'
        ]
        
        for url_name in profile_urls:
            try:
                if url_name == 'public-profile':
                    url = reverse(url_name, kwargs={'user_id': 1})
                else:
                    url = reverse(url_name)
                self.assertTrue(url.startswith('/api/users/'))
            except Exception as e:
                self.fail(f"URL {url_name} not properly configured: {e}")
    
    def test_preference_namespace(self):
        """测试preference相关URL命名"""
        preference_urls = [
            'preferences-list',
            'preferences-my-preferences',
            'preferences-update-my-preferences',
            'preferences-available-options'
        ]
        
        for url_name in preference_urls:
            try:
                url = reverse(url_name)
                self.assertTrue(url.startswith('/api/users/'))
            except Exception as e:
                self.fail(f"URL {url_name} not properly configured: {e}")
    
    def test_wallet_namespace(self):
        """测试wallet相关URL命名"""
        wallet_urls = [
            'wallets-list',
            'wallets-my-wallet',
            'wallets-available-currencies'
        ]
        
        for url_name in wallet_urls:
            try:
                url = reverse(url_name)
                self.assertTrue(url.startswith('/api/users/'))
            except Exception as e:
                self.fail(f"URL {url_name} not properly configured: {e}")


class URLParameterTest(TestCase):
    """URL参数测试"""
    
    def test_profile_detail_with_pk(self):
        """测试带主键的资料详情URL"""
        url = reverse('profiles-detail', kwargs={'pk': 123})
        self.assertEqual(url, '/api/users/profiles/123/')
        
        resolved = resolve(url)
        self.assertEqual(resolved.kwargs['pk'], '123')
    
    def test_public_profile_with_user_id(self):
        """测试带用户ID的公开资料URL"""
        url = reverse('public-profile', kwargs={'user_id': 456})
        self.assertEqual(url, '/api/users/public/456/')
        
        resolved = resolve(url)
        self.assertEqual(resolved.kwargs['user_id'], '456')
    
    def test_wallet_actions_with_pk(self):
        """测试带主键的钱包操作URL"""
        actions = ['deposit', 'withdraw', 'transfer', 'freeze', 'unfreeze', 'stats']
        
        for action in actions:
            url_name = f'wallets-{action}'
            url = reverse(url_name, kwargs={'pk': 789})
            expected_url = f'/api/users/wallets/789/{action}/'
            self.assertEqual(url, expected_url)
            
            resolved = resolve(url)
            self.assertEqual(resolved.kwargs['pk'], '789')
    
    def test_transaction_refund_with_pk(self):
        """测试带主键的交易退款URL"""
        url = reverse('transactions-refund', kwargs={'pk': 999})
        self.assertEqual(url, '/api/users/transactions/999/refund/')
        
        resolved = resolve(url)
        self.assertEqual(resolved.kwargs['pk'], '999')


class URLSecurityTest(TestCase):
    """URL安全测试"""
    
    def test_no_sensitive_info_in_urls(self):
        """测试URL中不包含敏感信息"""
        # 验证URL不包含敏感信息
        sensitive_patterns = ['password', 'secret', 'key', 'token']
        
        # 获取所有URL
        all_urls = [
            reverse('users:user-dashboard'),
            reverse('users:user-overview'),
            reverse('users:verify-user'),
            reverse('users:module-info'),
            reverse('profiles-list'),
            reverse('preferences-list'),
            reverse('wallets-list'),
            reverse('transactions-list'),
        ]
        
        for url in all_urls:
            for pattern in sensitive_patterns:
                self.assertNotIn(pattern, url.lower(), 
                    f"URL {url} contains sensitive pattern {pattern}")
    
    def test_url_length_limits(self):
        """测试URL长度限制"""
        # 验证URL长度在合理范围内
        all_urls = [
            reverse('users:user-dashboard'),
            reverse('profiles-my-profile'),
            reverse('preferences-update-my-preferences'),
            reverse('wallets-my-wallet'),
            reverse('transactions-transaction-summary'),
        ]
        
        for url in all_urls:
            self.assertLess(len(url), 100, f"URL too long: {url}")
    
    def test_url_special_characters(self):
        """测试URL特殊字符处理"""
        # 验证URL只包含安全字符
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/.?=&')
        
        all_urls = [
            reverse('users:user-dashboard'),
            reverse('profiles-list'),
            reverse('preferences-list'),
            reverse('wallets-list'),
        ]
        
        for url in all_urls:
            url_chars = set(url)
            unsafe_chars = url_chars - safe_chars
            self.assertEqual(len(unsafe_chars), 0, 
                f"URL {url} contains unsafe characters: {unsafe_chars}")
