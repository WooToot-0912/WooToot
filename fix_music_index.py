import os
import json
import logging
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义存储路径
MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download", "music")
COVER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download", "cover")
MUSIC_INDEX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download", "music_index.json")

def clean_filename(filename):
    """清理文件名中的非法字符"""
    import re
    return re.sub(r'[\\/:*?"<>|]', '_', filename)

def fix_music_index():
    """修复音乐索引文件的编码和标题/歌手顺序问题"""
    logger.info("开始修复音乐索引文件...")
    
    # 检查索引文件是否存在
    if not os.path.exists(MUSIC_INDEX_FILE):
        logger.error(f"音乐索引文件不存在: {MUSIC_INDEX_FILE}")
        return False
    
    try:
        # 读取现有索引
        with open(MUSIC_INDEX_FILE, 'r', encoding='utf-8') as f:
            try:
                music_index = json.load(f)
                logger.info(f"成功读取音乐索引，共 {len(music_index)} 首歌曲")
            except json.JSONDecodeError:
                logger.error("JSON解析失败，尝试使用其他编码")
                f.seek(0)
                content = f.read()
                music_index = json.loads(content)
        
        # 备份原始索引
        backup_file = MUSIC_INDEX_FILE + ".bak"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(music_index, f, ensure_ascii=False, indent=2)
            logger.info(f"已创建备份: {backup_file}")
        
        # 扫描音乐目录中的所有MP3文件
        mp3_files = []
        for root, dirs, files in os.walk(MUSIC_DIR):
            for file in files:
                if file.lower().endswith('.mp3'):
                    mp3_files.append(os.path.join(root, file))
        
        logger.info(f"在音乐目录中找到 {len(mp3_files)} 个MP3文件")
        
        # 创建新的索引
        new_index = []
        
        # 处理每个MP3文件
        for mp3_file in mp3_files:
            filename = os.path.basename(mp3_file)
            name_without_ext = os.path.splitext(filename)[0]
            
            # 尝试从文件名解析标题和歌手
            parts = name_without_ext.split('_')
            if len(parts) >= 2:
                title = parts[0].strip()
                singer = parts[1].strip()
            else:
                # 尝试使用 - 分隔符
                parts = name_without_ext.split('-')
                if len(parts) >= 2:
                    title = parts[0].strip()
                    singer = parts[1].strip()
                else:
                    title = name_without_ext
                    singer = "未知歌手"
            
            # 生成唯一ID
            song_id = hashlib.md5((title + singer).encode()).hexdigest()
            
            # 创建封面路径
            cover_filename = clean_filename(f"{title}_{singer}.jpg")
            cover_path = os.path.join(COVER_DIR, cover_filename)
            
            # 如果封面不存在，尝试创建默认封面
            if not os.path.exists(cover_path):
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    img = Image.new('RGB', (300, 300), color=(73, 109, 137))
                    d = ImageDraw.Draw(img)
                    
                    # 尝试加载字体
                    try:
                        font_large = ImageFont.truetype("arial.ttf", 28)
                        font_small = ImageFont.truetype("arial.ttf", 20)
                    except:
                        font_large = None
                        font_small = None
                    
                    # 绘制文字
                    text_color = (255, 255, 255)
                    
                    # 标题可能需要截断
                    if len(title) > 15:
                        title_display = title[:15] + "..."
                    else:
                        title_display = title
                    
                    title_position = (150 - len(title_display) * 7, 120)
                    singer_position = (150 - len(singer) * 5, 160)
                    
                    if font_large:
                        d.text(title_position, title_display, fill=text_color, font=font_large)
                        d.text(singer_position, singer, fill=text_color, font=font_small)
                    else:
                        d.text(title_position, title_display, fill=text_color)
                        d.text(singer_position, singer, fill=text_color)
                    
                    # 添加音符图案
                    d.ellipse((130, 80, 150, 100), fill=text_color)
                    d.rectangle((148, 95, 152, 170), fill=text_color)
                    
                    # 保存图片
                    img.save(cover_path)
                    logger.info(f"创建封面: {cover_path}")
                except Exception as e:
                    logger.error(f"创建封面失败: {str(e)}")
            
            # 创建歌曲信息
            song_info = {
                'id': song_id,
                'title': title,
                'singer': singer,
                'album': "本地音乐",
                'local_path': mp3_file,
                'local_cover': cover_path,
                'billboard': '本地导入',
                'duration': 0
            }
            
            new_index.append(song_info)
            logger.info(f"处理歌曲: {title} - {singer}")
        
        # 保存新索引
        with open(MUSIC_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_index, f, ensure_ascii=False, indent=2)
        
        logger.info(f"音乐索引修复完成，共 {len(new_index)} 首歌曲")
        return True
    
    except Exception as e:
        logger.error(f"修复音乐索引时出错: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("开始修复音乐索引文件...")
    if fix_music_index():
        print("修复完成！")
    else:
        print("修复失败，请查看日志。")
    input("按回车键退出...") 