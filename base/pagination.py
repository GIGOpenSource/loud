"""
基础分页器
提供标准化的分页功能
"""

from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from collections import OrderedDict
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from utils.response import BaseApiResponse


class BasePagination(PageNumberPagination):
    """
    基础分页器
    提供标准化的分页功能
    """
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        """返回标准化的分页响应"""
        return BaseApiResponse.success(
            data={
                'results': data,
                'pagination': {
                    'current_page': self.page.number,
                    'page_size': self.page.paginator.per_page,
                    'total_pages': self.page.paginator.num_pages,
                    'total_count': self.page.paginator.count,
                    'has_next': self.page.has_next(),
                    'has_previous': self.page.has_previous(),
                    'next_page': self.page.next_page_number() if self.page.has_next() else None,
                    'previous_page': self.page.previous_page_number() if self.page.has_previous() else None,
                }
            },
            message="获取数据成功"
        )
    
    def get_paginated_response_schema(self, schema):
        """返回分页响应的Schema"""
        return {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'code': {'type': 'integer'},
                'message': {'type': 'string'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'results': {
                            'type': 'array',
                            'items': schema,
                        },
                        'pagination': {
                            'type': 'object',
                            'properties': {
                                'current_page': {'type': 'integer'},
                                'page_size': {'type': 'integer'},
                                'total_pages': {'type': 'integer'},
                                'total_count': {'type': 'integer'},
                                'has_next': {'type': 'boolean'},
                                'has_previous': {'type': 'boolean'},
                                'next_page': {'type': 'integer', 'nullable': True},
                                'previous_page': {'type': 'integer', 'nullable': True},
                            }
                        }
                    }
                }
            }
        }


class SmallResultsPagination(BasePagination):
    """
    小结果集分页器
    用于数据量较小的列表
    """
    page_size = 10
    max_page_size = 50


class LargeResultsPagination(BasePagination):
    """
    大结果集分页器
    用于数据量较大的列表
    """
    page_size = 50
    max_page_size = 200


class CustomLimitOffsetPagination(LimitOffsetPagination):
    """
    自定义偏移分页器
    适用于需要精确控制偏移量的场景
    """
    
    default_limit = 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
    
    def get_paginated_response(self, data):
        """返回标准化的偏移分页响应"""
        return BaseApiResponse.success(
            data={
                'results': data,
                'pagination': {
                    'limit': self.limit,
                    'offset': self.offset,
                    'count': self.count,
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                }
            },
            message="获取数据成功"
        )


class NoPagination:
    """
    无分页器
    返回所有结果，慎用
    """
    
    def paginate_queryset(self, queryset, request, view=None):
        """不分页，直接返回查询集"""
        return None
    
    def get_paginated_response(self, data):
        """返回无分页的响应"""
        return BaseApiResponse.success(
            data=data,
            message="获取数据成功"
        )


class CursorPagination(PageNumberPagination):
    """
    游标分页器
    适用于实时数据流或大数据集
    """
    
    page_size = 20
    ordering = '-created_at'  # 必须指定排序字段
    cursor_query_param = 'cursor'
    
    def paginate_queryset(self, queryset, request, view=None):
        """使用游标进行分页"""
        self.count = None  # 游标分页不计算总数
        return super().paginate_queryset(queryset, request, view)
    
    def get_paginated_response(self, data):
        """返回游标分页响应"""
        return BaseApiResponse.success(
            data={
                'results': data,
                'pagination': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                    'count': None,  # 游标分页不返回总数
                }
            },
            message="获取数据成功"
        )


class DynamicPagination(BasePagination):
    """
    动态分页器
    根据请求参数动态调整分页大小
    """
    
    def __init__(self):
        super().__init__()
        # 动态分页配置
        self.pagination_configs = {
            'small': {'page_size': 10, 'max_page_size': 30},
            'medium': {'page_size': 20, 'max_page_size': 60},
            'large': {'page_size': 50, 'max_page_size': 150},
        }
    
    def paginate_queryset(self, queryset, request, view=None):
        """动态设置分页参数"""
        # 从请求中获取分页类型
        pagination_type = request.query_params.get('pagination_type', 'medium')
        
        if pagination_type in self.pagination_configs:
            config = self.pagination_configs[pagination_type]
            self.page_size = config['page_size']
            self.max_page_size = config['max_page_size']
        
        return super().paginate_queryset(queryset, request, view)


class MetaPagination(BasePagination):
    """
    元数据分页器
    包含额外的元数据信息
    """
    
    def get_paginated_response(self, data):
        """返回包含元数据的分页响应"""
        return BaseApiResponse.success(
            data={
                'results': data,
                'pagination': {
                    'current_page': self.page.number,
                    'page_size': self.page.paginator.per_page,
                    'total_pages': self.page.paginator.num_pages,
                    'total_count': self.page.paginator.count,
                    'has_next': self.page.has_next(),
                    'has_previous': self.page.has_previous(),
                    'next_page': self.page.next_page_number() if self.page.has_next() else None,
                    'previous_page': self.page.previous_page_number() if self.page.has_previous() else None,
                },
                'meta': {
                    'query_time': getattr(self, 'query_time', None),
                    'cache_hit': getattr(self, 'cache_hit', None),
                    'filters_applied': getattr(self, 'filters_applied', []),
                    'ordering': getattr(self, 'ordering', None),
                }
            },
            message="获取数据成功"
        )
