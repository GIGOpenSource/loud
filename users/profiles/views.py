"""
用户资料视图
使用base基础类重构
"""

from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from base.views import BaseModelViewSet, BaseRetrieveUpdateAPIView
from base.pagination import BasePagination
from base.permissions import IsOwnerOrReadOnly
from utils.response import BaseApiResponse
from utils.decorators import log_api_call, handle_exceptions

from .models import UserProfile
from .serializers import (
    UserProfileSerializer, UserProfileListSerializer,
    UserProfileCreateSerializer, UserProfileUpdateSerializer,
    UserAvatarUploadSerializer, UserPublicProfileSerializer,
    UserProfileStatsSerializer
)
from .permissions import UserProfilePermission
from .filters import UserProfileFilterSet


class UserProfileViewSet(BaseModelViewSet):
    """
    用户资料视图集
    提供完整的CRUD操作
    """
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    list_serializer_class = UserProfileListSerializer
    create_serializer_class = UserProfileCreateSerializer
    update_serializer_class = UserProfileUpdateSerializer
    
    permission_classes = [permissions.IsAuthenticated, UserProfilePermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = BasePagination
    filterset_class = UserProfileFilterSet
    
    search_fields = ['nickname', 'bio', 'city', 'country']
    ordering_fields = ['created_at', 'updated_at', 'nickname']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 普通用户只能看到自己的资料
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset
    
    def perform_create_pre(self, serializer):
        """创建前设置用户"""
        serializer.validated_data['user'] = self.request.user
    
    def perform_create_post(self, instance, serializer):
        """创建后的业务逻辑"""
        # 清除用户相关缓存
        self.clear_user_cache(instance.user)
        
        # 记录日志
        self.log_profile_action('created', instance)
    
    def perform_update_post(self, instance, serializer):
        """更新后的业务逻辑"""
        # 清除用户相关缓存
        self.clear_user_cache(instance.user)
        
        # 如果头像发生变化，记录特殊日志
        if 'avatar' in serializer.validated_data:
            self.log_profile_action('avatar_updated', instance)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    @log_api_call
    @handle_exceptions
    def upload_avatar(self, request, pk=None):
        """上传头像"""
        profile = self.get_object()
        serializer = UserAvatarUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            # 更新头像
            profile.update_avatar(serializer.validated_data['avatar'])
            
            # 返回更新后的资料
            response_serializer = self.get_serializer(profile)
            return BaseApiResponse.success(
                data=response_serializer.data,
                message='头像上传成功'
            )
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='头像上传失败'
        )
    
    @action(detail=True, methods=['delete'])
    @log_api_call
    @handle_exceptions
    def delete_avatar(self, request, pk=None):
        """删除头像"""
        profile = self.get_object()
        profile.delete_avatar()
        
        response_serializer = self.get_serializer(profile)
        return BaseApiResponse.success(
            data=response_serializer.data,
            message='头像删除成功'
        )
    
    @action(detail=True, methods=['get'])
    @method_decorator(cache_page(60 * 10))  # 缓存10分钟
    def public_profile(self, request, pk=None):
        """获取公开资料"""
        profile = self.get_object()
        serializer = UserPublicProfileSerializer(profile)
        
        return BaseApiResponse.success(
            data=serializer.data,
            message='获取公开资料成功'
        )
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """获取资料统计信息"""
        profile = self.get_object()
        serializer = UserProfileStatsSerializer(profile)
        
        return BaseApiResponse.success(
            data=serializer.data,
            message='获取统计信息成功'
        )
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """获取当前用户的资料"""
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'nickname': request.user.username}
        )
        
        serializer = self.get_serializer(profile)
        message = '获取个人资料成功'
        if created:
            message = '首次创建个人资料成功'
        
        return BaseApiResponse.success(
            data=serializer.data,
            message=message
        )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_my_profile(self, request):
        """更新当前用户的资料"""
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'nickname': request.user.username}
        )
        
        partial = request.method == 'PATCH'
        serializer = UserProfileUpdateSerializer(
            profile, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # 清除缓存
            self.clear_user_cache(request.user)
            
            response_serializer = self.get_serializer(profile)
            return BaseApiResponse.success(
                data=response_serializer.data,
                message='资料更新成功'
            )
        
        return BaseApiResponse.validation_error(
            errors=serializer.errors,
            message='资料更新失败'
        )
    
    def clear_user_cache(self, user):
        """清除用户相关缓存"""
        from django.core.cache import cache
        cache_keys = [
            f'user_profile_{user.id}',
            f'user_dashboard_{user.id}',
            f'user_public_profile_{user.id}',
        ]
        for key in cache_keys:
            cache.delete(key)
    
    def log_profile_action(self, action, profile):
        """记录资料操作日志"""
        import logging
        logger = logging.getLogger('business')
        logger.info(f'Profile {action}: user_id={profile.user.id}, profile_id={profile.id}')


class UserPublicProfileView(BaseRetrieveUpdateAPIView):
    """
    用户公开资料视图
    任何人都可以查看公开资料
    """
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserPublicProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'user_id'
    
    @method_decorator(cache_page(60 * 15))  # 缓存15分钟
    def get(self, request, *args, **kwargs):
        """获取公开资料"""
        return super().get(request, *args, **kwargs)
    
    def get_object(self):
        """获取对象，只返回公开或半公开的资料"""
        user_id = self.kwargs.get('user_id')
        profile = get_object_or_404(
            UserProfile.objects.select_related('user'),
            user_id=user_id
        )
        
        # 检查资料可见性
        if profile.profile_visibility == 'private':
            # 只有本人可以查看私密资料
            if not self.request.user.is_authenticated or self.request.user != profile.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('该用户的资料为私密状态')
        
        return profile
