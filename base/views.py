"""
基础视图类
提供标准化的API视图基类，统一处理CRUD操作、分页、过滤等
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db import transaction

from utils.decorators import api_response, handle_exceptions, log_api_call, validate_request_data
from utils.response import BaseApiResponse
from .filters import BaseFilterSet
from .permissions import BasePermission
from .serializers import BaseModelSerializer


class BaseAPIView:
    """
    基础API视图类
    提供通用的功能和配置
    """
    
    # 默认权限类
    permission_classes = [permissions.IsAuthenticated]
    
    # 缓存配置
    cache_timeout = 60 * 5  # 5分钟
    
    # 日志配置
    enable_logging = True
    
    def get_permissions(self):
        """获取权限类"""
        permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]
    
    def get_cache_key(self, prefix="view"):
        """生成缓存键"""
        user_id = getattr(self.request.user, 'id', 'anonymous')
        view_name = self.__class__.__name__
        return f"{prefix}_{view_name}_{user_id}_{self.request.method}"
    
    def clear_cache(self, prefix="view"):
        """清除相关缓存"""
        cache_key = self.get_cache_key(prefix)
        cache.delete(cache_key)


class BaseListAPIView(BaseAPIView, generics.ListAPIView):
    """
    基础列表视图
    提供标准化的列表查询功能
    """
    
    # 分页配置
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    # 过滤配置
    filterset_class = BaseFilterSet
    search_fields = []
    ordering_fields = []
    ordering = ['-created_at']
    
    @method_decorator(cache_page(60 * 5))
    @log_api_call
    @handle_exceptions
    @api_response(success_message="获取列表成功")
    def get(self, request, *args, **kwargs):
        """获取列表数据"""
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 应用搜索
        search = self.request.query_params.get('search')
        if search and self.search_fields:
            search_query = Q()
            for field in self.search_fields:
                search_query |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(search_query)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """重写list方法，返回标准化响应"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return BaseApiResponse.success(
            data=serializer.data,
            message="获取列表成功"
        )


class BaseCreateAPIView(BaseAPIView, generics.CreateAPIView):
    """
    基础创建视图
    提供标准化的创建功能
    """
    
    @log_api_call
    @handle_exceptions
    @validate_request_data()
    @api_response(success_message="创建成功")
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """创建数据"""
        return super().post(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """重写create方法，返回标准化响应"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 执行创建前的钩子
        self.perform_create_pre(serializer)
        
        # 执行创建
        instance = serializer.save()
        
        # 执行创建后的钩子
        self.perform_create_post(instance, serializer)
        
        # 清除相关缓存
        self.clear_cache()
        
        return BaseApiResponse.created(
            data=self.get_serializer(instance).data,
            message="创建成功"
        )
    
    def perform_create_pre(self, serializer):
        """创建前钩子，子类可重写"""
        pass
    
    def perform_create_post(self, instance, serializer):
        """创建后钩子，子类可重写"""
        pass


class BaseRetrieveAPIView(BaseAPIView, generics.RetrieveAPIView):
    """
    基础详情视图
    提供标准化的详情查询功能
    """
    
    @method_decorator(cache_page(60 * 10))
    @log_api_call
    @handle_exceptions
    @api_response(success_message="获取详情成功")
    def get(self, request, *args, **kwargs):
        """获取详情数据"""
        return super().get(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        """重写retrieve方法，返回标准化响应"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return BaseApiResponse.success(
            data=serializer.data,
            message="获取详情成功"
        )


