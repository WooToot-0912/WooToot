import os
import json
import logging
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import re
from PIL import Image, ImageDraw, ImageFont
import subprocess
import tempfile
import time
import hashlib
import shutil
from functools import lru_cache
from threading import Lock
import mimetypes
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('music_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # 启用跨域支持

# 定义存储路径
BASE_DIR = Path(__file__).parent
MUSIC_DIR = BASE_DIR / "download" / "music"
COVER_DIR = BASE_DIR / "download" / "cover"
CACHE_DIR = BASE_DIR / "download" / "cache"
MUSIC_INDEX_FILE = BASE_DIR / "download" / "music_index.json"

# 确保目录存在
for path in [MUSIC_DIR, COVER_DIR, CACHE_DIR]:
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"确保目录存在: {path}")

# 全局缓存和锁
music_index_cache = None
music_index_lock = Lock()
cache_timestamp = 0
CACHE_TIMEOUT = 300  # 5分钟缓存

# 加载音乐索引（带缓存）
def load_music_index():
    """加载音乐索引文件，使用缓存提高性能"""
    global music_index_cache, cache_timestamp

    current_time = time.time()

    # 检查缓存是否有效
    with music_index_lock:
        if (music_index_cache is not None and
            current_time - cache_timestamp < CACHE_TIMEOUT):
            logger.debug("使用缓存的音乐索引")
            return music_index_cache

    # 缓存失效或不存在，重新加载
    if not MUSIC_INDEX_FILE.exists():
        logger.warning(f"音乐索引文件不存在: {MUSIC_INDEX_FILE}")
        return []

    try:
        with open(MUSIC_INDEX_FILE, 'r', encoding='utf-8') as f:
            music_index = json.load(f)

        # 验证和清理索引数据
        valid_music = []
        for song in music_index:
            if validate_song_data(song):
                valid_music.append(song)
            else:
                logger.warning(f"跳过无效歌曲数据: {song.get('title', 'Unknown')}")

        # 更新缓存
        with music_index_lock:
            music_index_cache = valid_music
            cache_timestamp = current_time

        logger.info(f"加载音乐索引成功，共 {len(valid_music)} 首有效歌曲")
        return valid_music

    except Exception as e:
        logger.error(f"加载音乐索引失败: {str(e)}")
        return []

def validate_song_data(song):
    """验证歌曲数据的完整性"""
    required_fields = ['id', 'title', 'singer']
    for field in required_fields:
        if not song.get(field):
            return False

    # 检查文件是否存在
    if 'local_path' in song:
        return Path(song['local_path']).exists()

    return True

# 搜索本地音乐
def search_local_music(keyword):
    """从本地索引中搜索音乐"""
    try:
        music_index = load_music_index()
        if not music_index:
            return []
        
        results = []
        keyword = keyword.lower()
        
        for song in music_index:
            title = song.get('title', '').lower()
            singer = song.get('singer', '').lower()
            album = song.get('album', '').lower()
            
            # 匹配标题、歌手或专辑
            if (keyword in title) or (keyword in singer) or (keyword in album):
                # 确保文件存在
                if 'local_path' in song and os.path.exists(song['local_path']):
                    # 添加API路径
                    song['cover_url'] = f'/api/cover/{song["id"]}'
                    song['audio_url'] = f'/api/play/{song["id"]}'
                    results.append(song)
        
        logger.info(f"本地搜索关键词 '{keyword}' 找到 {len(results)} 首歌曲")
        return results
    
    except Exception as e:
        logger.error(f"搜索本地音乐时出错: {str(e)}")
        return []

# API路由
@app.route('/api/search', methods=['GET'])
def api_search():
    """搜索歌曲API"""
    keyword = request.args.get('keyword', '')
    platform = request.args.get('platform', 'local')  # 默认使用本地平台
    
    if not keyword:
        logger.warning("搜索请求缺少关键词")
        return jsonify({'code': 400, 'message': '请提供搜索关键词', 'data': []})
    
    logger.info(f"接收到搜索请求: {keyword}, 平台: {platform}")
    
    # 搜索结果
    results = []
    
    # 所有平台都使用本地搜索
    # 网易云模块已移除，所有搜索都使用本地索引
    results = search_local_music(keyword)
    
    logger.info(f"搜索结果数量: {len(results)}")
    return jsonify({'code': 200, 'message': 'success', 'data': results})

