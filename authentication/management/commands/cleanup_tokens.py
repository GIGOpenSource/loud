"""
清理过期Token的管理命令
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import AuthToken


class Command(BaseCommand):
    help = '清理过期的认证Token'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='清理多少天前过期的token（默认清理所有过期token）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行，不实际删除数据'
        )

    def handle(self, *args, **options):
        """执行清理任务"""
        days = options['days']
        dry_run = options['dry_run']
        
        # 计算过期时间
        cutoff_time = timezone.now()
        if days > 0:
            cutoff_time = cutoff_time - timezone.timedelta(days=days)
        
        # 查找过期的token
        expired_tokens = AuthToken.objects.filter(expires_at__lt=cutoff_time)
        count = expired_tokens.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'试运行：将删除 {count} 个过期token')
            )
            return
        
        # 执行删除
        deleted_count = expired_tokens.delete()[0]
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'成功删除 {deleted_count} 个过期token')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('没有找到过期的token')
            )
