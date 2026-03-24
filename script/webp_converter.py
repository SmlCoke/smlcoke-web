import os
import re
from pathlib import Path
from PIL import Image

# ================= 配置区 =================
DOCS_DIR = "../docs/AI-Tools" # 你的文档目录
# 支持转换的原始格式
IMAGE_EXTS = {'.png', '.jpg', '.jpeg'} 
# WEBP 压缩质量 (0-100)，85 是画质和体积的最佳平衡点，肉眼完全看不出区别
WEBP_QUALITY = 85 
# ==========================================

def convert_images_and_update_md():
    converted_count = 0
    updated_md_count = 0

    # 1. 遍历并转换图片
    print("⏳ 开始转换图片为 WebP...")
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in IMAGE_EXTS:
                old_filepath = os.path.join(root, file)
                # 生成新的 webp 路径
                new_filepath = os.path.splitext(old_filepath)[0] + '.webp'
                
                try:
                    # 打开并转换保存
                    with Image.open(old_filepath) as img:
                        # RGB 模式转换（防止部分带透明通道的图在某些情况下报错）
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGBA')
                        img.save(new_filepath, 'WEBP', quality=WEBP_QUALITY)
                    
                    # 删除原文件
                    os.remove(old_filepath)
                    converted_count += 1
                    print(f"✅ 转换成功: {file} -> {Path(new_filepath).name}")
                except Exception as e:
                    print(f"❌ 转换失败 {old_filepath}: {e}")

    print(f"\n🎉 图片转换完成！共转换了 {converted_count} 张图片。")
    print("-" * 40)
    print("⏳ 开始同步更新 Markdown 文件中的链接...")

    # 2. 遍历并更新 Markdown 文件
    # 正则表达式解释：匹配 ![任意文字](任意路径.png/jpg/jpeg) 忽略大小写
    # (?i) 表示忽略大小写，匹配 .png, .PNG 等
    md_pattern = re.compile(r'(!\[.*?\]\([^)]+?)\.(png|jpg|jpeg)(?=\))', re.IGNORECASE)
    # 兼容 HTML 标签写法： <img src="...png">
    html_pattern = re.compile(r'(<img[^>]+src=["\'][^"\']+?)\.(png|jpg|jpeg)(?=["\'])', re.IGNORECASE)

    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 执行正则替换
                new_content = md_pattern.sub(r'\1.webp', content)
                new_content = html_pattern.sub(r'\1.webp', new_content)

                # 如果内容有变化，才写回文件
                if new_content != content:
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    updated_md_count += 1
                    print(f"🔗 更新链接: {md_path}")

    print(f"\n🎉 Markdown 更新完成！共修改了 {updated_md_count} 个文件。")

if __name__ == "__main__":
    convert_images_and_update_md()