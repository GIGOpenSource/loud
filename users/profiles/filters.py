"""
用户资料过滤器
使用base基础类重构
"""

import django_filters
from base.filters import BaseFilterSet, TimestampFilterSet
from .models import UserProfile


class UserProfileFilterSet(TimestampFilterSet):
    """用户资料过滤器"""
    
    # 基本过滤
    gender = django_filters.ChoiceFilter(
        choices=UserProfile._meta.get_field('gender').choices,
        help_text='性别过滤'
    )
    
    profile_visibility = django_filters.ChoiceFilter(
        choices=UserProfile._meta.get_field('profile_visibility').choices,
        help_text='资料可见性过滤'
    )
    
    # 地理位置过滤
    country = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='国家过滤'
    )
    
    province = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='省份过滤'
    )
    
    city = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='城市过滤'
    )
    
    # 年龄范围过滤
    age_min = django_filters.NumberFilter(
        method='filter_age_min',
        help_text='最小年龄'
    )
    
    age_max = django_filters.NumberFilter(
        method='filter_age_max',
        help_text='最大年龄'
    )
    
    # 是否有头像
    has_avatar = django_filters.BooleanFilter(
        method='filter_has_avatar',
        help_text='是否有头像'
    )
    
    # 是否有个人简介
    has_bio = django_filters.BooleanFilter(
        method='filter_has_bio',
        help_text='是否有个人简介'
    )
    
    # 是否填写了联系方式
    has_website = django_filters.BooleanFilter(
        method='filter_has_website',
        help_text='是否有个人网站'
    )
    
    has_social_links = django_filters.BooleanFilter(
        method='filter_has_social_links',
        help_text='是否有社交链接'
    )
    
    class Meta:
        model = UserProfile
        fields = ['gender', 'profile_visibility', 'country', 'province', 'city', 'is_active']
        search_fields = ['nickname', 'bio', 'city', 'country', 'user__username', 'user__email']
    
    def filter_age_min(self, queryset, name, value):
        """按最小年龄过滤"""
        if not value:
            return queryset
        
        from datetime import date, timedelta
        max_birth_date = date.today() - timedelta(days=value * 365)
        return queryset.filter(birth_date__lte=max_birth_date)
    
    def filter_age_max(self, queryset, name, value):
        """按最大年龄过滤"""
        if not value:
            return queryset
        
        from datetime import date, timedelta
        min_birth_date = date.today() - timedelta(days=(value + 1) * 365)
        return queryset.filter(birth_date__gte=min_birth_date)
    
    def filter_has_avatar(self, queryset, name, value):
        """按是否有头像过滤"""
        if value:
            return queryset.exclude(avatar__isnull=True).exclude(avatar='')
        else:
            return queryset.filter(avatar__isnull=True) | queryset.filter(avatar='')
    
    def filter_has_bio(self, queryset, name, value):
        """按是否有个人简介过滤"""
        if value:
            return queryset.exclude(bio__isnull=True).exclude(bio='')
        else:
            return queryset.filter(bio__isnull=True) | queryset.filter(bio='')
    
    def filter_has_website(self, queryset, name, value):
        """按是否有个人网站过滤"""
        if value:
            return queryset.exclude(website__isnull=True).exclude(website='')
        else:
            return queryset.filter(website__isnull=True) | queryset.filter(website='')
    
    def filter_has_social_links(self, queryset, name, value):
        """按是否有社交链接过滤"""
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(twitter__isnull=False) & ~Q(twitter='') |
                Q(github__isnull=False) & ~Q(github='')
            )
        else:
            return queryset.filter(
                Q(twitter__isnull=True) | Q(twitter='')
            ).filter(
                Q(github__isnull=True) | Q(github='')
            )


class PublicUserProfileFilterSet(django_filters.FilterSet):
    """公开用户资料过滤器"""
    
    # 只包含基本的公开信息过滤
    gender = django_filters.ChoiceFilter(
        choices=[
            ('male', '男'),
            ('female', '女'),
            ('other', '其他'),
        ]
    )
    
    country = django_filters.CharFilter(lookup_expr='icontains')
    city = django_filters.CharFilter(lookup_expr='icontains')
    
    has_avatar = django_filters.BooleanFilter(
        method='filter_has_avatar'
    )
    
    # 搜索
    search = django_filters.CharFilter(
        method='filter_search'
    )
    
    class Meta:
        model = UserProfile
        fields = ['gender', 'country', 'city']
    
    def filter_has_avatar(self, queryset, name, value):
        """按是否有头像过滤"""
        if value:
            return queryset.exclude(avatar__isnull=True).exclude(avatar='')
        else:
            return queryset.filter(avatar__isnull=True) | queryset.filter(avatar='')
    
    def filter_search(self, queryset, name, value):
        """搜索过滤"""
        if not value:
            return queryset
        
        from django.db.models import Q
        return queryset.filter(
            Q(nickname__icontains=value) |
            Q(bio__icontains=value) |
            Q(city__icontains=value) |
            Q(country__icontains=value)
        )
