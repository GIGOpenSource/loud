from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    """认证功能测试用例"""
    
    def setUp(self):
        """测试前准备"""
        self.client = APIClient()
        self.register_url = reverse('authentication:register')
        self.login_url = reverse('authentication:login')
        self.logout_url = reverse('authentication:logout')
        self.check_auth_url = reverse('authentication:check_auth')
        
        # 测试用户数据
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'nickname': '测试用户'
        }
    
    def test_user_registration(self):
        """测试用户注册"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data['data'])
        self.assertIn('tokens', response.data['data'])
        self.assertEqual(response.data['message'], '注册成功')
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['code'], 2102)  # REGISTER_SUCCESS
        self.assertEqual(response.data['data']['user']['username'], 'testuser')
        self.assertEqual(response.data['data']['user']['email'], 'test@example.com')
        
        # 验证用户是否真的创建了
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.nickname, '测试用户')
    
    def test_user_registration_duplicate_username(self):
        """测试重复用户名注册"""
        # 先创建一个用户
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='testpass123'
        )
        
        # 尝试用相同用户名注册
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('username', response.data['data'])
    
    def test_user_registration_password_mismatch(self):
        """测试密码不匹配"""
        data = self.user_data.copy()
        data['password_confirm'] = 'wrongpassword'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('non_field_errors', response.data['data'])
    
    def test_user_login(self):
        """测试用户登录"""
        # 先创建用户
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        login_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'remember_me': True
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data['data'])
        self.assertIn('tokens', response.data['data'])
        self.assertEqual(response.data['message'], '登录成功')
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['code'], 2100)  # LOGIN_SUCCESS
        self.assertEqual(response.data['data']['user']['username'], 'testuser')
    
    def test_user_login_invalid_credentials(self):
        """测试无效凭据登录"""
        login_data = {
            'username': 'nonexistent',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_user_logout(self):
        """测试用户登出"""
        # 创建用户并获取token
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '登出成功')
    
    def test_check_auth_status(self):
        """测试认证状态检查"""
        # 创建用户并获取token
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(self.check_auth_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['authenticated'])
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_check_auth_status_unauthenticated(self):
        """测试未认证状态检查"""
        response = self.client.get(self.check_auth_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordTestCase(APITestCase):
    """密码相关功能测试用例"""
    
    def setUp(self):
        """测试前准备"""
        self.client = APIClient()
        self.password_change_url = reverse('authentication:password_change')
        self.password_reset_url = reverse('authentication:password_reset')
        
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123'
        )
        
        # 获取token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_password_change(self):
        """测试密码修改"""
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        
        response = self.client.post(self.password_change_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], '密码修改成功')
        
        # 验证新密码是否生效
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
    
    def test_password_change_wrong_old_password(self):
        """测试密码修改时旧密码错误"""
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        
        response = self.client.post(self.password_change_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)
    
    def test_password_change_password_mismatch(self):
        """测试密码修改时新密码不匹配"""
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'differentpassword'
        }
        
        response = self.client.post(self.password_change_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_password_reset_request(self):
        """测试密码重置请求"""
        data = {'email': 'test@example.com'}
        
        response = self.client.post(self.password_reset_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)


class RoleTestCase(APITestCase):
    """角色管理测试用例"""
    
    def setUp(self):
        """测试前准备"""
        self.client = APIClient()
        self.roles_url = reverse('authentication:role_list')
        self.role_detail_url = reverse('authentication:role_detail', kwargs={'pk': 1})
        
        # 创建管理员用户
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # 获取管理员token
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # 创建测试角色
        from .models import Role
        self.role = Role.objects.create(
            name='测试角色',
            code='test_role',
            description='测试角色描述'
        )
    
    def test_create_role(self):
        """测试创建角色"""
        data = {
            'name': '新角色',
            'code': 'new_role',
            'description': '新角色描述',
            'is_active': True
        }
        
        response = self.client.post(self.roles_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], '新角色')
        self.assertEqual(response.data['code'], 'new_role')
        self.assertEqual(response.data['description'], '新角色描述')
        self.assertTrue(response.data['is_active'])
    
    def test_get_roles_list(self):
        """测试获取角色列表"""
        response = self.client.get(self.roles_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '测试角色')
    
    def test_get_role_detail(self):
        """测试获取角色详情"""
        url = reverse('authentication:role_detail', kwargs={'pk': self.role.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '测试角色')
        self.assertEqual(response.data['code'], 'test_role')
    
    def test_update_role(self):
        """测试更新角色"""
        url = reverse('authentication:role_detail', kwargs={'pk': self.role.pk})
        data = {
            'name': '更新的角色',
            'code': 'test_role',  # 保持原有code
            'description': '更新的描述'
        }
        
        response = self.client.put(url, data, format='json')
        
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '更新的角色')
        self.assertEqual(response.data['description'], '更新的描述')
    
    def test_delete_role(self):
        """测试删除角色"""
        url = reverse('authentication:role_detail', kwargs={'pk': self.role.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 验证角色是否被删除
        from .models import Role
        self.assertFalse(Role.objects.filter(pk=self.role.pk).exists())


class UserModelTestCase(TestCase):
    """用户模型测试用例"""
    
    def setUp(self):
        """测试前准备"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            nickname='测试用户'
        )
    
    def test_user_creation(self):
        """测试用户创建"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.nickname, '测试用户')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_verified)
    
    def test_user_display_name(self):
        """测试用户显示名称"""
        self.assertEqual(self.user.display_name, '测试用户')
        
        # 测试没有昵称时使用用户名
        self.user.nickname = ''
        self.user.save()
        self.assertEqual(self.user.display_name, 'testuser')
    
    def test_user_str_representation(self):
        """测试用户字符串表示"""
        self.assertEqual(str(self.user), 'testuser')
    
    def test_user_has_role(self):
        """测试用户角色检查"""
        from .models import Role
        
        # 创建角色
        role = Role.objects.create(
            name='测试角色',
            code='test_role',
            description='测试角色描述'
        )
        
        # 添加角色给用户
        self.user.roles.add(role)
        
        self.assertTrue(self.user.has_role('test_role'))
        self.assertFalse(self.user.has_role('nonexistent_role'))
    
    def test_user_has_any_role(self):
        """测试用户多角色检查"""
        from .models import Role
        
        # 创建角色
        role1 = Role.objects.create(name='角色1', code='role1')
        role2 = Role.objects.create(name='角色2', code='role2')
        
        # 添加角色给用户
        self.user.roles.add(role1)
        
        self.assertTrue(self.user.has_any_role(['role1', 'role2']))
        self.assertFalse(self.user.has_any_role(['role2', 'role3']))
    
    def test_user_permissions(self):
        """测试用户权限"""
        from .models import Role
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # 创建角色
        role = Role.objects.create(
            name='管理员角色',
            code='admin_role'
        )
        
        # 获取权限
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename='can_manage_users',
            name='Can manage users',
            content_type=content_type
        )
        
        # 给角色添加权限
        role.permissions.add(permission)
        
        # 给用户添加角色
        self.user.roles.add(role)
        
        # 测试权限检查
        self.assertTrue(self.user.has_permission('can_manage_users'))
        self.assertFalse(self.user.has_permission('nonexistent_permission'))
