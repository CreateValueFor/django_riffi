import yt_dlp

def music_extractor(youtube_url):
    # YouTube에서 음악 다운로드
    # url = "https://www.youtube.com/watch?v=IWbwORvo91U"  # YouTube 링크
    url = youtube_url  # YouTube 링크
    title = ""
    ext = ""

    ydl_opts = {
        'format': 'bestaudio/best',
        # 'outtmpl': 'downloaded_music/%(title)s.%(ext)s',  # 파일 이름에 동영상 제목 포함
        'outtmpl': 'downloaded_music/temp.%(ext)s',  # 파일 이름에 동영상 제목 포함
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        video_info = ydl.extract_info(url, download=False)
        title = video_info['title']+'.wav'
    return 'downloaded_music/temp.wav'