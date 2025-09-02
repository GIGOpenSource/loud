"""
基础响应工具类测试用例
"""

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .response import (
    BaseApiResponse, BasePaginatedResponse,
    ResponseCode, ResponseMessage,
    success_response, error_response, paginated_response
)

User = get_user_model()


class ResponseCodeTestCase(TestCase):
    """响应状态码测试"""
    
    def test_response_codes(self):
        """测试响应状态码定义"""
        self.assertEqual(ResponseCode.SUCCESS, 2000)
        self.assertEqual(ResponseCode.CREATED, 2001)
        self.assertEqual(ResponseCode.UPDATED, 2002)
        self.assertEqual(ResponseCode.DELETED, 2003)
        self.assertEqual(ResponseCode.BAD_REQUEST, 4000)
        self.assertEqual(ResponseCode.UNAUTHORIZED, 4001)
        self.assertEqual(ResponseCode.FORBIDDEN, 4003)
        self.assertEqual(ResponseCode.NOT_FOUND, 4004)


class ResponseMessageTestCase(TestCase):
    """响应消息测试"""
    
    def test_response_messages(self):
        """测试响应消息定义"""
        self.assertEqual(ResponseMessage.SUCCESS, "操作成功")
        self.assertEqual(ResponseMessage.CREATED, "创建成功")
        self.assertEqual(ResponseMessage.UPDATED, "更新成功")
        self.assertEqual(ResponseMessage.DELETED, "删除成功")


class BaseApiResponseTestCase(TestCase):
    """BaseApiResponse类测试"""
    
    def test_success_response(self):
        """测试成功响应"""
        data = {'user_id': 1, 'username': 'test'}
        response = BaseApiResponse.success(
            data=data,
            message="测试成功",
            code=ResponseCode.SUCCESS
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['code'], ResponseCode.SUCCESS)
        self.assertEqual(response.data['message'], "测试成功")
        self.assertEqual(response.data['data'], data)
    
    def test_created_response(self):
        """测试创建成功响应"""
        data = {'user_id': 1}
        response = BaseApiResponse.created(
            data=data,
            message="用户创建成功"
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['code'], ResponseCode.CREATED)
        self.assertEqual(response.data['message'], "用户创建成功")
        self.assertEqual(response.data['data'], data)
    
    def test_updated_response(self):
        """测试更新成功响应"""
        data = {'user_id': 1, 'nickname': '新昵称'}
        response = BaseApiResponse.updated(
            data=data,
            message="用户信息更新成功"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['code'], ResponseCode.UPDATED)
        self.assertEqual(response.data['message'], "用户信息更新成功")
        self.assertEqual(response.data['data'], data)
    
    def test_deleted_response(self):
        """测试删除成功响应"""
        response = BaseApiResponse.deleted("用户删除成功")
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['code'], ResponseCode.DELETED)
        self.assertEqual(response.data['message'], "用户删除成功")
        self.assertIsNone(response.data['data'])
    
    def test_error_response(self):
        """测试错误响应"""
        response = BaseApiResponse.error(
            message="操作失败",
            code=ResponseCode.BAD_REQUEST
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['code'], ResponseCode.BAD_REQUEST)
        self.assertEqual(response.data['message'], "操作失败")
    
    def test_not_found_response(self):
        """测试资源不存在响应"""
        response = BaseApiResponse.not_found("用户不存在")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['code'], ResponseCode.NOT_FOUND)
        self.assertEqual(response.data['message'], "用户不存在")
    
    def test_unauthorized_response(self):
        """测试未授权响应"""
        response = BaseApiResponse.unauthorized("请先登录")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['code'], ResponseCode.UNAUTHORIZED)
        self.assertEqual(response.data['message'], "请先登录")
    
    def test_forbidden_response(self):
        """测试禁止访问响应"""
        response = BaseApiResponse.forbidden("权限不足")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['code'], ResponseCode.FORBIDDEN)
        self.assertEqual(response.data['message'], "权限不足")
    
    def test_validation_error_response(self):
        """测试数据验证错误响应"""
        errors = {'username': ['用户名不能为空']}
        response = BaseApiResponse.validation_error(
            errors=errors,
            message="数据验证失败"
        )
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['code'], ResponseCode.VALIDATION_ERROR)
        self.assertEqual(response.data['message'], "数据验证失败")
        self.assertEqual(response.data['data'], errors)
    
    def test_internal_error_response(self):
        """测试服务器内部错误响应"""
        response = BaseApiResponse.internal_error("服务器内部错误")
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['code'], ResponseCode.INTERNAL_ERROR)
        self.assertEqual(response.data['message'], "服务器内部错误")


class BasePaginatedResponseTestCase(TestCase):
    """基础分页响应测试"""
    
    def setUp(self):
        """创建测试数据"""
        # 创建测试用户
        for i in range(25):
            User.objects.create_user(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                password='testpass123'
            )
    
    def test_paginated_response(self):
        """测试分页响应"""
        users = User.objects.all().order_by('username')
        response = BasePaginatedResponse.paginate(
            queryset=users,
            page=1,
            page_size=10,
            message="获取用户列表成功"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['code'], ResponseCode.SUCCESS)
        self.assertEqual(response.data['message'], "获取用户列表成功")
        self.assertEqual(len(response.data['data']), 10)
        
        # 检查分页信息
        pagination = response.data['pagination']
        self.assertEqual(pagination['current_page'], 1)
        self.assertEqual(pagination['total_pages'], 3)
        self.assertEqual(pagination['total_count'], 25)
        self.assertEqual(pagination['page_size'], 10)
        self.assertTrue(pagination['has_next'])
        self.assertFalse(pagination['has_previous'])
        self.assertEqual(pagination['next_page'], 2)
    
    def test_paginated_response_page_2(self):
        """测试第二页分页响应"""
        users = User.objects.all().order_by('username')
        response = BasePaginatedResponse.paginate(
            queryset=users,
            page=2,
            page_size=10,
            message="获取用户列表成功"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 10)
        
        # 检查分页信息
        pagination = response.data['pagination']
        self.assertEqual(pagination['current_page'], 2)
        self.assertTrue(pagination['has_next'])
        self.assertTrue(pagination['has_previous'])
        self.assertEqual(pagination['next_page'], 3)
        self.assertEqual(pagination['previous_page'], 1)
    
    def test_paginated_response_invalid_page(self):
        """测试无效页码"""
        users = User.objects.all().order_by('username')
        response = BasePaginatedResponse.paginate(
            queryset=users,
            page=999,  # 无效页码
            page_size=10
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['message'], "页码超出范围")


class ShortcutFunctionsTestCase(TestCase):
    """快捷函数测试"""
    
    def test_success_response_function(self):
        """测试成功响应快捷函数"""
        data = {'user_id': 1}
        response = success_response(
            data=data,
            message="操作成功"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data'], data)
        self.assertEqual(response.data['message'], "操作成功")
    
    def test_error_response_function(self):
        """测试错误响应快捷函数"""
        response = error_response(
            message="操作失败",
            code=ResponseCode.BAD_REQUEST
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['code'], ResponseCode.BAD_REQUEST)
        self.assertEqual(response.data['message'], "操作失败")
    
    def test_paginated_response_function(self):
        """测试分页响应快捷函数"""
        # 创建测试数据
        for i in range(15):
            User.objects.create_user(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                password='testpass123'
            )
        
        users = User.objects.all().order_by('username')
        response = paginated_response(
            queryset=users,
            page=1,
            page_size=10
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(len(response.data['data']), 10)
        self.assertIn('pagination', response.data)
