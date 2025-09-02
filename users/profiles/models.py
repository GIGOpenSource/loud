"""
用户资料模型
使用base基础类重构
"""

import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date

from base.models import BaseAuditModel
from base.validators import chinese_name_validator, image_validator, image_size_validator


def user_avatar_path(instance, filename):
    """生成用户头像上传路径"""
    from base.utils import FileUtils
    return f'avatars/{FileUtils.generate_filename(filename, f"user_{instance.user.id}")}'


class UserProfile(BaseAuditModel):
    """
    用户详细信息模型
    继承BaseAuditModel获得审计功能
    """
    user = models.OneToOneField(
        'authentication.User', 
        on_delete=models.CASCADE, 
        related_name='profile', 
        verbose_name=_('用户')
    )
    
    # 个人信息
    nickname = models.CharField(
        _('昵称'), 
        max_length=50, 
        blank=True, 
        validators=[chinese_name_validator],
        help_text=_('用户昵称，支持中文')
    )
    bio = models.TextField(
        _('个人简介'), 
        max_length=500, 
        blank=True, 
        help_text=_('个人简介，最多500字')
    )
    avatar = models.ImageField(
        _('头像'), 
        upload_to=user_avatar_path, 
        blank=True, 
        null=True,
        validators=[image_validator, image_size_validator],
        help_text=_('用户头像，支持jpg、png、gif格式，最大5MB')
    )
    birth_date = models.DateField(
        _('出生日期'), 
        null=True, 
        blank=True, 
        help_text=_('出生日期')
    )
    gender = models.CharField(
        _('性别'), 
        max_length=10, 
        choices=[
            ('male', _('男')),
            ('female', _('女')),
            ('other', _('其他')),
        ], 
        blank=True, 
        help_text=_('性别')
    )
    
    # 地址信息
    country = models.CharField(_('国家'), max_length=50, blank=True)
    province = models.CharField(_('省份'), max_length=50, blank=True)
    city = models.CharField(_('城市'), max_length=50, blank=True)
    address = models.TextField(_('详细地址'), blank=True)
    
    # 联系信息
    website = models.URLField(_('个人网站'), blank=True)
    twitter = models.CharField(
        _('Twitter'), 
        max_length=100, 
        blank=True,
        validators=[RegexValidator(
            regex=r'^https?://(?:www\.)?twitter\.com/[A-Za-z0-9_]+/?$',
            message='请输入正确的Twitter链接'
        )]
    )
    github = models.CharField(
        _('GitHub'), 
        max_length=100, 
        blank=True,
        validators=[RegexValidator(
            regex=r'^https?://(?:www\.)?github\.com/[A-Za-z0-9_-]+/?$',
            message='请输入正确的GitHub链接'
        )]
    )
    
    # 隐私设置
    profile_visibility = models.CharField(
        _('资料可见性'),
        max_length=20,
        choices=[
            ('public', _('公开')),
            ('friends', _('仅好友')),
            ('private', _('私密')),
        ],
        default='public',
        help_text=_('控制个人资料的可见性')
    )
    show_email = models.BooleanField(_('显示邮箱'), default=False)
    show_phone = models.BooleanField(_('显示手机'), default=False)
    
    class Meta:
        verbose_name = _('用户资料')
        verbose_name_plural = _('用户资料')
        db_table = 'user_profiles'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f'{self.user.username} 的资料'
    
    @property
    def display_name(self):
        """获取显示名称"""
        return self.nickname or self.user.username or self.user.email
    
    @property
    def avatar_url(self):
        """获取头像URL"""
        if self.avatar:
            return self.avatar.url
        return None
    
    @property
    def age(self):
        """计算年龄"""
        from base.utils import DateUtils
        return DateUtils.get_age(self.birth_date)
    
    @property
    def full_address(self):
        """获取完整地址"""
        from base.utils import BusinessUtils
        return BusinessUtils.format_address(
            self.country, self.province, self.city, self.address
        )
    
    def clean(self):
        """模型验证"""
        super().clean()
        
        # 验证出生日期不能是未来
        if self.birth_date and self.birth_date > date.today():
            raise ValidationError({'birth_date': '出生日期不能是未来日期'})
        
        # 验证网站URL格式
        if self.website and not self.website.startswith(('http://', 'https://')):
            raise ValidationError({'website': '网站链接必须以http://或https://开头'})
    
    def get_public_data(self):
        """获取公开资料数据"""
        data = {
            'id': self.id,
            'user_id': self.user.id,
            'display_name': self.display_name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'website': self.website,
        }
        
        # 根据隐私设置控制显示内容
        if self.profile_visibility == 'public':
            data.update({
                'gender': self.gender,
                'country': self.country,
                'city': self.city,
                'twitter': self.twitter,
                'github': self.github,
            })
            
            if self.show_email:
                data['email'] = self.user.email
            
            if self.birth_date:
                data['age'] = self.age
        
        return data
    
    def update_avatar(self, avatar_file):
        """更新头像"""
        # 删除旧头像
        if self.avatar:
            self.avatar.delete(save=False)
        
        # 保存新头像
        self.avatar = avatar_file
        self.save(update_fields=['avatar', 'updated_at'])
    
    def delete_avatar(self):
        """删除头像"""
        if self.avatar:
            self.avatar.delete(save=False)
            self.avatar = None
            self.save(update_fields=['avatar', 'updated_at'])
