# -*- coding: utf-8 -*-
"""
一键生成所有Demo可视化
运行此脚本自动生成所有演示材料
"""

import os
import sys

def print_banner():
    print("="*60)
    print("  财产权演化Demo可视化生成器")
    print("  Property Rights Evolution Demo Generator")
    print("="*60)
    print()

def check_dependencies():
    """检查依赖"""
    print("📦 检查依赖...")
    required = ['matplotlib', 'pandas', 'plotly', 'numpy']
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"   ✗ {package} (未安装)")

    if missing:
        print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        print(f"   请运行: pip install {' '.join(missing)}")
        return False

    # 检查ffmpeg（可选）
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("   ✓ ffmpeg (视频生成可用)")
        return True
    except:
        print("   ⚠️  ffmpeg 未安装（视频生成将���过，但不影响其他功能）")
        return True

def run_script(script_name, description):
    """运行单个脚本"""
    print(f"\n{'='*60}")
    print(f"▶️  {description}")
    print(f"{'='*60}")

    try:
        exec(open(script_name, encoding='utf-8').read(), {'__name__': '__main__'})
        print(f"✅ {description} - 完成!")
        return True
    except Exception as e:
        print(f"❌ {description} - 失败: {e}")
        return False

def main():
    print_banner()

    # 检查依赖
    if not check_dependencies():
        print("\n❌ 请先安装依赖后再运行此脚本")
        sys.exit(1)

    print("\n" + "="*60)
    print("🚀 开始生成Demo材料...")
    print("="*60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts = [
        # (脚本文件, 描述)
        ('3_key_findings_visualization.py', '生成关键发现图 (key_findings.png)'),
        ('2_interactive_dashboard.py', '生成交互式Dashboard (interactive_dashboard.html)'),
        ('1_grid_evolution_animation.py', '生成网格演化动画 (grid_evolution.mp4)'),
    ]

    results = []
    for script_file, desc in scripts:
        script_path = os.path.join(base_dir, script_file)
        if os.path.exists(script_path):
            success = run_script(script_path, desc)
            results.append((desc, success))
        else:
            print(f"⚠️  跳过 {script_file} (文件不存在)")
            results.append((desc, False))

    # 汇总结果
    print("\n" + "="*60)
    print("📊 生成结果汇总")
    print("="*60)

    for desc, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} - {desc}")

    # 成功提示
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    print("\n" + "="*60)
    if success_count == total_count:
        print("🎉 所有材料生成完成!")
        print("\n📁 生成的文件位置:")
        print(f"   {base_dir}")
        print("\n📖 查看使用说明:")
        print(f"   {os.path.join(base_dir, 'README.md')}")
        print("\n💡 下一步:")
        print("   1. 查看生成的key_findings.png")
        print("   2. 在浏览器中打开interactive_dashboard.html")
        print("   3. （如果成功）播放grid_evolution.mp4")
        print("   4. 阅读README.md了解如何在PPT中使用这些材料")
    else:
        print(f"⚠️  部分材料生成失败 ({success_count}/{total_count})")
        print("\n💡 建议:")
        print("   1. 检查错误信息")
        print("   2. 确保数据文件路径正确")
        print("   3. 如果ffmpeg安装失败，可以只使用交互式Dashboard")

    print("="*60)

if __name__ == '__main__':
    main()
