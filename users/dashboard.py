"""
用户仪表板
整合所有用户相关的信息
"""

from rest_framework import permissions
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from base.permissions import BasePermission
from utils.response import BaseApiResponse
from utils.decorators import log_api_call, handle_exceptions

from .profiles.models import UserProfile
from .preferences.models import UserPreference
from .wallets.models import UserWallet
from .profiles.serializers import UserProfileSerializer
from .preferences.serializers import UserPreferenceSummarySerializer
from .wallets.serializers import UserWalletSerializer


class UserDashboardView(APIView):
    """
    用户仪表板视图
    整合用户的所有信息
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @method_decorator(cache_page(60 * 5))  # 缓存5分钟
    @log_api_call
    @handle_exceptions
    def get(self, request):
        """获取用户仪表板数据"""
        user = request.user
        
        # 获取或创建用户相关数据
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={'nickname': user.username}
        )
        
        preference, _ = UserPreference.objects.get_or_create(
            user=user,
            defaults={}
        )
        
        wallet, _ = UserWallet.objects.get_or_create(
            user=user,
            defaults={'currency': 'CNY'}
        )
        
        # 序列化数据
        profile_serializer = UserProfileSerializer(profile)
        preference_serializer = UserPreferenceSummarySerializer(preference)
        wallet_serializer = UserWalletSerializer(wallet)
        
        # 计算统计信息
        stats = self.get_user_stats(user, wallet)
        
        # 获取最近活动
        recent_activities = self.get_recent_activities(user, wallet)
        
        dashboard_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': getattr(user, 'phone', None),
                'is_staff': user.is_staff,
                'is_verified': getattr(user, 'is_verified', False),
                'last_login': user.last_login,
                'date_joined': user.date_joined,
            },
            'profile': profile_serializer.data,
            'preferences': preference_serializer.data,
            'wallet': wallet_serializer.data,
            'stats': stats,
            'recent_activities': recent_activities,
        }
        
        return BaseApiResponse.success(
            data=dashboard_data,
            message="获取仪表板数据成功"
        )
    
    def get_user_stats(self, user, wallet):
        """获取用户统计信息"""
        from django.utils import timezone
        from datetime import timedelta
        
        # 计算账户使用时间
        account_age = (timezone.now().date() - user.date_joined.date()).days
        
        # 钱包统计
        wallet_stats = {
            'balance': wallet.balance,
            'total_income': wallet.total_income,
            'total_expense': wallet.total_expense,
            'transaction_count': wallet.transactions.count(),
            'last_transaction': wallet.last_transaction_at,
        }
        
        # 最近7天交易统计
        week_ago = timezone.now() - timedelta(days=7)
        recent_transactions = wallet.transactions.filter(created_at__gte=week_ago)
        
        weekly_stats = {
            'transaction_count': recent_transactions.count(),
            'income': sum(t.amount for t in recent_transactions if t.is_income),
            'expense': sum(t.amount for t in recent_transactions if t.is_expense),
        }
        
        return {
            'account_age_days': account_age,
            'wallet': wallet_stats,
            'weekly': weekly_stats,
        }
    
    def get_recent_activities(self, user, wallet):
        """获取最近活动"""
        activities = []
        
        # 最近5笔交易
        recent_transactions = wallet.transactions.order_by('-created_at')[:5]
        for tx in recent_transactions:
            activities.append({
                'type': 'transaction',
                'action': tx.get_transaction_type_display(),
                'description': tx.description,
                'amount': tx.amount,
                'timestamp': tx.created_at,
                'is_income': tx.is_income,
            })
        
        # 按时间排序
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return activities[:10]  # 返回最近10条活动


class UserOverviewView(APIView):
    """
    用户概览视图
    提供用户的基本信息概览
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @log_api_call
    @handle_exceptions
    def get(self, request):
        """获取用户概览数据"""
        user = request.user
        
        # 基本信息
        overview = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'status': 'active' if user.is_active else 'inactive',
            'member_since': user.date_joined,
            'last_seen': user.last_login,
        }
        
        # 模块状态
        modules_status = {}
        
        # 检查用户资料
        try:
            profile = UserProfile.objects.get(user=user)
            modules_status['profile'] = {
                'exists': True,
                'completeness': self.calculate_profile_completeness(profile),
                'last_updated': profile.updated_at,
            }
        except UserProfile.DoesNotExist:
            modules_status['profile'] = {'exists': False}
        
        # 检查用户偏好
        try:
            preference = UserPreference.objects.get(user=user)
            modules_status['preferences'] = {
                'exists': True,
                'theme': preference.theme,
                'language': preference.language,
                'last_updated': preference.updated_at,
            }
        except UserPreference.DoesNotExist:
            modules_status['preferences'] = {'exists': False}
        
        # 检查钱包
        try:
            wallet = UserWallet.objects.get(user=user)
            modules_status['wallet'] = {
                'exists': True,
                'currency': wallet.currency,
                'balance': wallet.balance,
                'status': wallet.wallet_status,
                'last_updated': wallet.updated_at,
            }
        except UserWallet.DoesNotExist:
            modules_status['wallet'] = {'exists': False}
        
        overview['modules'] = modules_status
        
        return BaseApiResponse.success(
            data=overview,
            message="获取用户概览成功"
        )
    
    def calculate_profile_completeness(self, profile):
        """计算资料完整度"""
        total_fields = 8
        filled_fields = 0
        
        if profile.nickname:
            filled_fields += 1
        if profile.bio:
            filled_fields += 1
        if profile.avatar:
            filled_fields += 1
        if profile.birth_date:
            filled_fields += 1
        if profile.gender:
            filled_fields += 1
        if profile.country:
            filled_fields += 1
        if profile.city:
            filled_fields += 1
        if profile.website:
            filled_fields += 1
        
        return round((filled_fields / total_fields) * 100, 1)
