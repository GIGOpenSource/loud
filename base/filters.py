"""
基础过滤器类
提供标准化的过滤功能
"""

import django_filters
from django.db import models
from django.utils import timezone
from datetime import datetime, date
from django_filters import rest_framework as filters


class BaseFilterSet(django_filters.FilterSet):
    """
    基础过滤器
    提供通用的过滤功能
    """
    
    # 时间范围过滤
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text='创建时间开始'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text='创建时间结束'
    )
    
    updated_after = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte',
        help_text='更新时间开始'
    )
    updated_before = django_filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte',
        help_text='更新时间结束'
    )
    
    # 状态过滤
    is_active = django_filters.BooleanFilter(help_text='是否激活')
    status = django_filters.CharFilter(help_text='状态')
    
    # 搜索过滤
    search = django_filters.CharFilter(
        method='filter_search',
        help_text='搜索关键词'
    )
    
    # 排序
    ordering = django_filters.OrderingFilter(
        fields=[
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
            ('id', 'id'),
        ],
        help_text='排序字段'
    )
    
    class Meta:
        abstract = True
    
    def filter_search(self, queryset, name, value):
        """搜索过滤方法，子类可重写"""
        if not value:
            return queryset
        
        # 获取搜索字段
        search_fields = getattr(self._meta, 'search_fields', [])
        if not search_fields:
            return queryset
        
        # 构建搜索查询
        from django.db.models import Q
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": value})
        
        return queryset.filter(query)


class TimestampFilterSet(BaseFilterSet):
    """
    时间戳过滤器
    专门用于时间戳相关的过滤
    """
    
    # 日期过滤
    created_date = django_filters.DateFilter(
        field_name='created_at__date',
        help_text='创建日期'
    )
    
    updated_date = django_filters.DateFilter(
        field_name='updated_at__date',
        help_text='更新日期'
    )
    
    # 年月过滤
    created_year = django_filters.NumberFilter(
        field_name='created_at__year',
        help_text='创建年份'
    )
    
    created_month = django_filters.NumberFilter(
        field_name='created_at__month',
        help_text='创建月份'
    )
    
    # 最近时间过滤
    recent = django_filters.ChoiceFilter(
        method='filter_recent',
        choices=[
            ('1h', '最近1小时'),
            ('1d', '最近1天'),
            ('1w', '最近1周'),
            ('1m', '最近1月'),
        ],
        help_text='最近时间'
    )
    
    def filter_recent(self, queryset, name, value):
        """最近时间过滤"""
        now = timezone.now()
        
        if value == '1h':
            start_time = now - timezone.timedelta(hours=1)
        elif value == '1d':
            start_time = now - timezone.timedelta(days=1)
        elif value == '1w':
            start_time = now - timezone.timedelta(weeks=1)
        elif value == '1m':
            start_time = now - timezone.timedelta(days=30)
        else:
            return queryset
        
        return queryset.filter(created_at__gte=start_time)


class SoftDeleteFilterSet(BaseFilterSet):
    """
    软删除过滤器
    """
    
    include_deleted = django_filters.BooleanFilter(
        method='filter_include_deleted',
        help_text='是否包含已删除数据'
    )
    
    only_deleted = django_filters.BooleanFilter(
        method='filter_only_deleted',
        help_text='只显示已删除数据'
    )
    
    deleted_after = django_filters.DateTimeFilter(
        field_name='deleted_at',
        lookup_expr='gte',
        help_text='删除时间开始'
    )
    
    deleted_before = django_filters.DateTimeFilter(
        field_name='deleted_at',
        lookup_expr='lte',
        help_text='删除时间结束'
    )
    
    def filter_include_deleted(self, queryset, name, value):
        """包含已删除数据"""
        if value:
            return queryset
        else:
            return queryset.filter(is_deleted=False)
    
    def filter_only_deleted(self, queryset, name, value):
        """只显示已删除数据"""
        if value:
            return queryset.filter(is_deleted=True)
        else:
            return queryset


