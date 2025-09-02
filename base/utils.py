"""
业务工具类
提供通用的业务逻辑和辅助功能
"""

import uuid
import hashlib
import secrets
import string
from io import BytesIO
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger('api')


class IDGenerator:
    """ID生成器"""
    
    @staticmethod
    def generate_uuid():
        """生成UUID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_id(length=8):
        """生成短ID"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_numeric_id(length=6):
        """生成数字ID"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def generate_order_no(prefix="ORDER"):
        """生成订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = IDGenerator.generate_numeric_id(4)
        return f"{prefix}{timestamp}{random_str}"
    
    @staticmethod
    def generate_trade_no(prefix="TRADE"):
        """生成交易号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = IDGenerator.generate_short_id(6)
        return f"{prefix}{timestamp}{random_str}"


class HashUtils:
    """哈希工具类"""
    
    @staticmethod
    def md5(text):
        """MD5哈希"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sha256(text):
        """SHA256哈希"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_file_hash(file_obj):
        """生成文件哈希"""
        hash_md5 = hashlib.md5()
        for chunk in iter(lambda: file_obj.read(4096), b""):
            hash_md5.update(chunk)
        file_obj.seek(0)  # 重置文件指针
        return hash_md5.hexdigest()


class NumberUtils:
    """数字工具类"""
    
    @staticmethod
    def format_decimal(value, decimal_places=2):
        """格式化小数"""
        if value is None:
            return None
        
        decimal_value = Decimal(str(value))
        quantizer = Decimal(10) ** -decimal_places
        return decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP)
    
    @staticmethod
    def format_currency(value, currency='CNY'):
        """格式化货币"""
        if value is None:
            return None
        
        formatted_value = NumberUtils.format_decimal(value, 2)
        
        currency_symbols = {
            'CNY': '¥',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
        }
        
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{formatted_value}"
    
    @staticmethod
    def format_percentage(value, decimal_places=2):
        """格式化百分比"""
        if value is None:
            return None
        
        percentage = value * 100
        formatted_value = NumberUtils.format_decimal(percentage, decimal_places)
        return f"{formatted_value}%"
    
    @staticmethod
    def format_file_size(size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f}{size_names[i]}"


class DateUtils:
    """日期工具类"""
    
    @staticmethod
    def get_date_range(period_type, date_value=None):
        """获取日期范围"""
        if date_value is None:
            date_value = timezone.now().date()
        
        if period_type == 'today':
            start_date = date_value
            end_date = date_value
        elif period_type == 'yesterday':
            start_date = date_value - timedelta(days=1)
            end_date = start_date
        elif period_type == 'this_week':
            start_date = date_value - timedelta(days=date_value.weekday())
            end_date = start_date + timedelta(days=6)
        elif period_type == 'last_week':
            this_week_start = date_value - timedelta(days=date_value.weekday())
            start_date = this_week_start - timedelta(days=7)
            end_date = start_date + timedelta(days=6)
        elif period_type == 'this_month':
            start_date = date_value.replace(day=1)
            if date_value.month == 12:
                end_date = date_value.replace(year=date_value.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = date_value.replace(month=date_value.month + 1, day=1) - timedelta(days=1)
        elif period_type == 'last_month':
            if date_value.month == 1:
                start_date = date_value.replace(year=date_value.year - 1, month=12, day=1)
                end_date = date_value.replace(day=1) - timedelta(days=1)
            else:
                start_date = date_value.replace(month=date_value.month - 1, day=1)
                end_date = date_value.replace(day=1) - timedelta(days=1)
        else:
            raise ValueError(f"不支持的时间段类型: {period_type}")
        
        return start_date, end_date
    
    @staticmethod
    def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
        """格式化日期时间"""
        if dt is None:
            return None
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str, format_str='%Y-%m-%d %H:%M:%S'):
        """解析日期时间字符串"""
        if not date_str:
            return None
        return datetime.strptime(date_str, format_str)
    
    @staticmethod
    def get_age(birth_date):
        """计算年龄"""
        if not birth_date:
            return None
        
        today = date.today()
        age = today.year - birth_date.year
        
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return age
    
    @staticmethod
    def is_weekend(date_value):
        """判断是否是周末"""
        return date_value.weekday() >= 5


class CacheUtils:
    """缓存工具类"""
    
    @staticmethod
    def get_or_set(key, callable_func, timeout=3600):
        """获取缓存或设置缓存"""
        result = cache.get(key)
        if result is None:
            result = callable_func()
            cache.set(key, result, timeout)
        return result
    
    @staticmethod
    def delete_pattern(pattern):
        """删除匹配模式的缓存"""
        # 这里需要根据使用的缓存后端来实现
        # Redis示例
        try:
            from django_redis import get_redis_connection
            r = get_redis_connection("default")
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
        except ImportError:
            # 如果没有Redis，使用基础的cache
            pass
    
    @staticmethod
    def generate_cache_key(*args, prefix="cache"):
        """生成缓存键"""
        key_parts = [str(arg) for arg in args if arg is not None]
        key = f"{prefix}:{'_'.join(key_parts)}"
        return key.replace(' ', '_').lower()


class QRCodeUtils:
    """二维码工具类"""
    
    @staticmethod
    def generate_qr_code(data, size=(200, 200)):
        """生成二维码"""
        if not HAS_QRCODE:
            raise ImportError("请安装qrcode库: pip install qrcode[pil]")
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize(size)
        
        # 转换为字节
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer


class EmailUtils:
    """邮件工具类"""
    
    @staticmethod
    def send_email(subject, message, recipient_list, html_message=None, from_email=None):
        """发送邮件"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email or settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False
            )
            return True
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    @staticmethod
    def send_template_email(template_name, context, subject, recipient_list, from_email=None):
        """使用模板发送邮件"""
        try:
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            return EmailUtils.send_email(
                subject=subject,
                message=plain_message,
                recipient_list=recipient_list,
                html_message=html_message,
                from_email=from_email
            )
        except Exception as e:
            logger.error(f"发送模板邮件失败: {e}")
            return False


