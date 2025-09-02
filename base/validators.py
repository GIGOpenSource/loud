"""
基础验证器
提供标准化的数据验证功能
"""

import re
import os
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils.deconstruct import deconstructible
from datetime import date, datetime
from decimal import Decimal
import mimetypes


@deconstructible
class ChineseNameValidator(RegexValidator):
    """中文姓名验证器"""
    regex = r'^[\u4e00-\u9fa5]{2,10}$'
    message = '请输入2-10个中文字符的姓名'
    flags = 0


@deconstructible
class UsernameValidator(RegexValidator):
    """用户名验证器"""
    regex = r'^[a-zA-Z0-9_-]{3,20}$'
    message = '用户名只能包含字母、数字、下划线和连字符，长度3-20个字符'
    flags = 0


@deconstructible
class MobileValidator(RegexValidator):
    """手机号验证器"""
    regex = r'^1[3-9]\d{9}$'
    message = '请输入正确的手机号码'
    flags = 0


@deconstructible
class PasswordValidator:
    """密码强度验证器"""
    
    def __init__(self, min_length=8, require_uppercase=True, require_lowercase=True, 
                 require_digits=True, require_special=True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
    
    def __call__(self, value):
        """验证密码"""
        if len(value) < self.min_length:
            raise ValidationError(f'密码长度至少需要{self.min_length}个字符')
        
        if self.require_uppercase and not re.search(r'[A-Z]', value):
            raise ValidationError('密码必须包含至少一个大写字母')
        
        if self.require_lowercase and not re.search(r'[a-z]', value):
            raise ValidationError('密码必须包含至少一个小写字母')
        
        if self.require_digits and not re.search(r'\d', value):
            raise ValidationError('密码必须包含至少一个数字')
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError('密码必须包含至少一个特殊字符')
    
    def __eq__(self, other):
        return (
            isinstance(other, PasswordValidator) and
            self.min_length == other.min_length and
            self.require_uppercase == other.require_uppercase and
            self.require_lowercase == other.require_lowercase and
            self.require_digits == other.require_digits and
            self.require_special == other.require_special
        )


@deconstructible
class IDCardValidator(RegexValidator):
    """身份证号验证器"""
    
    def __init__(self):
        super().__init__(
            regex=r'^\d{15}$|^\d{18}$|^\d{17}[Xx]$',
            message='请输入正确的身份证号码'
        )
    
    def __call__(self, value):
        """验证身份证号"""
        super().__call__(value)
        
        # 18位身份证校验位验证
        if len(value) == 18:
            if not self.validate_id_card_checksum(value):
                raise ValidationError('身份证号码校验位不正确')
    
    def validate_id_card_checksum(self, id_card):
        """验证18位身份证校验位"""
        if len(id_card) != 18:
            return True
        
        # 权重因子
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        # 校验码
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        # 计算校验码
        sum_val = sum(int(id_card[i]) * weights[i] for i in range(17))
        check_index = sum_val % 11
        
        return id_card[17].upper() == check_codes[check_index]


@deconstructible
class BankCardValidator(RegexValidator):
    """银行卡号验证器"""
    regex = r'^\d{16,19}$'
    message = '请输入正确的银行卡号'
    flags = 0
    
    def __call__(self, value):
        """验证银行卡号"""
        super().__call__(value)
        
        # Luhn算法验证
        if not self.luhn_check(value):
            raise ValidationError('银行卡号格式不正确')
    
    def luhn_check(self, card_number):
        """Luhn算法验证"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0


@deconstructible
class FileExtensionValidator:
    """文件扩展名验证器"""
    
    def __init__(self, allowed_extensions=None, allowed_mimes=None):
        self.allowed_extensions = allowed_extensions or []
        self.allowed_mimes = allowed_mimes or []
    
    def __call__(self, value):
        """验证文件扩展名"""
        if not value:
            return
        
        # 获取文件扩展名
        ext = os.path.splitext(value.name)[1][1:].lower()
        
        # 验证扩展名
        if self.allowed_extensions and ext not in self.allowed_extensions:
            raise ValidationError(
                f'不支持的文件格式。支持的格式：{", ".join(self.allowed_extensions)}'
            )
        
        # 验证MIME类型
        if self.allowed_mimes:
            mime_type, _ = mimetypes.guess_type(value.name)
            if mime_type not in self.allowed_mimes:
                raise ValidationError(
                    f'不支持的文件类型。支持的类型：{", ".join(self.allowed_mimes)}'
                )
    
    def __eq__(self, other):
        return (
            isinstance(other, FileExtensionValidator) and
            self.allowed_extensions == other.allowed_extensions and
            self.allowed_mimes == other.allowed_mimes
        )


@deconstructible
class FileSizeValidator:
    """文件大小验证器"""
    
    def __init__(self, max_size=None, min_size=None):
        self.max_size = max_size
        self.min_size = min_size
    
    def __call__(self, value):
        """验证文件大小"""
        if not value:
            return
        
        size = value.size
        
        if self.max_size and size > self.max_size:
            raise ValidationError(
                f'文件大小不能超过{self.format_size(self.max_size)}'
            )
        
        if self.min_size and size < self.min_size:
            raise ValidationError(
                f'文件大小不能小于{self.format_size(self.min_size)}'
            )
    
    def format_size(self, size):
        """格式化文件大小"""
        if size < 1024:
            return f'{size}B'
        elif size < 1024 * 1024:
            return f'{size // 1024}KB'
        elif size < 1024 * 1024 * 1024:
            return f'{size // (1024 * 1024)}MB'
        else:
            return f'{size // (1024 * 1024 * 1024)}GB'
    
    def __eq__(self, other):
        return (
            isinstance(other, FileSizeValidator) and
            self.max_size == other.max_size and
            self.min_size == other.min_size
        )


@deconstructible
class ImageValidator:
    """图片验证器"""
    
    def __init__(self, max_width=None, max_height=None, min_width=None, min_height=None):
        self.max_width = max_width
        self.max_height = max_height
        self.min_width = min_width
        self.min_height = min_height
    
    def __call__(self, value):
        """验证图片"""
        if not value:
            return
        
        try:
            from PIL import Image
            image = Image.open(value)
            width, height = image.size
            
            if self.max_width and width > self.max_width:
                raise ValidationError(f'图片宽度不能超过{self.max_width}像素')
            
            if self.max_height and height > self.max_height:
                raise ValidationError(f'图片高度不能超过{self.max_height}像素')
            
            if self.min_width and width < self.min_width:
                raise ValidationError(f'图片宽度不能小于{self.min_width}像素')
            
            if self.min_height and height < self.min_height:
                raise ValidationError(f'图片高度不能小于{self.min_height}像素')
                
        except ImportError:
            raise ValidationError('请安装Pillow库以支持图片验证')
        except Exception:
            raise ValidationError('无效的图片文件')
    
    def __eq__(self, other):
        return (
            isinstance(other, ImageValidator) and
            self.max_width == other.max_width and
            self.max_height == other.max_height and
            self.min_width == other.min_width and
            self.min_height == other.min_height
        )


@deconstructible
class DateRangeValidator:
    """日期范围验证器"""
    
    def __init__(self, min_date=None, max_date=None):
        self.min_date = min_date
        self.max_date = max_date
    
    def __call__(self, value):
        """验证日期范围"""
        if not value:
            return
        
        if self.min_date and value < self.min_date:
            raise ValidationError(f'日期不能早于{self.min_date}')
        
        if self.max_date and value > self.max_date:
            raise ValidationError(f'日期不能晚于{self.max_date}')
    
    def __eq__(self, other):
        return (
            isinstance(other, DateRangeValidator) and
            self.min_date == other.min_date and
            self.max_date == other.max_date
        )


@deconstructible
class FutureDateValidator:
    """未来日期验证器"""
    
    def __init__(self, allow_today=True):
        self.allow_today = allow_today
    
    def __call__(self, value):
        """验证是否是未来日期"""
        if not value:
            return
        
        today = date.today()
        
        if self.allow_today:
            if value < today:
                raise ValidationError('日期不能是过去日期')
        else:
            if value <= today:
                raise ValidationError('日期必须是未来日期')


@deconstructible
class PastDateValidator:
    """过去日期验证器"""
    
    def __init__(self, allow_today=True):
        self.allow_today = allow_today
    
    def __call__(self, value):
        """验证是否是过去日期"""
        if not value:
            return
        
        today = date.today()
        
        if self.allow_today:
            if value > today:
                raise ValidationError('日期不能是未来日期')
        else:
            if value >= today:
                raise ValidationError('日期必须是过去日期')


@deconstructible
class DecimalRangeValidator:
    """小数范围验证器"""
    
    def __init__(self, min_value=None, max_value=None, max_digits=None, decimal_places=None):
        self.min_value = min_value
        self.max_value = max_value
        self.max_digits = max_digits
        self.decimal_places = decimal_places
    
    def __call__(self, value):
        """验证小数"""
        if value is None:
            return
        
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(f'值不能小于{self.min_value}')
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(f'值不能大于{self.max_value}')
        
        if self.max_digits is not None:
            digits = len(str(value).replace('.', '').replace('-', ''))
            if digits > self.max_digits:
                raise ValidationError(f'总位数不能超过{self.max_digits}位')
        
        if self.decimal_places is not None:
            decimal_part = str(value).split('.')
            if len(decimal_part) > 1 and len(decimal_part[1]) > self.decimal_places:
                raise ValidationError(f'小数位数不能超过{self.decimal_places}位')
    
    def __eq__(self, other):
        return (
            isinstance(other, DecimalRangeValidator) and
            self.min_value == other.min_value and
            self.max_value == other.max_value and
            self.max_digits == other.max_digits and
            self.decimal_places == other.decimal_places
        )


@deconstructible
class JSONValidator:
    """JSON格式验证器"""
    
    def __call__(self, value):
        """验证JSON格式"""
        if not value:
            return
        
        import json
        try:
            json.loads(value)
        except (ValueError, TypeError):
            raise ValidationError('请输入有效的JSON格式')


@deconstructible
class URLValidator(RegexValidator):
    """增强的URL验证器"""
    
    def __init__(self, schemes=None):
        self.schemes = schemes or ['http', 'https']
        pattern = r'^(?:' + '|'.join(self.schemes) + r')://[^\s/$.?#].[^\s]*$'
        super().__init__(
            regex=pattern,
            message='请输入有效的URL地址',
            flags=re.IGNORECASE
        )


# 预定义的常用验证器实例
chinese_name_validator = ChineseNameValidator()
username_validator = UsernameValidator()
mobile_validator = MobileValidator()
id_card_validator = IDCardValidator()
bank_card_validator = BankCardValidator()
json_validator = JSONValidator()
future_date_validator = FutureDateValidator()
past_date_validator = PastDateValidator()

# 文件验证器实例
image_validator = FileExtensionValidator(
    allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
    allowed_mimes=['image/jpeg', 'image/png', 'image/gif', 'image/webp']
)

document_validator = FileExtensionValidator(
    allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'rtf'],
    allowed_mimes=[
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/rtf'
    ]
)

# 文件大小验证器
image_size_validator = FileSizeValidator(max_size=5 * 1024 * 1024)  # 5MB
document_size_validator = FileSizeValidator(max_size=10 * 1024 * 1024)  # 10MB
