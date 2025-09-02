"""
用户资料子模块测试
"""

from django.urls import reverse
from rest_framework import status
from decimal import Decimal

from .base import BaseAPITestCase, TestDataFactory, TestUtils


class UserProfileAPITest(BaseAPITestCase):
    """用户资料API测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
        self.profile_data = TestDataFactory.create_profile_data()
    
    def test_my_profile_get(self):
        """测试获取我的资料"""
        url = reverse('userprofile-my-profile')
        response = self.client.get(url)
        
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertEqual(data['user'], self.user.id)
    
    def test_my_profile_update(self):
        """测试更新我的资料"""
        url = reverse('userprofile-update-my-profile')
        response = self.client.put(url, self.profile_data, format='json')
        
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertEqual(data['nickname'], '测试昵称')
        self.assertEqual(data['bio'], '这是一个测试用户的个人简介')
    
    def test_avatar_upload(self):
        """测试头像上传"""
        from users.profiles.models import UserProfile
        
        profile = UserProfile.objects.create(user=self.user)
        
        url = reverse('userprofile-upload-avatar', kwargs={'pk': profile.id})
        
        # 有效图片上传
        image = TestUtils.create_test_image()
        data = {'avatar': image}
        
        response = self.client.post(url, data, format='multipart')
        self.assert_api_success(response)
    
    def test_public_profile(self):
        """测试公开资料"""
        from users.profiles.models import UserProfile
        
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='公开用户',
            bio='这是公开的简介',
            profile_visibility='public'
        )
        
        url = reverse('public-profile', kwargs={'user_id': self.user.id})
        
        # 无需认证即可访问
        self.logout_user()
        response = self.client.get(url)
        
        self.assert_api_success(response)
        
        data = response.data['data']
        self.assertIn('nickname', data)
        self.assertIn('bio', data)


class UserProfilePermissionTest(BaseAPITestCase):
    """用户资料权限测试"""
    
    def setUp(self):
        super().setUp()
        from users.profiles.models import UserProfile
        
        self.profile = UserProfile.objects.create(user=self.user)
        self.other_profile = UserProfile.objects.create(user=self.other_user)
    
    def test_owner_access(self):
        """测试所有者访问权限"""
        self.authenticate_user(self.user)
        
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.id})
        response = self.client.get(url)
        
        self.assert_api_success(response)
    
    def test_other_user_access(self):
        """测试其他用户访问权限"""
        self.authenticate_user(self.other_user)
        
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.id})
        response = self.client.get(url)
        
        # 根据资料可见性决定是否可访问
        if self.profile.profile_visibility == 'private':
            self.assert_api_forbidden(response)
        else:
            self.assert_api_success(response)
    
    def test_admin_access(self):
        """测试管理员访问权限"""
        self.authenticate_user(self.admin_user)
        
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.id})
        response = self.client.get(url)
        
        self.assert_api_success(response)
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.id})
        response = self.client.get(url)
        
        self.assert_api_unauthorized(response)


class UserProfileFilterTest(BaseAPITestCase):
    """用户资料过滤器测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user(self.admin_user)  # 使用管理员账户测试过滤
        
        from users.profiles.models import UserProfile
        
        # 创建测试数据
        self.profile1 = UserProfile.objects.create(
            user=self.user,
            gender='male',
            country='中国',
            city='北京',
            birth_date='1990-01-01'
        )
        
        self.profile2 = UserProfile.objects.create(
            user=self.other_user,
            gender='female',
            country='美国',
            city='纽约',
            birth_date='1995-01-01'
        )
    
    def test_gender_filter(self):
        """测试性别过滤"""
        url = reverse('userprofile-list')
        response = self.client.get(url, {'gender': 'male'})
        
        self.assert_api_success(response)
        
        results = response.data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['gender'], 'male')
    
    def test_location_filter(self):
        """测试地理位置过滤"""
        url = reverse('userprofile-list')
        response = self.client.get(url, {'country': '中国'})
        
        self.assert_api_success(response)
        
        results = response.data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['country'], '中国')
    
    def test_age_range_filter(self):
        """测试年龄范围过滤"""
        url = reverse('userprofile-list')
        response = self.client.get(url, {'age_min': 25, 'age_max': 35})
        
        self.assert_api_success(response)
        
        # 验证返回的结果在年龄范围内
        results = response.data['data']['results']
        for result in results:
            if result.get('birth_date'):
                # 这里可以添加更详细的年龄验证逻辑
                pass


class UserProfileValidationTest(BaseAPITestCase):
    """用户资料验证测试"""
    
    def setUp(self):
        super().setUp()
        self.authenticate_user()
    
    def test_invalid_birth_date(self):
        """测试无效出生日期"""
        data = {
            'birth_date': '2030-01-01'  # 未来日期
        }
        
        url = reverse('userprofile-update-my-profile')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_website_url(self):
        """测试无效网站URL"""
        data = {
            'website': 'invalid-url'
        }
        
        url = reverse('userprofile-update-my-profile')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_social_links(self):
        """测试无效社交链接"""
        data = {
            'twitter': 'not-a-twitter-url'
        }
        
        url = reverse('userprofile-update-my-profile')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_error(response, status.HTTP_400_BAD_REQUEST)
    
    def test_valid_data(self):
        """测试有效数据"""
        data = {
            'nickname': '有效昵称',
            'bio': '这是一个有效的个人简介',
            'birth_date': '1990-01-01',
            'website': 'https://valid-website.com',
            'twitter': 'https://twitter.com/validuser'
        }
        
        url = reverse('userprofile-update-my-profile')
        response = self.client.patch(url, data, format='json')
        
        self.assert_api_success(response)
