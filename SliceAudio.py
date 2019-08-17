from pydub import AudioSegment
import wave
import struct
# from scipy import *
from pylab import specgram, zeros, show
import configparser
import json

wave_temp_path = 'temp/temp.wav'  # 临时wav文件名称地址

song = []


def readMp3(filePath):
    global song
    song = AudioSegment.from_file(filePath, format="mp3")  # 读取文件


def analysisMp3(config):
    song.export(wave_temp_path, 'wav')  # 生成临时 wav文件
    wavefile = wave.open(wave_temp_path, 'r')  # 读取临时wav文件
    numframes = wavefile.getnframes()  # 获取总帧数

    high_count = 0  # 高音谱计数
    cur_sart = -1  # 开始位置
    cur_end = -1
    cur_start_list = []  # 记录开始位置
    cur_end_list = []  # 记录结束位置
    low_count = 0

    for i in range(numframes):
        val = wavefile.readframes(1)
        left = val[0:2]  # 左声道
# right = val[2:4]
        v = struct.unpack('h', left)[0]
        v = abs(v)
        if v > int(config["hight_frame"]):  # 坡度大于 hight_frame
            high_count += 1
            low_count = 0
            cur_end = -1
            if cur_sart == -1:
                cur_sart = i
        if high_count == int(config["min_hight_frame_start"]):  # 数量达到10帧
            high_count += 1
            cur_start_list.append(cur_sart)
        if v < int(config["hight_frame"])and cur_sart != -1:  # 有开始  并且 坡度小于 1000
            low_count = low_count + 1
        # 结束（用high_count标记是否有开始）
        if low_count == int(config["min_low_frame_end"])and cur_end == -1 and high_count >= int(config["min_hight_frame_start"]):
            high_count = 0
            cur_end = i
            cur_sart = -1
            cur_end_list.append(i)
        # 有开始 最后一帧位置
        if i == numframes and high_count >= int(config["min_hight_frame_start"]) and cur_end == -1:
            cur_end_list.append(i)
    perframeTime = song.duration_seconds / numframes * 1000  # 每帧时长
    config['start_list'] = cur_start_list
    config['end_list'] = cur_end_list
    config['perframeTime'] = perframeTime
    if len(cur_end_list) == len(cur_start_list):
        return config
    else:
        print('len(cur_end_list) != len(cur_start_list)',
              len(cur_end_list), len(cur_start_list))
        input()
        exit()


def outputMp3(config):
    i = 0
    time = []
    silence_audio = AudioSegment.silent(duration=3000)
    fime_pre = 0
    while i < len(config['start_list']):
        fime_pre = i
        start = config['start_list'][i] * config["perframeTime"]
        if config["del_data"]:
            while i+1 in config["del_data"]:
                i += 1
        if i >= len(config['start_list']):
            i = len(config['start_list'])-1  # 修正最后一个
        end = config['end_list'][i]*config["perframeTime"]
        out = song[start:end]
        time.append((end-start)/1000)
        if config['need_add_time']:
            if end-start < 3000:
                out += silence_audio
        out.export(config['outPath']+str(fime_pre)+'.mp3', format="mp3")
        i += 1
    return time


def writeFile(filePath, data):
    f = open(filePath, 'w')
    f.write(json.dumps(data))
    f.close


def readFile(filePath):
    f = open(filePath, 'r')
    data = json.loads(f.read())
    f.close()
    return data


if __name__ == "__main__":
    mp3_path_origin = input("输入音频源地址：")
    readMp3(mp3_path_origin)
    temp = int(input('请输入 1（开始裁切） | 2（已裁切 修改配置文件）:'))
    config = {}
    if temp == 1:
        # 读取配置文件
        config = readFile('config.ini')
        config = analysisMp3(config)

        config['del_data'] = []
        config['need_add_time'] = False
        config['outPath'] = 'temp/'
        outputMp3(config)  # 第一次生成 temp mp3
        writeFile('config.ini', config)  # 保存一次config

    config = readFile('config.ini')
    config['del_data'] = []
    data = []
    for i in range(len(config['start_list'])):
        data.append(i)
    writeFile('temp/slice.txt', data)
    input('配置 temp/slice.txt 文件')
    data = readFile('temp/slice.txt')
    for i in range(len(config['start_list'])):
        if i in data:
            continue
        else:
            config['del_data'].append(i)
    config['need_add_time'] = True
    config['outPath'] = 'mp3/'
    time = outputMp3(config)  # 第二次生成 temp mp3
    writeFile('mp3/time.txt', time)
    writeFile('config.ini', config)