@app.route('/api/play/<song_id>', methods=['GET', 'HEAD'])
def api_play(song_id):
    """播放歌曲API"""
    logger.info(f"接收到播放请求，歌曲ID: {song_id}")
    
    # 从索引中查找歌曲路径
    song_path = None
    music_index = load_music_index()
    
    # 记录所有歌曲ID，用于调试
    all_ids = [str(song.get('id', '')) for song in music_index]
    logger.info(f"索引中的歌曲ID数量: {len(all_ids)}")
    
    for song in music_index:
        if str(song.get('id')) == str(song_id):
            logger.info(f"找到匹配歌曲: {song.get('title')} - {song.get('singer')}")
            if 'local_path' in song:
                song_path = song['local_path']
                if os.path.exists(song_path):
                    logger.info(f"歌曲文件存在: {song_path}")
                    break
                else:
                    logger.error(f"歌曲文件不存在: {song_path}")
            else:
                logger.error(f"歌曲缺少本地路径: {song}")
    
    if not song_path:
        logger.error(f"歌曲不存在或路径无效: {song_id}")
        return jsonify({'code': 404, 'message': '歌曲不存在或路径无效'}), 404
    
    if not os.path.exists(song_path):
        logger.error(f"歌曲文件不存在: {song_path}")
        return jsonify({'code': 404, 'message': '歌曲文件不存在'}), 404
    
    # 检查文件大小是否超过微信小程序限制
    file_size = os.path.getsize(song_path)
    logger.info(f"歌曲文件大小: {file_size} 字节")
    
    # 如果文件大小超过2MB，转码为较小的文件
    if file_size > 2 * 1024 * 1024:
        logger.warning(f"文件大小 {file_size} 字节超过2MB限制，进行转码")
        converted_path = convert_audio_for_wechat(song_path)
        if converted_path:
            logger.info(f"转码成功，使用转码后的文件: {converted_path}")
            return send_file(converted_path, mimetype='audio/mpeg')
    
    # 为所有音频文件使用流式传输，避免大文件问题
    return stream_local_file(song_path)

