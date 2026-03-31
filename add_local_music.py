import os
import json
import logging
import hashlib
import shutil
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义存储路径
MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download", "music")
COVER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download", "cover")
MUSIC_INDEX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download", "music_index.json")

# 确保目录存在
for path in [MUSIC_DIR, COVER_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"创建目录: {path}")

def clean_filename(filename):
    """清理文件名中的非法字符"""
    import re
    return re.sub(r'[\\/:*?"<>|]', '_', filename)

def create_default_cover(title, singer, output_path):
    """创建默认封面"""
    try:
        # 创建封面图片
        img = Image.new('RGB', (300, 300), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        
        # 尝试加载字体
        try:
            font_large = ImageFont.truetype("arial.ttf", 28)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except:
            try:
                font_large = ImageFont.truetype("simhei.ttf", 28)
                font_small = ImageFont.truetype("simhei.ttf", 20)
            except:
                font_large = None
                font_small = None
        
        # 绘制文字
        text_color = (255, 255, 255)
        
        # 标题可能需要截断
        if len(title) > 15:
            title = title[:15] + "..."
        
        title_position = (150 - len(title) * 7, 120)
        singer_position = (150 - len(singer) * 5, 160)
        
        if font_large:
            d.text(title_position, title, fill=text_color, font=font_large)
            d.text(singer_position, singer, fill=text_color, font=font_small)
        else:
            d.text(title_position, title, fill=text_color)
            d.text(singer_position, singer, fill=text_color)
        
        # 添加音符图案
        d.ellipse((130, 80, 150, 100), fill=text_color)
        d.rectangle((148, 95, 152, 170), fill=text_color)
        
        # 保存图片
        img.save(output_path)
        logger.info(f"创建默认封面成功: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"创建默认封面时出错: {str(e)}")
        return None

def load_music_index():
    """加载音乐索引文件"""
    if not os.path.exists(MUSIC_INDEX_FILE):
        logger.warning(f"音乐索引文件不存在，将创建新文件: {MUSIC_INDEX_FILE}")
        return []
    
    try:
        with open(MUSIC_INDEX_FILE, 'r', encoding='utf-8') as f:
            music_index = json.load(f)
        logger.info(f"加载音乐索引成功，共 {len(music_index)} 首歌曲")
        return music_index
    except Exception as e:
        logger.error(f"加载音乐索引失败: {str(e)}")
        return []

def save_music_index(music_index):
    """保存音乐索引到文件"""
    try:
        with open(MUSIC_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(music_index, f, ensure_ascii=False, indent=2)
        logger.info(f"保存音乐索引成功，共 {len(music_index)} 首歌曲")
        return True
    except Exception as e:
        logger.error(f"保存音乐索引失败: {str(e)}")
        return False

def add_song_to_index(song_path, title=None, singer=None, album=None):
    """添加歌曲到索引"""
    try:
        # 获取文件名
        filename = os.path.basename(song_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        # 如果没有提供标题和歌手，尝试从文件名解析
        if not title or not singer:
            parts = name_without_ext.split('-')
            if len(parts) >= 2:
                if not title:
                    title = parts[0].strip()
                if not singer:
                    singer = parts[1].strip()
            else:
                if not title:
                    title = name_without_ext
                if not singer:
                    singer = "未知歌手"
        
        if not album:
            album = "本地音乐"
        
        # 生成唯一ID
        song_id = hashlib.md5((title + singer).encode()).hexdigest()
        
        # 复制文件到音乐目录
        new_filename = clean_filename(f"{title}_{singer}.mp3")
        new_path = os.path.join(MUSIC_DIR, new_filename)
        
        if song_path != new_path:  # 避免复制到自身
            shutil.copy2(song_path, new_path)
        
        # 创建封面
        cover_filename = clean_filename(f"{title}_{singer}.jpg")
        cover_path = os.path.join(COVER_DIR, cover_filename)
        create_default_cover(title, singer, cover_path)
        
        # 创建歌曲信息
        song_info = {
            'id': song_id,
            'title': title,
            'singer': singer,
            'album': album,
            'local_path': new_path,
            'local_cover': cover_path,
            'billboard': '本地导入',
            'duration': 0  # 可以添加获取时长的代码
        }
        
        # 添加到索引
        music_index = load_music_index()
        
        # 检查是否已存在
        for i, song in enumerate(music_index):
            if song.get('id') == song_id:
                music_index[i] = song_info
                logger.info(f"更新歌曲: {title} - {singer}")
                save_music_index(music_index)
                return True
        
        # 添加新歌曲
        music_index.append(song_info)
        logger.info(f"添加歌曲: {title} - {singer}")
        save_music_index(music_index)
        return True
    
    except Exception as e:
        logger.error(f"添加歌曲到索引时出错: {str(e)}")
        return False

def select_files():
    """选择文件对话框"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    file_paths = filedialog.askopenfilenames(
        title="选择音乐文件",
        filetypes=[("音频文件", "*.mp3 *.wav *.flac *.m4a")]
    )
    
    return list(file_paths)

def main():
    """主函数"""
    print("=== 本地音乐导入工具 ===")
    print("此工具将帮助您添加本地音乐文件到音乐索引")
    print()
    
    # 选择文件
    print("请选择要导入的音乐文件...")
    file_paths = select_files()
    
    if not file_paths:
        print("未选择任何文件，程序退出")
        return
    
    print(f"选择了 {len(file_paths)} 个文件")
    
    # 导入文件
    success_count = 0
    for i, file_path in enumerate(file_paths):
        print(f"\n处理文件 [{i+1}/{len(file_paths)}]: {os.path.basename(file_path)}")
        
        # 获取文件名
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        # 尝试解析文件名
        parts = name_without_ext.split('-')
        if len(parts) >= 2:
            default_title = parts[0].strip()
            default_singer = parts[1].strip()
        else:
            default_title = name_without_ext
            default_singer = "未知歌手"
        
        # 手动输入信息
        print("请输入歌曲信息（直接回车使用默认值）：")
        title = input(f"标题 [{default_title}]: ").strip() or default_title
        singer = input(f"歌手 [{default_singer}]: ").strip() or default_singer
        album = input("专辑 [本地音乐]: ").strip() or "本地音乐"
        
        # 添加到索引
        if add_song_to_index(file_path, title, singer, album):
            success_count += 1
    
    print(f"\n导入完成，成功导入 {success_count}/{len(file_paths)} 首歌曲")
    print(f"音乐文件保存在: {MUSIC_DIR}")
    print(f"封面文件保存在: {COVER_DIR}")
    print(f"音乐索引文件: {MUSIC_INDEX_FILE}")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main() 