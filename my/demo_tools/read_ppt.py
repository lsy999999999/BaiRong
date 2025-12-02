# -*- coding: utf-8 -*-
"""
读取PPT结构并输出内容摘要
"""

from pptx import Presentation
import sys

ppt_path = r"D:\yulan-onesim\YuLan-OneSim\my\刘师妤-中国人民大学信息学院-From Chaos to order： AI simulation research on the property rights）.pptx"

try:
    prs = Presentation(ppt_path)

    print("="*60)
    print(f"PPT结构分析")
    print("="*60)
    print(f"总页数: {len(prs.slides)}\n")

    for i, slide in enumerate(prs.slides):
        print(f"\n{'='*60}")
        print(f"第{i+1}页 (Slide {i+1})")
        print("="*60)

        # 获取页面标题（通常是第一个文本框）
        title_found = False
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                if not title_found and len(shape.text.strip()) < 100:
                    print(f"【标题】: {shape.text.strip()}")
                    title_found = True
                    break

        # 获取所有文本内容
        print("\n【内容】:")
        text_count = 0
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                text = shape.text.strip()
                if len(text) > 0:
                    # 限制显示长度
                    if len(text) > 150:
                        print(f"  - {text[:150]}...")
                    else:
                        print(f"  - {text}")
                    text_count += 1

        if text_count == 0:
            print("  (无文本内容或仅有图片)")

        # 统计图片数量
        image_count = 0
        for shape in slide.shapes:
            if shape.shape_type == 13:  # 13 = Picture
                image_count += 1

        if image_count > 0:
            print(f"\n【图片】: {image_count}张")

    print("\n" + "="*60)
    print("分析完成")
    print("="*60)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
