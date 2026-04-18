import asyncio
import edge_tts
import os
import re
from pathlib import Path

# 设置配音角色
VOICE = "zh-CN-XiaoxiaoNeural"

def strip_markdown(text):
    """
    简单剥离 Markdown 格式，让语音朗读更自然
    """
    # 移除 YAML Front Matter
    text = re.sub(r'---.*?---', '', text, flags=re.DOTALL)
    # 移除 Markdown 链接 [text](url) -> text
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # 移除图片 ![alt](url) -> ""
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # 移除加粗/斜体
    text = text.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
    # 移除 Hugo Shortcodes {{< ... >}} or {{% ... %}}
    text = re.sub(r'\{\{.*?\}\}', '', text)
    # 移除标题符号 #
    text = re.sub(r'#+', '', text)
    return text.strip()

async def generate_audio(text, output_path):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

async def process_post(md_path):
    audio_path = md_path.parent / "audio.mp3"
    
    # 检查是否需要更新：如果音频不存在，或者博文修改时间晚于音频生成时间
    if not audio_path.exists() or md_path.stat().st_mtime > audio_path.stat().st_mtime:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        clean_text = strip_markdown(content)
        if len(clean_text) > 10:  # 忽略太短的内容
            print(f"正在为 {md_path.parent.name} 生成音频...")
            try:
                await generate_audio(clean_text, audio_path)
                print(f"已生成: {audio_path}")
            except Exception as e:
                print(f"生成失败 {md_path}: {e}")

async def main():
    # 扫描 content/blog 下的所有 index.md
    blog_dir = Path("content/blog")
    tasks = []
    for md_path in blog_dir.rglob("index.md"):
        tasks.append(process_post(md_path))
    
    if tasks:
        await asyncio.gather(*tasks)
    else:
        print("未发现博文。")

if __name__ == "__main__":
    asyncio.run(main())
