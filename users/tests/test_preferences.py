"""
用户偏好子模块测试
"""

from django.urls import reverse
from rest_framework import status

from .base import BaseAPITestCase, TestDataFactory


class UserPreferenceAPITest(BaseAPITestCase):
    """用户偏好API测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
        self.preference_data = TestDataFactory.create_preference_data()
    
    def test_my_preferences_get(self):
        """测试获取我的偏好设置"""
        url = reverse('userpreference-my-preferences')
        response = self.client.get(url)
        
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertEqual(data['user'], self.user.id)
        self.assertIn('theme', data)
        self.assertIn('language', data)
    
    def test_my_preferences_update(self):
        """测试更新我的偏好设置"""
        url = reverse('userpreference-update-my-preferences')
        response = self.client.put(url, self.preference_data, format='json')
        
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertEqual(data['theme'], 'dark')
        self.assertEqual(data['language'], 'en')
        self.assertEqual(data['timezone'], 'America/New_York')
    
    def test_update_notifications(self):
        """测试更新通知设置"""
        from users.preferences.models import UserPreference
        
        preference = UserPreference.objects.create(user=self.user)
        
        url = reverse('preferences-update-notifications', kwargs={'pk': preference.id})
        
        notification_data = {
            'notification_types': {
                'messages': True,
                'likes': False,
                'comments': True
            }
        }
        
        response = self.client.patch(url, notification_data, format='json')
        self.assert_api_success(response)
        
        # 验证设置已更新
        preference.refresh_from_db()
        self.assertTrue(preference.get_notification_setting('messages'))
        self.assertFalse(preference.get_notification_setting('likes'))
        self.assertTrue(preference.get_notification_setting('comments'))
    
    def test_custom_settings(self):
        """测试自定义设置"""
        from users.preferences.models import UserPreference
        
        preference = UserPreference.objects.create(user=self.user)
        
        url = reverse('preferences-update-custom-settings', kwargs={'pk': preference.id})
        
        custom_data = {
            'custom_settings': {
                'custom_key1': 'value1',
                'custom_key2': 'value2'
            }
        }
        
        response = self.client.patch(url, custom_data, format='json')
        self.assert_api_success(response)
    
    def test_reset_to_defaults(self):
        """测试重置为默认设置"""
        from users.preferences.models import UserPreference
        
        preference = UserPreference.objects.create(
            user=self.user,
            theme='dark',
            language='en',
            email_notifications=False
        )
        
        url = reverse('preferences-reset-to-defaults', kwargs={'pk': preference.id})
        
        response = self.client.post(url)
        self.assert_api_success(response)
        
        # 验证已重置为默认值
        preference.refresh_from_db()
        self.assertEqual(preference.theme, 'light')
        self.assertEqual(preference.language, 'zh-hans')
        self.assertTrue(preference.email_notifications)
    
    def test_export_settings(self):
        """测试导出设置"""
        from users.preferences.models import UserPreference
        
        preference = UserPreference.objects.create(
            user=self.user,
            **self.preference_data
        )
        
        url = reverse('preferences-export-settings', kwargs={'pk': preference.id})
        
        response = self.client.get(url)
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertIn('export_data', data)
        self.assertIsInstance(data['export_data'], dict)
    
    def test_import_settings(self):
        """测试导入设置"""
        from users.preferences.models import UserPreference
        
        preference = UserPreference.objects.create(user=self.user)
        
        url = reverse('preferences-import-settings', kwargs={'pk': preference.id})
        
        import_data = {
            'settings_data': {
                'theme': 'dark',
                'language': 'en',
                'email_notifications': False
            }
        }
        
        response = self.client.post(url, import_data, format='json')
        self.assert_api_success(response)
        
        # 验证设置已导入
        preference.refresh_from_db()
        self.assertEqual(preference.theme, 'dark')
        self.assertEqual(preference.language, 'en')
        self.assertFalse(preference.email_notifications)
    
    def test_available_options(self):
        """测试获取可用选项"""
        url = reverse('preferences-available-options')
        
        response = self.client.get(url)
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertIn('themes', data)
        self.assertIn('languages', data)
        self.assertIn('timezones', data)
        self.assertIn('notification_types', data)
        
        # 验证选项格式
        themes = data['themes']
        self.assertIsInstance(themes, list)
        if themes:
            theme = themes[0]
            self.assertIn('value', theme)
            self.assertIn('label', theme)


class UserPreferenceValidationTest(BaseAPITestCase):
    """用户偏好验证测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
    
    def test_invalid_theme(self):
        """测试无效主题"""
        data = {'theme': 'invalid_theme'}
        
        url = reverse('userpreference-update-my-preferences')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_language(self):
        """测试无效语言"""
        data = {'language': 'invalid_lang'}
        
        url = reverse('userpreference-update-my-preferences')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_timezone(self):
        """测试无效时区"""
        data = {'timezone': 'Invalid/Timezone'}
        
        url = reverse('userpreference-update-my-preferences')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_items_per_page(self):
        """测试无效每页显示条数"""
        data = {'items_per_page': 200}  # 超过最大值
        
        url = reverse('userpreference-update-my-preferences')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_valid_data(self):
        """测试有效数据"""
        data = {
            'theme': 'dark',
            'language': 'en',
            'timezone': 'America/New_York',
            'items_per_page': 25
        }
        
        url = reverse('userpreference-update-my-preferences')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_success(response)


class UserPreferencePermissionTest(BaseAPITestCase):
    """用户偏好权限测试"""
    
    def setUp(self):
        super().setUp()
        from users.preferences.models import UserPreference
        
        self.preference = UserPreference.objects.create(user=self.user)
        self.other_preference = UserPreference.objects.create(user=self.other_user)
    
    def test_owner_access(self):
        """测试所有者访问权限"""
        self.authenticate_user(self.user)
        
        url = reverse('userpreference-detail', kwargs={'pk': self.preference.id})
        response = self.client.get(url)
        
        self.assert_api_success(response)
    
    def test_other_user_access(self):
        """测试其他用户访问权限"""
        self.authenticate_user(self.other_user)
        
        url = reverse('userpreference-detail', kwargs={'pk': self.preference.id})
        response = self.client.get(url)
        
        self.assert_api_forbidden(response)
    
    def test_admin_access(self):
        """测试管理员访问权限"""
        self.authenticate_user(self.admin_user)
        
        url = reverse('userpreference-detail', kwargs={'pk': self.preference.id})
        response = self.client.get(url)
        
        self.assert_api_success(response)
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        url = reverse('userpreference-detail', kwargs={'pk': self.preference.id})
        response = self.client.get(url)
        
        self.assert_api_unauthorized(response)
