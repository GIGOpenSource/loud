"""
基础模型类
提供标准化的模型基类，包含时间戳、软删除、审计等功能
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid

User = get_user_model()


class TimestampMixin(models.Model):
    """
    时间戳混入类
    自动添加创建时间和更新时间
    """
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True, db_index=True)
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    软删除混入类
    标记删除而不是物理删除
    """
    is_deleted = models.BooleanField(_('是否删除'), default=False, db_index=True)
    deleted_at = models.DateTimeField(_('删除时间'), null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted_set',
        verbose_name=_('删除者')
    )
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def hard_delete(self, using=None, keep_parents=False):
        """硬删除"""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """恢复删除"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class AuditMixin(models.Model):
    """
    审计混入类
    记录创建者和更新者
    """
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created_set',
        verbose_name=_('创建者')
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated_set',
        verbose_name=_('更新者')
    )
    
    class Meta:
        abstract = True


class StatusMixin(models.Model):
    """
    状态混入类
    通用的状态管理
    """
    STATUS_CHOICES = [
        ('active', _('激活')),
        ('inactive', _('未激活')),
        ('pending', _('待处理')),
        ('approved', _('已批准')),
        ('rejected', _('已拒绝')),
        ('suspended', _('已暂停')),
    ]
    
    is_active = models.BooleanField(_('是否激活'), default=True, db_index=True)
    status = models.CharField(
        _('状态'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    
    class Meta:
        abstract = True
    
    def activate(self):
        """激活"""
        self.is_active = True
        self.status = 'active'
        self.save(update_fields=['is_active', 'status'])
    
    def deactivate(self):
        """停用"""
        self.is_active = False
        self.status = 'inactive'
        self.save(update_fields=['is_active', 'status'])


class UUIDMixin(models.Model):
    """
    UUID混入类
    使用UUID作为主键
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True


class VersionMixin(models.Model):
    """
    版本控制混入类
    乐观锁实现
    """
    version = models.PositiveIntegerField(_('版本号'), default=1)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """保存时自动增加版本号"""
        if self.pk:  # 更新操作
            # 检查版本冲突
            current_version = self.__class__.objects.filter(pk=self.pk).values_list('version', flat=True).first()
            if current_version and current_version != self.version:
                raise ValidationError("数据已被其他用户修改，请刷新后重试")
            
            self.version += 1
        
        super().save(*args, **kwargs)


class SortMixin(models.Model):
    """
    排序混入类
    支持拖拽排序
    """
    sort_order = models.PositiveIntegerField(_('排序'), default=0, db_index=True)
    
    class Meta:
        abstract = True
        ordering = ['sort_order', 'id']
    
    def move_up(self):
        """上移"""
        prev_item = self.__class__.objects.filter(
            sort_order__lt=self.sort_order
        ).order_by('-sort_order').first()
        
        if prev_item:
            self.sort_order, prev_item.sort_order = prev_item.sort_order, self.sort_order
            self.save(update_fields=['sort_order'])
            prev_item.save(update_fields=['sort_order'])
    
    def move_down(self):
        """下移"""
        next_item = self.__class__.objects.filter(
            sort_order__gt=self.sort_order
        ).order_by('sort_order').first()
        
        if next_item:
            self.sort_order, next_item.sort_order = next_item.sort_order, self.sort_order
            self.save(update_fields=['sort_order'])
            next_item.save(update_fields=['sort_order'])


class BaseModel(TimestampMixin, StatusMixin):
    """
    基础模型
    包含时间戳和状态功能
    """
    
    class Meta:
        abstract = True
    
    def __str__(self):
        """字符串表示"""
        if hasattr(self, 'name'):
            return self.name
        elif hasattr(self, 'title'):
            return self.title
        else:
            return f"{self.__class__.__name__} #{self.pk}"


class BaseAuditModel(BaseModel, AuditMixin):
    """
    基础审计模型
    包含时间戳、状态和审计功能
    """
    
    class Meta:
        abstract = True


class BaseSoftDeleteModel(BaseModel, SoftDeleteMixin):
    """
    基础软删除模型
    包含时间戳、状态和软删除功能
    """
    
    class Meta:
        abstract = True


class BaseFullModel(BaseModel, AuditMixin, SoftDeleteMixin, VersionMixin):
    """
    完整的基础模型
    包含所有常用功能：时间戳、状态、审计、软删除、版本控制
    """
    
    class Meta:
        abstract = True


class BaseTreeModel(BaseModel):
    """
    基础树形模型
    支持树形结构
    """
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('父级')
    )
    level = models.PositiveIntegerField(_('层级'), default=0, db_index=True)
    path = models.CharField(_('路径'), max_length=500, db_index=True, blank=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """保存时自动计算层级和路径"""
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path}/{self.pk}" if self.parent.path else str(self.pk)
        else:
            self.level = 0
            self.path = str(self.pk) if self.pk else ""
        
        super().save(*args, **kwargs)
        
        # 如果是新创建的对象，需要更新路径
        if not self.path or self.path == "None":
            self.path = str(self.pk)
            self.__class__.objects.filter(pk=self.pk).update(path=self.path)
    
    def get_descendants(self, include_self=False):
        """获取所有子节点"""
        queryset = self.__class__.objects.filter(path__startswith=f"{self.path}/")
        if include_self:
            queryset = queryset | self.__class__.objects.filter(pk=self.pk)
        return queryset
    
    def get_ancestors(self, include_self=False):
        """获取所有父节点"""
        if not self.path:
            return self.__class__.objects.none()
        
        ancestor_ids = [int(id_str) for id_str in self.path.split('/') if id_str.isdigit()]
        if not include_self and self.pk in ancestor_ids:
            ancestor_ids.remove(self.pk)
        
        return self.__class__.objects.filter(pk__in=ancestor_ids)
    
    def get_siblings(self, include_self=False):
        """获取同级节点"""
        queryset = self.__class__.objects.filter(parent=self.parent)
        if not include_self:
            queryset = queryset.exclude(pk=self.pk)
        return queryset
    
    def is_ancestor_of(self, node):
        """判断是否是某个节点的祖先"""
        return node.path.startswith(f"{self.path}/")
    
    def is_descendant_of(self, node):
        """判断是否是某个节点的后代"""
        return self.path.startswith(f"{node.path}/")


class BaseTagModel(BaseModel):
    """
    基础标签模型
    支持标签功能
    """
    tags = models.JSONField(_('标签'), default=list, blank=True)
    
    class Meta:
        abstract = True
    
    def add_tag(self, tag):
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save(update_fields=['tags'])
    
    def remove_tag(self, tag):
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save(update_fields=['tags'])
    
    def has_tag(self, tag):
        """判断是否有指定标签"""
        return tag in self.tags


class BaseMetaModel(BaseModel):
    """
    基础元数据模型
    支持动态字段
    """
    meta_data = models.JSONField(_('元数据'), default=dict, blank=True)
    
    class Meta:
        abstract = True
    
    def set_meta(self, key, value):
        """设置元数据"""
        self.meta_data[key] = value
        self.save(update_fields=['meta_data'])
    
    def get_meta(self, key, default=None):
        """获取元数据"""
        return self.meta_data.get(key, default)
    
    def has_meta(self, key):
        """判断是否有指定元数据"""
        return key in self.meta_data
    
    def remove_meta(self, key):
        """移除元数据"""
        if key in self.meta_data:
            del self.meta_data[key]
            self.save(update_fields=['meta_data'])
