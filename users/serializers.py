"""
用户模块统一序列化器
导入和重新导出子模块的序列化器
"""

# 用户资料序列化器
from .profiles.serializers import (
    UserProfileSerializer,
    UserProfileListSerializer,
    UserProfileCreateSerializer,
    UserProfileUpdateSerializer,
    UserAvatarUploadSerializer,
    UserPublicProfileSerializer,
    UserProfileStatsSerializer,
)

# 用户偏好序列化器
from .preferences.serializers import (
    UserPreferenceSerializer,
    UserPreferenceCreateSerializer,
    UserPreferenceUpdateSerializer,
    UserPreferenceSummarySerializer,
    NotificationTypeSerializer,
    CustomSettingSerializer,
    PreferenceExportSerializer,
    PreferenceImportSerializer,
)

# 用户钱包序列化器
from .wallets.serializers import (
    UserWalletSerializer,
    UserWalletListSerializer,
    UserWalletCreateSerializer,
    UserWalletUpdateSerializer,
    WalletTransactionSerializer,
    WalletTransactionListSerializer,
    DepositSerializer,
    WithdrawSerializer,
    TransferSerializer,
    FreezeSerializer,
    PaymentPasswordSerializer,
    WalletStatsSerializer,
)

# 用于向后兼容的别名
UserDashboardSerializer = UserProfileSerializer

__all__ = [
    # 用户资料
    'UserProfileSerializer',
    'UserProfileListSerializer', 
    'UserProfileCreateSerializer',
    'UserProfileUpdateSerializer',
    'UserAvatarUploadSerializer',
    'UserPublicProfileSerializer',
    'UserProfileStatsSerializer',
    
    # 用户偏好
    'UserPreferenceSerializer',
    'UserPreferenceCreateSerializer',
    'UserPreferenceUpdateSerializer',
    'UserPreferenceSummarySerializer',
    'NotificationTypeSerializer',
    'CustomSettingSerializer',
    'PreferenceExportSerializer',
    'PreferenceImportSerializer',
    
    # 用户钱包
    'UserWalletSerializer',
    'UserWalletListSerializer',
    'UserWalletCreateSerializer',
    'UserWalletUpdateSerializer',
    'WalletTransactionSerializer',
    'WalletTransactionListSerializer',
    'DepositSerializer',
    'WithdrawSerializer',
    'TransferSerializer',
    'FreezeSerializer',
    'PaymentPasswordSerializer',
    'WalletStatsSerializer',
    
    # 兼容性
    'UserDashboardSerializer',
]