import ffmpeg
import yt_dlp
import os
import shutil
from contextlib import redirect_stdout


def resize_video(video_full_path, output_file_name, target_width = 480, target_height = 360, frame_rate=24):
    i = ffmpeg.input(video_full_path)
    ffmpeg.output(i, output_file_name,
                  **{'r': f'{frame_rate}', 's': f'{target_width}x{target_height}', 'c:v': 'libx264', 'f': 'mp4'}
                  ).overwrite_output().run()

def get_video_duration(video_full_path):
    try:
        probe = ffmpeg.probe(video_full_path)
        duration = float(probe['format']['duration'])
        return duration
    except:
        return 0

def scale_width_video(video_full_path: str, output_file_name: str, target_width = 480, frame_rate=24):
    '''Масштабировать видео по ширине
    для попадания в целевой размер файла в байтах
    '''
    # Определяем параметры видео
    try:
        probe = ffmpeg.probe(video_full_path)
        width = 0
        height = 0
        streams = probe['streams']
        for stream in streams:
            codec_type = stream['codec_type']
            if codec_type == 'video':
                try:
                    width = stream['width']
                    height = stream['height']
                except:
                    width = 0
                    height = 0
        if target_width <= width:
            scale = target_width / width
            new_width = target_width
            new_height = int(scale * height)
            if (new_height % 2 == 1):
                new_height += 1
            i = ffmpeg.input(video_full_path,  nostdin=None)
            #with redirect_stdout(open(os.devnull, "w")):
            ffmpeg.output(i, output_file_name,
                          #**{'r': f'{frame_rate}', 's': f'{new_width}x{new_height}', 'c:v': 'libx264', 'f': 'mp4',}
                           **{'r': f'{frame_rate}', 's': f'{new_width}x{new_height}', 'c:v': 'libx264', 'f': 'mp4', 'loglevel': 'quiet'}
                           ).overwrite_output().run()
        else:
            os.rename(video_full_path, output_file_name)
        return output_file_name
    except Exception as ex:
        try:
            os.rename(video_full_path, output_file_name)
        except:
            pass
        return output_file_name


def compress_video(video_full_path, output_file_name, target_size):
    # Reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
    try:
        min_audio_bitrate = 32000
        max_audio_bitrate = 256000
        probe = ffmpeg.probe(video_full_path)
        # Video duration, in s.
        duration = float(probe['format']['duration'])
        # Audio bitrate, in bps.
        audio_bitrate = float(next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)['bit_rate'])
        # Target total bitrate, in bps.
        target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

        # Target audio bitrate, in bps
        if 10 * audio_bitrate > target_total_bitrate:
            audio_bitrate = target_total_bitrate / 10
            if audio_bitrate < min_audio_bitrate < target_total_bitrate:
                audio_bitrate = min_audio_bitrate
            elif audio_bitrate > max_audio_bitrate:
                audio_bitrate = max_audio_bitrate
        # Target video bitrate, in bps.
        video_bitrate = target_total_bitrate - audio_bitrate
        i = ffmpeg.input(video_full_path, nostdin=None)
        # ffmpeg.output(i, os.devnull,
        #               **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
        #               ).overwrite_output().run()
        # ffmpeg.output(i, output_file_name,
        #               **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
        #               ).overwrite_output().run()
        with redirect_stdout(open(os.devnull, "w")):
            ffmpeg.output(i, output_file_name,
                      **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4', 'c:a': 'aac', 'b:a': audio_bitrate, 'loglevel': 'quiet'}
                      ).overwrite_output().run()
        return output_file_name
    except:
        try:
            os.rename(video_full_path, output_file_name)
        except:
            pass
        return output_file_name


def download_and_compress_video(video_url: str, output_directory: str, target_size = 52000000, max_duration = 1800):
    try:
        with redirect_stdout(open(os.devnull, "w")):
            #output_directory = f'{MAIN_PATH}\\downloads'
            #ydl_opts = {'outtmpl': f'{output_directory}\\%(title)s.%(ext)s'}
            ydl_opts = {'outtmpl': f'{output_directory}\\%(title)s.%(ext)s'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                #ydl.download([video_url])
                info = ydl.extract_info(video_url, download=True)
                try:
                    pass
                    # duration = info['duration']
                    # resolution = info['resolution']
                    # height = info['height']
                    # width = info['width']
                except:
                    pass
                filename = f"{output_directory}\\{info['title']}.{info['ext']}"
            # Определяем дляительность видео если больше 30 минут то выкладываем ссылкой
            duration = get_video_duration(filename)
            if duration != 0 and duration <= max_duration:
                # Определяем возможно ли выложить видео в исходном виде
                filesize = os.path.getsize(filename)
                # Если размер файла больше 50 мегабайт пытаемся перкодировать видео
                if filesize > target_size:
                #if filesize > 0:
                    new_filename1 = scale_width_video(filename, f'{filename}_tmp1')
                    # Удаляем исходный файл
                    try:
                        os.remove(filename)
                    except:
                        pass
                    # Переименовываем файл в исходный
                    try:
                        os.rename(new_filename1, filename)
                    except:
                        pass
                # Снова проверяем размер файла если он больше целевого то пытаемся сжимать битрейт
                filesize = os.path.getsize(filename)
                if filesize > target_size:
                    new_filename2 = compress_video(filename, f'{filename}_tmp2', int(target_size / 1000))
                    try:
                        os.remove(filename)
                    except:
                        pass
                    try:
                        os.rename(new_filename2, filename)
                    except:
                        pass
                pass
                # Подставляем нормальное расширение
                pos = filename.find('.')
                new_filename = filename[:pos]
                new_filename = f'{new_filename}.mp4'
                try:
                    # Удаляем файл старый если он существует
                    #os.remove(new_filename)
                    pass
                except:
                    pass
                os.rename(filename, new_filename)
                return new_filename
            else:
                # Видео слишком длинное выкладывваем ссылкой
                return ''
    except Exception as ex:
        return f''