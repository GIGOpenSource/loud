"""
测试基础类和工具
提供测试所需的基础设施和工具方法
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from authentication.models import AuthToken
from authentication.cookie_utils import SecureCookieManager
import json

User = get_user_model()


class BaseTestCase(TestCase):
    """测试基础类"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='13800138000'
        )
        
        cls.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        cls.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
    
    def setUp(self):
        """每个测试前的设置"""
        self.user.refresh_from_db()
        self.admin_user.refresh_from_db()
        self.other_user.refresh_from_db()
        
        # 清理可能存在的自动创建对象，避免测试中的约束冲突
        from users.models import UserProfile, UserPreference, UserWallet
        UserProfile.objects.filter(user=self.user).delete()
        UserPreference.objects.filter(user=self.user).delete()
        UserWallet.objects.filter(user=self.user).delete()


class BaseAPITestCase(APITestCase):
    """API测试基础类"""
    
    @classmethod
    def setUpTestData(cls):
        """设置测试数据"""
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='13800138000'
        )
        
        cls.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        cls.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
    
    def setUp(self):
        """每个测试前的设置"""
        self.client = APIClient()
        self.user.refresh_from_db()
        self.admin_user.refresh_from_db()
        self.other_user.refresh_from_db()
        
        # 清理可能存在的自动创建对象，避免测试中的约束冲突
        from users.models import UserProfile, UserPreference, UserWallet
        UserProfile.objects.filter(user__in=[self.user, self.other_user, self.admin_user]).delete()
        UserPreference.objects.filter(user__in=[self.user, self.other_user, self.admin_user]).delete()
        UserWallet.objects.filter(user__in=[self.user, self.other_user, self.admin_user]).delete()
    
    def authenticate_user(self, user=None):
        """认证用户"""
        if user is None:
            user = self.user
        
        # 创建访问令牌
        access_token, refresh_token = AuthToken.create_token_pair(user)
        
        # 设置认证头
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token.token}')
        
        return access_token, refresh_token
    
    def logout_user(self):
        """登出用户"""
        self.client.credentials()
    
    def assert_api_success(self, response, status_code=status.HTTP_200_OK):
        """断言API成功响应"""
        self.assertEqual(response.status_code, status_code)
        self.assertTrue(response.data.get('success', False))
        self.assertIsNotNone(response.data.get('data'))
    
    def assert_api_error(self, response, status_code=status.HTTP_400_BAD_REQUEST):
        """断言API错误响应"""
        self.assertEqual(response.status_code, status_code)
        self.assertFalse(response.data.get('success', True))
    
    def assert_api_unauthorized(self, response):
        """断言未授权响应"""
        # 接受401或403状态码，因为不同的认证机制可能返回不同状态码
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def assert_api_forbidden(self, response):
        """断言禁止访问响应"""
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def assert_api_not_found(self, response):
        """断言未找到响应"""
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DatabaseTestCase(TransactionTestCase):
    """数据库事务测试基础类"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def setUp(self):
        """每个测试前的设置"""
        self.user.refresh_from_db()


class MockTestCase(TestCase):
    """Mock测试基础类"""
    
    def setUp(self):
        """每个测试前的设置"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )


class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_user(username='testuser', email='test@example.com', **kwargs):
        """创建测试用户"""
        defaults = {
            'password': 'testpass123',
            'is_active': True
        }
        defaults.update(kwargs)
        
        return User.objects.create_user(
            username=username,
            email=email,
            **defaults
        )
    
    @staticmethod
    def create_profile_data():
        """创建用户资料测试数据"""
        return {
            'nickname': '测试昵称',
            'bio': '这是一个测试用户的个人简介',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'country': '中国',
            'province': '北京市',
            'city': '北京',
            'address': '测试地址',
            'website': 'https://example.com',
            'twitter': 'https://twitter.com/testuser',
            'github': 'https://github.com/testuser',
            'profile_visibility': 'public',
            'show_email': False,
            'show_phone': False
        }
    
    @staticmethod
    def create_preference_data():
        """创建用户偏好测试数据"""
        return {
            'theme': 'dark',
            'language': 'en',
            'timezone': 'America/New_York',
            'email_notifications': True,
            'push_notifications': False,
            'sms_notifications': False,
            'show_online_status': True,
            'allow_friend_requests': True,
            'allow_messages_from_strangers': False,
            'auto_save_drafts': True,
            'enable_keyboard_shortcuts': True,
            'items_per_page': 25,
            'notification_types': {
                'system_updates': True,
                'security_alerts': True,
                'account_changes': False,
                'friend_requests': True,
                'messages': True,
                'mentions': False,
                'likes': False,
                'comments': True,
                'marketing': False,
                'newsletters': False
            },
            'custom_settings': {
                'custom_field1': 'value1',
                'custom_field2': 'value2'
            }
        }
    
    @staticmethod
    def create_wallet_data():
        """创建用户钱包测试数据"""
        return {
            'currency': 'USD',
            'daily_limit': '5000.00',
            'monthly_limit': '50000.00'
        }


class TestUtils:
    """测试工具类"""
    
    @staticmethod
    def get_response_data(response):
        """获取响应数据"""
        if hasattr(response, 'data'):
            return response.data
        return json.loads(response.content)
    
    @staticmethod
    def create_test_image():
        """创建测试图片"""
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # 创建一个简单的测试图片
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        return SimpleUploadedFile(
            'test_image.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    @staticmethod
    def create_large_test_image():
        """创建大尺寸测试图片"""
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # 创建一个大尺寸的测试图片
        image = Image.new('RGB', (2000, 2000), color='blue')
        image_io = BytesIO()
        image.save(image_io, format='JPEG', quality=100)
        image_io.seek(0)
        
        return SimpleUploadedFile(
            'large_test_image.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    @staticmethod
    def create_invalid_image():
        """创建无效的图片文件"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        return SimpleUploadedFile(
            'invalid_image.txt',
            b'This is not an image file',
            content_type='text/plain'
        )
