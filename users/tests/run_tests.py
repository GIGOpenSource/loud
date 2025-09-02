#!/usr/bin/env python
"""
Users模块测试运行器
提供便捷的测试执行和覆盖率检查功能
"""

import os
import sys
import subprocess
import django
from django.conf import settings
from django.test.utils import get_runner

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def setup_django():
    """设置Django环境"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
    django.setup()

def run_tests_with_coverage():
    """运行带覆盖率检查的测试"""
    print("🧪 开始运行Users模块测试套件...")
    print("=" * 50)
    
    # 检查coverage是否安装
    try:
        import coverage
    except ImportError:
        print("❌ 错误：未安装coverage包")
        print("请运行：pip install coverage")
        return False
    
    # 设置Django环境
    setup_django()
    
    # 定义测试命令
    test_modules = [
        'users.tests.test_models',
        'users.tests.test_serializers', 
        'users.tests.test_views',
        'users.tests.test_profiles',
        'users.tests.test_preferences',
        'users.tests.test_wallets',
        'users.tests.test_admin',
        'users.tests.test_signals',
        'users.tests.test_urls',
        'users.tests.test_integration',
    ]
    
    # 启动覆盖率收集
    cov = coverage.Coverage(
        source=['users'],
        omit=[
            '*/migrations/*',
            '*/tests/*',
            '*/venv/*',
            '*/.venv/*',
            '*/env/*',
            '*/__pycache__/*',
        ]
    )
    cov.start()
    
    try:
        # 运行测试
        from django.test.runner import DiscoverRunner
        
        test_runner = DiscoverRunner(verbosity=2, interactive=False, keepdb=False)
        failures = test_runner.run_tests(test_modules)
        
        # 停止覆盖率收集
        cov.stop()
        cov.save()
        
        print("\n" + "=" * 50)
        print("📊 测试覆盖率报告")
        print("=" * 50)
        
        # 生成覆盖率报告
        print("\n📋 覆盖率摘要:")
        cov.report(show_missing=True)
        
        # 生成HTML报告
        html_dir = os.path.join(os.path.dirname(__file__), 'coverage_html')
        cov.html_report(directory=html_dir)
        print(f"\n🌐 HTML覆盖率报告已生成: {html_dir}/index.html")
        
        # 检查覆盖率是否达到目标
        total_coverage = cov.report(show_missing=False)
        print(f"\n🎯 总覆盖率: {total_coverage:.1f}%")
        
        if total_coverage >= 100:
            print("✅ 恭喜！达到100%覆盖率目标！")
        elif total_coverage >= 95:
            print("🟡 覆盖率良好，接近100%目标")
        elif total_coverage >= 90:
            print("🟠 覆盖率尚可，需要继续改进")
        else:
            print("🔴 覆盖率不足，需要大幅改进")
        
        # 检查是否有测试失败
        if failures:
            print(f"\n❌ 有 {failures} 个测试失败")
            return False
        else:
            print("\n✅ 所有测试通过！")
            return True
            
    except Exception as e:
        print(f"\n❌ 测试运行出错: {e}")
        return False
    finally:
        cov.stop()

def run_specific_test(test_module):
    """运行特定的测试模块"""
    print(f"🧪 运行测试模块: {test_module}")
    print("=" * 50)
    
    setup_django()
    
    try:
        from django.test.runner import DiscoverRunner
        
        test_runner = DiscoverRunner(verbosity=2, interactive=False)
        failures = test_runner.run_tests([f'users.tests.{test_module}'])
        
        if failures:
            print(f"\n❌ {test_module} 测试失败")
            return False
        else:
            print(f"\n✅ {test_module} 测试通过！")
            return True
            
    except Exception as e:
        print(f"\n❌ 测试运行出错: {e}")
        return False

def run_quick_tests():
    """运行快速测试（不包括覆盖率）"""
    print("🚀 运行快速测试...")
    print("=" * 50)
    
    setup_django()
    
    try:
        from django.test.runner import DiscoverRunner
        
        # 只运行核心测试
        core_tests = [
            'users.tests.test_models',
            'users.tests.test_views',
            'users.tests.test_serializers',
        ]
        
        test_runner = DiscoverRunner(verbosity=1, interactive=False)
        failures = test_runner.run_tests(core_tests)
        
        if failures:
            print(f"\n❌ 有 {failures} 个测试失败")
            return False
        else:
            print("\n✅ 快速测试通过！")
            return True
            
    except Exception as e:
        print(f"\n❌ 测试运行出错: {e}")
        return False

def check_test_files():
    """检查测试文件完整性"""
    print("🔍 检查测试文件完整性...")
    print("=" * 50)
    
    test_dir = os.path.dirname(__file__)
    required_files = [
        'test_models.py',
        'test_serializers.py',
        'test_views.py',
        'test_profiles.py',
        'test_preferences.py',
        'test_wallets.py',
        'test_admin.py',
        'test_signals.py',
        'test_urls.py',
        'test_integration.py',
        'base.py',
    ]
    
    missing_files = []
    existing_files = []
    
    for file_name in required_files:
        file_path = os.path.join(test_dir, file_name)
        if os.path.exists(file_path):
            existing_files.append(file_name)
            print(f"✅ {file_name}")
        else:
            missing_files.append(file_name)
            print(f"❌ {file_name} - 缺失")
    
    print(f"\n📊 统计:")
    print(f"✅ 存在的文件: {len(existing_files)}")
    print(f"❌ 缺失的文件: {len(missing_files)}")
    
    if missing_files:
        print(f"\n🔴 缺失的测试文件: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ 所有测试文件都存在！")
        return True

def generate_test_report():
    """生成测试报告"""
    print("📋 生成测试报告...")
    print("=" * 50)
    
    report = {
        'total_test_files': 0,
        'total_test_classes': 0,
        'total_test_methods': 0,
        'modules': {}
    }
    
    test_dir = os.path.dirname(__file__)
    
    for file_name in os.listdir(test_dir):
        if file_name.startswith('test_') and file_name.endswith('.py'):
            file_path = os.path.join(test_dir, file_name)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 统计测试类和方法
                class_count = content.count('class ') - content.count('class Mock')
                method_count = content.count('def test_')
                
                module_name = file_name[:-3]  # 去掉.py
                report['modules'][module_name] = {
                    'classes': class_count,
                    'methods': method_count,
                    'size': len(content)
                }
                
                report['total_test_files'] += 1
                report['total_test_classes'] += class_count
                report['total_test_methods'] += method_count
                
            except Exception as e:
                print(f"⚠️ 无法分析 {file_name}: {e}")
    
    # 打印报告
    print(f"📁 测试文件总数: {report['total_test_files']}")
    print(f"🏛️ 测试类总数: {report['total_test_classes']}")
    print(f"🧪 测试方法总数: {report['total_test_methods']}")
    
    print(f"\n📊 各模块详情:")
    for module, stats in report['modules'].items():
        print(f"  {module}:")
        print(f"    类: {stats['classes']}, 方法: {stats['methods']}, 大小: {stats['size']} 字符")
    
    return report

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python run_tests.py all          # 运行所有测试（带覆盖率）")
        print("  python run_tests.py quick        # 运行快速测试")
        print("  python run_tests.py check        # 检查测试文件")
        print("  python run_tests.py report       # 生成测试报告")
        print("  python run_tests.py <module>     # 运行特定测试模块")
        return
    
    command = sys.argv[1]
    
    if command == 'all':
        success = run_tests_with_coverage()
    elif command == 'quick':
        success = run_quick_tests()
    elif command == 'check':
        success = check_test_files()
    elif command == 'report':
        generate_test_report()
        success = True
    else:
        success = run_specific_test(command)
    
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()