@app.route('/api/cover/<song_id>', methods=['GET'])
def api_cover(song_id):
    """获取歌曲封面API"""
    logger.info(f"接收到封面请求，歌曲ID: {song_id}")
    
    # 网易云音乐功能已移除
    # if str(song_id).startswith('ne_'):
    #     return jsonify({'code': 404, 'message': '网易云音乐功能已移除'}), 404
    
    # 从索引中查找封面路径
    cover_path = None
    music_index = load_music_index()
    
    for song in music_index:
        if str(song.get('id')) == str(song_id):
            logger.info(f"找到匹配歌曲: {song.get('title')} - {song.get('singer')}")
            if 'local_cover' in song:
                cover_path = song['local_cover']
                if os.path.exists(cover_path):
                    logger.info(f"封面文件存在: {cover_path}")
                    break
                else:
                    logger.error(f"封面文件不存在: {cover_path}")
            else:
                logger.error(f"歌曲缺少封面路径: {song}")
    
    # 如果没有找到封面，使用默认封面
    if not cover_path or not os.path.exists(cover_path):
        logger.warning(f"封面不存在: {song_id}")
        # 这里可以返回一个默认封面
        try:
            # 创建一个简单的默认封面
            default_cover_path = os.path.join(COVER_DIR, "default_cover.jpg")
            
            # 只在第一次需要时创建默认封面
            if not os.path.exists(default_cover_path):
                img = Image.new('RGB', (300, 300), color=(73, 109, 137))
                d = ImageDraw.Draw(img)
                
                # 尝试加载字体
                try:
                    font = ImageFont.truetype("arial.ttf", 28)
                except:
                    font = None
                
                # 绘制文字
                text = "无封面"
                if font:
                    d.text((100, 150), text, fill=(255, 255, 255), font=font)
                else:
                    d.text((100, 150), text, fill=(255, 255, 255))
                
                # 保存图片
                img.save(default_cover_path)
                logger.info(f"创建默认封面: {default_cover_path}")
            
            cover_path = default_cover_path
        except Exception as e:
            logger.error(f"创建默认封面失败: {str(e)}")
            return jsonify({'code': 404, 'message': '封面不存在且无法创建默认封面'}), 404
    
    logger.info(f"返回封面文件: {cover_path}")
    
    # 允许跨域访问
    try:
        response = send_file(cover_path, mimetype='image/jpeg')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    except Exception as e:
        logger.error(f"send_file出错: {str(e)}")
        # 尝试手动读取文件并返回
        try:
            with open(cover_path, 'rb') as f:
                data = f.read()
                resp = Response(data, mimetype='image/jpeg')
                resp.headers.add('Access-Control-Allow-Origin', '*')
                resp.headers.add('Access-Control-Allow-Headers', 'Content-Type')
                resp.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
                return resp
        except Exception as e2:
            logger.error(f"手动读取封面文件出错: {str(e2)}")
            return jsonify({'code': 500, 'message': f'读取封面文件出错: {str(e2)}'}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """服务状态API"""
    # 统计文件数量
    try:
        music_files = len([f for f in os.listdir(MUSIC_DIR) if os.path.isfile(os.path.join(MUSIC_DIR, f))])
        cover_files = len([f for f in os.listdir(COVER_DIR) if os.path.isfile(os.path.join(COVER_DIR, f))])
    except:
        music_files = 0
        cover_files = 0
    
    # 检查本地索引是否存在
    local_index_exists = os.path.exists(MUSIC_INDEX_FILE)
    local_songs_count = 0
    
    if local_index_exists:
        try:
            with open(MUSIC_INDEX_FILE, 'r', encoding='utf-8') as f:
                music_index = json.load(f)
                local_songs_count = len(music_index)
        except Exception:
            local_songs_count = 0
    
    return jsonify({
        'code': 200,
        'message': 'API服务正常运行',
        'data': {
            'platform': {
                'current': 'local',
                'name': '本地音乐'
            },
            'storage': {
                'music_files': music_files,
                'cover_files': cover_files,
                'music_dir': MUSIC_DIR,
                'cover_dir': COVER_DIR
            },
            'local': {
                'index_exists': local_index_exists,
                'songs_count': local_songs_count
            }
        }
    })

# 直接访问路由（便于调试）
@app.route('/play/<song_id>', methods=['GET'])
def api_play_direct(song_id):
    return api_play(song_id)

@app.route('/cover/<song_id>', methods=['GET'])
def api_cover_direct(song_id):
    return api_cover(song_id)

# 添加本地文件流式传输函数
def stream_local_file(file_path):
    """流式传输本地文件，确保不超过微信小程序2MB限制"""
    logger.info(f"开始流式传输本地文件: {file_path}")
    
    # 确保文件存在
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return jsonify({'code': 404, 'message': '文件不存在'}), 404
    
    try:
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        
        # 确定内容类型
        content_type = 'audio/mpeg'
        if file_path.lower().endswith('.mp3'):
            content_type = 'audio/mpeg'
        elif file_path.lower().endswith('.m4a'):
            content_type = 'audio/mp4'
        elif file_path.lower().endswith('.wav'):
            content_type = 'audio/wav'
        
        logger.info(f"文件总大小: {file_size} 字节, 内容类型: {content_type}")
        
        # 处理Range请求
        range_header = request.headers.get('Range', None)
        if range_header:
            byte1, byte2 = 0, None
            match = re.search(r'(\d+)-(\d*)', range_header)
            if match:
                groups = match.groups()
                
                if groups[0]:
                    byte1 = int(groups[0])
                if groups[1]:
                    byte2 = int(groups[1])
                else:
                    byte2 = min(byte1 + 2 * 1024 * 1024 - 1, file_size - 1)  # 限制为2MB片段
                
                length = byte2 - byte1 + 1
                logger.info(f"范围请求: {byte1}-{byte2}, 长度: {length}")
                
                def generate_range():
                    with open(file_path, 'rb') as f:
                        f.seek(byte1)
                        data = f.read(length)
                        yield data
                
                resp = Response(
                    generate_range(),
                    status=206,
                    mimetype=content_type
                )
                
                resp.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
                resp.headers.add('Accept-Ranges', 'bytes')
                resp.headers.add('Content-Length', str(length))
                resp.headers.add('Access-Control-Allow-Origin', '*')
                resp.headers.add('Access-Control-Allow-Headers', 'Range, Content-Type')
                resp.headers.add('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
                
                return resp
        
        # 如果没有Range请求，返回小块数据
        def generate():
            # 初始化计数器
            bytes_sent = 0
            # 微信小程序的大小限制（2MB = 2 * 1024 * 1024 字节）
            MAX_SIZE = 2 * 1024 * 1024
            
            with open(file_path, 'rb') as f:
                # 只发送前2MB的数据
                data = f.read(MAX_SIZE)
                yield data
            
            logger.info(f"流式传输完成，总共发送: {len(data)} 字节")
        
        # 创建流式响应
        response = Response(
            generate(),
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{os.path.basename(file_path)}"',
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Range, Content-Type',
                'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS'
            }
        )
        
        return response
    
    except Exception as e:
        logger.error(f"流式传输文件时出错: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return jsonify({'code': 500, 'message': f'流式传输失败: {str(e)}'}), 500

# 添加音频转码函数
def convert_audio_for_wechat(file_path):
    """将大音频文件转码为小文件，以适应微信小程序2MB限制"""
    try:
        # 创建缓存目录
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download", "cache")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # 生成缓存文件名
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        output_path = os.path.join(cache_dir, f"{file_hash}_small.mp3")
        
        # 如果已经有转换好的文件，直接返回
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size <= 2 * 1024 * 1024:
                logger.info(f"使用缓存的转码文件: {output_path}, 大小: {file_size} 字节")
                return output_path
        
        # 使用ffmpeg转码为低比特率MP3
        # 检查是否安装了ffmpeg
        try:
            # 尝试创建一个30秒的预览版本，比特率为64k
            cmd = [
                'ffmpeg', '-y', '-i', file_path,
                '-ss', '0', '-t', '30',  # 只取前30秒
                '-b:a', '64k',  # 低比特率
                '-ar', '22050',  # 降低采样率
                '-ac', '1',  # 单声道
                output_path
            ]
            
            logger.info(f"执行转码命令: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"转码失败: {stderr.decode()}")
                return None
            
            # 检查转码后的文件大小
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"转码后的文件大小: {file_size} 字节")
                if file_size <= 2 * 1024 * 1024:
                    return output_path
                else:
                    logger.warning(f"转码后的文件仍然超过2MB，尝试进一步降低质量")
                    # 如果仍然超过2MB，进一步降低质量
                    cmd = [
                        'ffmpeg', '-y', '-i', file_path,
                        '-ss', '0', '-t', '20',  # 只取前20秒
                        '-b:a', '32k',  # 更低的比特率
                        '-ar', '16000',  # 更低的采样率
                        '-ac', '1',  # 单声道
                        output_path
                    ]
                    
                    logger.info(f"执行二次转码命令: {' '.join(cmd)}")
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    
                    if process.returncode != 0:
                        logger.error(f"二次转码失败: {stderr.decode()}")
                        return None
                    
                    if os.path.exists(output_path):
                        return output_path
            
            return None
        except Exception as e:
            logger.error(f"执行ffmpeg转码时出错: {str(e)}")
            
            # 如果ffmpeg不可用，尝试使用简单的方法：截取文件前2MB
            logger.info("尝试使用简单方法：截取文件前2MB")
            try:
                with open(file_path, 'rb') as src_file:
                    data = src_file.read(2 * 1024 * 1024)  # 读取前2MB
                
                with open(output_path, 'wb') as dest_file:
                    dest_file.write(data)
                
                return output_path
            except Exception as e2:
                logger.error(f"截取文件失败: {str(e2)}")
                return None
    
    except Exception as e:
        logger.error(f"转码音频时出错: {str(e)}")
        return None

@app.route('/api/stream', methods=['GET'])
def api_stream():
    """流式传输歌曲，支持质量选择"""
    song_id = request.args.get('id', '')
    title = request.args.get('title', '')
    artist = request.args.get('artist', '')
    quality = request.args.get('quality', 'low')  # low或high
    
    logger.info(f"接收到流式传输请求，歌曲ID: {song_id}，质量: {quality}")
    
    # 从索引中查找歌曲路径
    song_path = None
    music_index = load_music_index()
    
    for song in music_index:
        if str(song.get('id')) == str(song_id):
            logger.info(f"找到匹配歌曲: {song.get('title')} - {song.get('singer')}")
            if 'local_path' in song:
                song_path = song['local_path']
                if os.path.exists(song_path):
                    logger.info(f"歌曲文件存在: {song_path}")
                    break
                else:
                    logger.error(f"歌曲文件不存在: {song_path}")
            else:
                logger.error(f"歌曲缺少本地路径: {song}")
    
    if not song_path:
        logger.error(f"歌曲不存在或路径无效: {song_id}")
        return jsonify({'code': 404, 'message': '歌曲不存在或路径无效'}), 404
    
    if not os.path.exists(song_path):
        logger.error(f"歌曲文件不存在: {song_path}")
        return jsonify({'code': 404, 'message': '歌曲文件不存在'}), 404
    
    # 根据质量选择处理方式
    if quality == 'low' or quality == 'preview':
        # 创建低质量预览版本
        logger.info("创建低质量预览版本")
        converted_path = convert_audio_for_wechat(song_path)
        if converted_path:
            return stream_local_file(converted_path)
        else:
            logger.warning("转换失败，返回原文件")
            return stream_local_file(song_path)
    else:
        # 返回高质量版本
        logger.info("返回原始高质量版本")
        return stream_local_file(song_path)

if __name__ == "__main__":
    # 显示API服务信息
    print("=" * 50)
    print("本地音乐API服务已启动")
    print(f"音乐目录: {MUSIC_DIR}")
    print(f"封面目录: {COVER_DIR}")
    print(f"索引文件: {MUSIC_INDEX_FILE}")
    print("=" * 50)
    
    # 启动Flask应用，监听所有网络接口，这样手机可以通过IP地址访问
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True) 