class ValidationUtils:
    """验证工具类"""
    
    @staticmethod
    def is_valid_email(email):
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_mobile(mobile):
        """验证手机号格式"""
        import re
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, mobile) is not None
    
    @staticmethod
    def is_valid_id_card(id_card):
        """验证身份证号"""
        import re
        if not re.match(r'^\d{15}$|^\d{18}$|^\d{17}[Xx]$', id_card):
            return False
        
        if len(id_card) == 18:
            return ValidationUtils.validate_id_card_checksum(id_card)
        
        return True
    
    @staticmethod
    def validate_id_card_checksum(id_card):
        """验证18位身份证校验位"""
        if len(id_card) != 18:
            return True
        
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        sum_val = sum(int(id_card[i]) * weights[i] for i in range(17))
        check_index = sum_val % 11
        
        return id_card[17].upper() == check_codes[check_index]


class TextUtils:
    """文本工具类"""
    
    @staticmethod
    def truncate(text, length, suffix='...'):
        """截断文本"""
        if not text or len(text) <= length:
            return text
        return text[:length] + suffix
    
    @staticmethod
    def mask_string(text, start=0, end=None, mask_char='*'):
        """遮掩字符串"""
        if not text:
            return text
        
        if end is None:
            end = len(text)
        
        if start < 0 or end > len(text) or start >= end:
            return text
        
        return text[:start] + mask_char * (end - start) + text[end:]
    
    @staticmethod
    def mask_email(email):
        """遮掩邮箱"""
        if not email or '@' not in email:
            return email
        
        username, domain = email.split('@', 1)
        if len(username) <= 2:
            masked_username = username
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"
    
    @staticmethod
    def mask_mobile(mobile):
        """遮掩手机号"""
        if not mobile or len(mobile) != 11:
            return mobile
        
        return f"{mobile[:3]}****{mobile[-4:]}"
    
    @staticmethod
    def mask_id_card(id_card):
        """遮掩身份证号"""
        if not id_card:
            return id_card
        
        if len(id_card) == 15:
            return f"{id_card[:6]}*****{id_card[-4:]}"
        elif len(id_card) == 18:
            return f"{id_card[:6]}********{id_card[-4:]}"
        
        return id_card


class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def get_file_extension(filename):
        """获取文件扩展名"""
        import os
        return os.path.splitext(filename)[1][1:].lower()
    
    @staticmethod
    def is_image(filename):
        """判断是否是图片文件"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return FileUtils.get_file_extension(filename) in image_extensions
    
    @staticmethod
    def generate_filename(original_filename, prefix=''):
        """生成唯一文件名"""
        ext = FileUtils.get_file_extension(original_filename)
        unique_id = IDGenerator.generate_short_id(12)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        if prefix:
            return f"{prefix}_{timestamp}_{unique_id}.{ext}"
        else:
            return f"{timestamp}_{unique_id}.{ext}"


class BusinessUtils:
    """业务工具类"""
    
    @staticmethod
    def calculate_discount(original_price, discount_rate):
        """计算折扣价"""
        if not original_price or not discount_rate:
            return original_price
        
        discount_amount = original_price * (discount_rate / 100)
        final_price = original_price - discount_amount
        
        return NumberUtils.format_decimal(final_price, 2)
    
    @staticmethod
    def calculate_tax(amount, tax_rate):
        """计算税额"""
        if not amount or not tax_rate:
            return Decimal('0')
        
        tax_amount = amount * (tax_rate / 100)
        return NumberUtils.format_decimal(tax_amount, 2)
    
    @staticmethod
    def generate_invoice_no(prefix='INV'):
        """生成发票号"""
        return IDGenerator.generate_order_no(prefix)
    
    @staticmethod
    def format_address(province, city, district, detail):
        """格式化地址"""
        address_parts = [province, city, district, detail]
        return ''.join(part for part in address_parts if part)
