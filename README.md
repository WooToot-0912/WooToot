# 本地音乐服务器

这是一个简单的本地音乐服务器，可以用于微信小程序音乐播放器。

## 功能

- 本地音乐文件管理
- 音乐搜索API
- 音乐播放API
- 封面图片API
- 服务器状态API

## 文件说明

- `simple_local_music.py`: 简化版本地音乐服务器，提供API接口
- `add_local_music.py`: 本地音乐导入工具，用于添加本地音乐文件到索引
- `start_music_server.bat`: 启动本地音乐服务器的批处理文件
- `import_music.bat`: 运行本地音乐导入工具的批处理文件
- `netease_music.py`: 网易云音乐API接口（目前可能无法使用）
- `crawl_music.py`: 爬取网易云音乐榜单歌曲的脚本（依赖于netease_music.py）

## 使用方法

### 导入本地音乐

1. 运行 `import_music.bat`
2. 在弹出的文件选择对话框中选择要导入的音乐文件（支持MP3、WAV、FLAC、M4A）
3. 按照提示输入歌曲信息（标题、歌手、专辑）
4. 完成导入后，音乐文件会被复制到 `download/music` 目录，封面文件会被创建在 `download/cover` 目录

### 启动服务器

1. 运行 `start_music_server.bat`
2. 服务器将在 http://127.0.0.1:5000 启动
3. 可以通过 http://127.0.0.1:5000/api/status 检查服务器状态
4. 在微信小程序中配置API地址为服务器的IP地址和端口（例如：http://192.168.1.x:5000）

### API接口

- 搜索音乐：`/api/search?keyword=关键词`
- 播放音乐：`/api/play/歌曲ID`
- 获取封面：`/api/cover/歌曲ID`
- 服务器状态：`/api/status`

## 注意事项

- 网易云音乐API可能已经失效，建议使用本地音乐功能
- 如果遇到中文路径问题，请确保使用UTF-8编码（批处理文件中已设置 `chcp 65001`）
- 本服务器仅供开发测试使用，不建议在生产环境中使用 