"""
用户模块信号处理
整合所有子模块的信号
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache

from .profiles.models import UserProfile
from .preferences.models import UserPreference
from .wallets.models import UserWallet

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_related_objects(sender, instance, created, **kwargs):
    """
    用户创建时自动创建相关对象
    """
    if created:
        # 创建用户资料
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'nickname': instance.username}
        )
        
        # 创建用户偏好
        UserPreference.objects.get_or_create(
            user=instance,
            defaults={}
        )
        
        # 创建用户钱包
        UserWallet.objects.get_or_create(
            user=instance,
            defaults={'currency': 'CNY'}
        )


@receiver(post_save, sender=UserProfile)
def clear_profile_cache(sender, instance, **kwargs):
    """清除用户资料相关缓存"""
    cache_keys = [
        f'user_profile_{instance.user.id}',
        f'user_dashboard_{instance.user.id}',
        f'user_public_profile_{instance.user.id}',
    ]
    for key in cache_keys:
        cache.delete(key)


@receiver(post_save, sender=UserPreference)
def clear_preference_cache(sender, instance, **kwargs):
    """清除用户偏好相关缓存"""
    cache_keys = [
        f'user_preferences_{instance.user.id}',
        f'user_dashboard_{instance.user.id}',
        f'user_settings_{instance.user.id}',
    ]
    for key in cache_keys:
        cache.delete(key)


@receiver(post_save, sender=UserWallet)
def clear_wallet_cache(sender, instance, **kwargs):
    """清除用户钱包相关缓存"""
    cache_keys = [
        f'user_wallet_{instance.user.id}',
        f'user_dashboard_{instance.user.id}',
        f'wallet_stats_{instance.user.id}',
    ]
    for key in cache_keys:
        cache.delete(key)


@receiver(post_delete, sender=UserProfile)
def handle_profile_deletion(sender, instance, **kwargs):
    """处理用户资料删除"""
    # 清除相关缓存
    clear_profile_cache(sender, instance)


@receiver(post_delete, sender=User)
def handle_user_deletion(sender, instance, **kwargs):
    """处理用户删除"""
    # 清除所有相关缓存
    cache_keys = [
        f'user_profile_{instance.id}',
        f'user_preferences_{instance.id}',
        f'user_wallet_{instance.id}',
        f'user_dashboard_{instance.id}',
        f'user_public_profile_{instance.id}',
        f'user_settings_{instance.id}',
        f'wallet_stats_{instance.id}',
    ]
    for key in cache_keys:
        cache.delete(key)