class AuditFilterSet(BaseFilterSet):
    """
    审计过滤器
    """
    
    created_by = django_filters.NumberFilter(
        field_name='created_by__id',
        help_text='创建者ID'
    )
    
    created_by_username = django_filters.CharFilter(
        field_name='created_by__username',
        lookup_expr='icontains',
        help_text='创建者用户名'
    )
    
    updated_by = django_filters.NumberFilter(
        field_name='updated_by__id',
        help_text='更新者ID'
    )
    
    updated_by_username = django_filters.CharFilter(
        field_name='updated_by__username',
        lookup_expr='icontains',
        help_text='更新者用户名'
    )


class NumericRangeFilterSet(BaseFilterSet):
    """
    数值范围过滤器
    """
    
    @classmethod
    def add_numeric_range_filter(cls, field_name, help_text_prefix=""):
        """添加数值范围过滤器"""
        min_filter = django_filters.NumberFilter(
            field_name=field_name,
            lookup_expr='gte',
            help_text=f'{help_text_prefix}最小值'
        )
        max_filter = django_filters.NumberFilter(
            field_name=field_name,
            lookup_expr='lte',
            help_text=f'{help_text_prefix}最大值'
        )
        
        setattr(cls, f'{field_name}_min', min_filter)
        setattr(cls, f'{field_name}_max', max_filter)


class TreeFilterSet(BaseFilterSet):
    """
    树形结构过滤器
    """
    
    parent = django_filters.NumberFilter(
        field_name='parent__id',
        help_text='父级ID'
    )
    
    level = django_filters.NumberFilter(help_text='层级')
    
    root_only = django_filters.BooleanFilter(
        method='filter_root_only',
        help_text='只显示根节点'
    )
    
    children_of = django_filters.NumberFilter(
        method='filter_children_of',
        help_text='指定节点的子节点'
    )
    
    def filter_root_only(self, queryset, name, value):
        """只显示根节点"""
        if value:
            return queryset.filter(parent__isnull=True)
        return queryset
    
    def filter_children_of(self, queryset, name, value):
        """指定节点的子节点"""
        if value:
            try:
                parent = queryset.model.objects.get(id=value)
                return queryset.filter(path__startswith=f"{parent.path}/")
            except queryset.model.DoesNotExist:
                return queryset.none()
        return queryset


class TagFilterSet(BaseFilterSet):
    """
    标签过滤器
    """
    
    tags = django_filters.CharFilter(
        method='filter_tags',
        help_text='标签，多个标签用逗号分隔'
    )
    
    has_tag = django_filters.CharFilter(
        method='filter_has_tag',
        help_text='包含指定标签'
    )
    
    def filter_tags(self, queryset, name, value):
        """标签过滤"""
        if not value:
            return queryset
        
        tags = [tag.strip() for tag in value.split(',')]
        for tag in tags:
            queryset = queryset.filter(tags__contains=tag)
        
        return queryset
    
    def filter_has_tag(self, queryset, name, value):
        """包含指定标签"""
        if not value:
            return queryset
        
        return queryset.filter(tags__contains=value)


class MetaFilterSet(BaseFilterSet):
    """
    元数据过滤器
    """
    
    meta_key = django_filters.CharFilter(
        method='filter_meta_key',
        help_text='元数据键'
    )
    
    meta_value = django_filters.CharFilter(
        method='filter_meta_value',
        help_text='元数据值'
    )
    
    def filter_meta_key(self, queryset, name, value):
        """按元数据键过滤"""
        if not value:
            return queryset
        
        return queryset.filter(meta_data__has_key=value)
    
    def filter_meta_value(self, queryset, name, value):
        """按元数据值过滤"""
        if not value:
            return queryset
        
        # 这里需要根据具体的元数据结构来实现
        # 示例：查找任何值包含指定文本的记录
        from django.contrib.postgres.fields import JSONField
        return queryset.extra(
            where=["meta_data::text LIKE %s"],
            params=[f'%{value}%']
        )