class BaseUpdateAPIView(BaseAPIView, generics.UpdateAPIView):
    """
    基础更新视图
    提供标准化的更新功能
    """
    
    @log_api_call
    @handle_exceptions
    @validate_request_data()
    @api_response(success_message="更新成功")
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        """完整更新"""
        return super().put(request, *args, **kwargs)
    
    @log_api_call
    @handle_exceptions
    @validate_request_data()
    @api_response(success_message="更新成功")
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        """部分更新"""
        return super().patch(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """重写update方法，返回标准化响应"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 执行更新前的钩子
        self.perform_update_pre(instance, request.data, partial)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # 执行更新
        instance = serializer.save()
        
        # 执行更新后的钩子
        self.perform_update_post(instance, serializer)
        
        # 清除相关缓存
        self.clear_cache()
        
        return BaseApiResponse.success(
            data=self.get_serializer(instance).data,
            message="更新成功"
        )
    
    def perform_update_pre(self, instance, validated_data, partial):
        """更新前钩子，子类可重写"""
        pass
    
    def perform_update_post(self, instance, serializer):
        """更新后钩子，子类可重写"""
        pass


class BaseDestroyAPIView(BaseAPIView, generics.DestroyAPIView):
    """
    基础删除视图
    提供标准化的删除功能
    """
    
    @log_api_call
    @handle_exceptions
    @api_response(success_message="删除成功")
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        """删除数据"""
        return super().delete(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """重写destroy方法，返回标准化响应"""
        instance = self.get_object()
        
        # 执行删除前的钩子
        self.perform_destroy_pre(instance)
        
        # 执行删除
        self.perform_destroy(instance)
        
        # 执行删除后的钩子
        self.perform_destroy_post(instance)
        
        # 清除相关缓存
        self.clear_cache()
        
        return BaseApiResponse.success(
            data=None,
            message="删除成功"
        )
    
    def perform_destroy_pre(self, instance):
        """删除前钩子，子类可重写"""
        pass
    
    def perform_destroy_post(self, instance):
        """删除后钩子，子类可重写"""
        pass


class BaseModelViewSet(BaseAPIView, ModelViewSet):
    """
    基础模型视图集
    提供完整的CRUD操作
    """
    
    # 序列化器配置
    serializer_class = BaseModelSerializer
    
    # 权限配置
    permission_classes = [BasePermission]
    
    # 过滤配置
    filterset_class = BaseFilterSet
    search_fields = []
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据action获取不同的序列化器"""
        if self.action == 'create':
            return getattr(self, 'create_serializer_class', self.serializer_class)
        elif self.action in ['update', 'partial_update']:
            return getattr(self, 'update_serializer_class', self.serializer_class)
        elif self.action == 'list':
            return getattr(self, 'list_serializer_class', self.serializer_class)
        return self.serializer_class
    
    def get_permissions(self):
        """根据action获取不同的权限"""
        if self.action == 'list':
            permission_classes = getattr(self, 'list_permission_classes', self.permission_classes)
        elif self.action == 'create':
            permission_classes = getattr(self, 'create_permission_classes', self.permission_classes)
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = getattr(self, 'update_permission_classes', self.permission_classes)
        elif self.action == 'destroy':
            permission_classes = getattr(self, 'destroy_permission_classes', self.permission_classes)
        else:
            permission_classes = self.permission_classes
        
        return [permission() for permission in permission_classes]
    
    @log_api_call
    @handle_exceptions
    def list(self, request, *args, **kwargs):
        """列表视图"""
        return super().list(request, *args, **kwargs)
    
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """创建视图"""
        return super().create(request, *args, **kwargs)
    
    @log_api_call
    @handle_exceptions
    def retrieve(self, request, *args, **kwargs):
        """详情视图"""
        return super().retrieve(request, *args, **kwargs)
    
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """更新视图"""
        return super().update(request, *args, **kwargs)
    
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """删除视图"""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def batch_create(self, request):
        """批量创建"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        instances = serializer.save()
        
        return BaseApiResponse.success(
            data=self.get_serializer(instances, many=True).data,
            message=f"批量创建成功，共创建{len(instances)}条记录"
        )
    
    @action(detail=False, methods=['patch'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def batch_update(self, request):
        """批量更新"""
        ids = request.data.get('ids', [])
        update_data = request.data.get('data', {})
        
        if not ids:
            return BaseApiResponse.error(message="请提供要更新的ID列表")
        
        queryset = self.get_queryset().filter(id__in=ids)
        updated_count = queryset.update(**update_data)
        
        return BaseApiResponse.success(
            data={'updated_count': updated_count},
            message=f"批量更新成功，共更新{updated_count}条记录"
        )
    
    @action(detail=False, methods=['delete'])
    @log_api_call
    @handle_exceptions
    @transaction.atomic
    def batch_destroy(self, request):
        """批量删除"""
        ids = request.data.get('ids', [])
        
        if not ids:
            return BaseApiResponse.error(message="请提供要删除的ID列表")
        
        queryset = self.get_queryset().filter(id__in=ids)
        deleted_count, _ = queryset.delete()
        
        return BaseApiResponse.success(
            data={'deleted_count': deleted_count},
            message=f"批量删除成功，共删除{deleted_count}条记录"
        )


class BaseListCreateAPIView(BaseListAPIView, BaseCreateAPIView):
    """
    基础列表创建视图
    组合列表和创建功能
    """
    pass


class BaseRetrieveUpdateAPIView(BaseRetrieveAPIView, BaseUpdateAPIView):
    """
    基础详情更新视图
    组合详情和更新功能
    """
    pass


class BaseRetrieveUpdateDestroyAPIView(BaseRetrieveAPIView, BaseUpdateAPIView, BaseDestroyAPIView):
    """
    基础详情更新删除视图
    组合详情、更新和删除功能
    """
    pass
