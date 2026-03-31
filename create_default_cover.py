"""
创建默认封面图片
这个脚本用于生成一个默认的音乐封面图片，供音乐播放器使用
"""
import os
from PIL import Image, ImageDraw, ImageFont

def create_default_cover():
    """创建默认封面图片"""
    print("开始创建默认封面图片...")
    
    # 确定存储路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cover_path = os.path.join(script_dir, "default_cover.jpg")
    
    # 创建一个彩色背景
    img = Image.new('RGB', (300, 300), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    
    # 尝试添加文字
    try:
        # 尝试使用系统字体
        try:
            font_large = ImageFont.truetype("arial.ttf", 40)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except:
            # 尝试另一种字体
            try:
                font_large = ImageFont.truetype("simhei.ttf", 40)
                font_small = ImageFont.truetype("simhei.ttf", 20)
            except:
                # 如果找不到字体，使用默认字体
                font_large = None
                font_small = None
        
        # 画一个音符图案
        # 音符头部
        d.ellipse((120, 80, 150, 110), fill=(255, 255, 255))
        # 音符柄
        d.rectangle((148, 90, 152, 180), fill=(255, 255, 255))
        
        # 添加文字
        text_color = (255, 255, 255)
        if font_large:
            d.text((100, 130), "音乐", fill=text_color, font=font_large)
            d.text((80, 200), "微信小程序播放器", fill=text_color, font=font_small)
        else:
            d.text((100, 130), "音乐", fill=text_color)
            d.text((80, 200), "微信小程序播放器", fill=text_color)
        
        # 画一个装饰边框
        d.rectangle((10, 10, 290, 290), outline=(255, 255, 255), width=2)
        
    except Exception as e:
        print(f"添加图案时出错: {str(e)}")
    
    # 保存图片
    try:
        img.save(cover_path, quality=95)
        print(f"默认封面图片已创建: {cover_path}")
        return True
    except Exception as e:
        print(f"保存图片时出错: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_default_cover()
    if success:
        print("默认封面图片已创建")
    else:
        print("创建默认封面图片失败") 