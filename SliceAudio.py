#!/usr/bin/python
# -*- coding: UTF-8 -*-
from pydub import AudioSegment
import wave
import struct
# from scipy import *
from pylab import specgram, zeros, show
import configparser
import time
import json
import concurrent.futures
import os

THREAD_COUNT = os.cpu_count() * 5


def readAudioFile(filePath, format="mp3"):
    return AudioSegment.from_file(filePath, format=format)  # 读取文件


def analysis(audio, config):
    frame_count = int(audio.frame_count())
    # 每帧时长  毫秒级 （duration_seconds 秒）
    per_fram_time = audio.duration_seconds / frame_count * 1000
    start = False
    start_index = -1
    hight_count = 0
    low_count = 0
    time_config_list = []
    count = 0
    for i in range(0, frame_count):
        value = audio.get_frame(i)
        # 左声道
        left = value[0:2]
        v = struct.unpack('h', left)[0]
        # 高帧
        if v >= config['MIN_HEIGH']:
            hight_count += 1
            low_count = 0
            if start_index == -1:
                start_index = i
            # 连续 MIN_HIGHT_COUNT 高帧 开始
            if hight_count == config['MIN_HIGHT_COUNT']:
                start = True
        # 低帧
        else:
            # 还没开始
            if start == False:
                start_index = -1
                # 已经开始
            else:
                low_count += 1
                # 连续MIN_LOW_COUNT低帧 结束
                if low_count == config['MIN_LOW_COUNT']:
                    time_config_list.append([
                        per_fram_time * start_index,
                        per_fram_time * i,
                        count
                    ])
                    start_index = -1
                    start = 0
                    low_count = 0
                    hight_count = 0
                    count += 1
    return time_config_list


def outputTempMp3(_time):
    outputMp3(audio, _time, config["TEMP_MP3_PATH"]+str(_time[2])+".mp3")


def outputMp3(audio, time, path):
    out = audio[time[0]:time[1]]
    out.export(path, format="mp3")
    return out


def writeFile(filePath, data):
    f = open(filePath, 'w')
    f.write(json.dumps(data,  indent=4))
    f.close


def readFile(filePath):
    f = open(filePath, 'r')
    data = json.loads(f.read())
    f.close()
    return data


if __name__ == "__main__":
    # mp3_path_origin = input("输入音频源地址：")
    # temp = int(input('请输入 1（开始裁切） | 2（已裁切 修改配置文件）:'))
    config = readFile('config.ini')

    audio = readAudioFile("PL2-1配音文稿.mp3")
    duration_time = time.perf_counter()
    time_config_list = analysis(audio, config)
    duration_time = time.perf_counter()-duration_time
    print(duration_time)
    with concurrent.futures.ThreadPoolExecutor(THREAD_COUNT) as executor:
        executor.map(outputTempMp3, time_config_list)
    duration_time = time.perf_counter()-duration_time
    print(duration_time)

    # start_index = []
    # end_index = []
    # per_frame_thread = int(frame_count / THREAD_COUNT)
    # duration_time = time.perf_counter()
    # for start in range(0, frame_count, per_frame_thread):
    #     start_index.append(start)
    #     end_index.append(start+per_frame_thread)
    # v = []
    # v_temp = []
    # print(time.perf_counter() - duration_time)
    # with concurrent.futures.ThreadPoolExecutor(THREAD_COUNT) as executor:
    #     for _v in executor.map(readAudioPerFrameV, start_index, end_index):
    #         v += _v
    #         v_temp.append(_v)
    # duration_time = time.perf_counter()-duration_time
    # print(duration_time)
    # print('end')
    # print(index_array)
    # config = {}
    # if temp == 1:
    #     # 读取配置文件
    #     config = readFile('config.ini')
    #     config = analysisMp3(config)

    #     config['del_data'] = []
    #     config['need_add_time'] = False
    #     config['outPath'] = 'temp/'
    #     outputMp3(config)  # 第一次生成 temp mp3
    #     writeFile('config.ini', config)  # 保存一次config

    # config = readFile('config.ini')
    # config['del_data'] = []
    # data = []
    # for i in range(len(config['start_list'])):
    #     data.append(i)
    # writeFile('temp/slice.txt', data)
    # input('配置 temp/slice.txt 文件')
    # data = readFile('temp/slice.txt')
    # for i in range(len(config['start_list'])):
    #     if i in data:
    #         continue
    #     else:
    #         config['del_data'].append(i)
    # config['need_add_time'] = True
    # config['outPath'] = 'mp3/'
    # time = outputMp3(config)  # 第二次生成 temp mp3
    # writeFile('mp3/time.txt', time)
    # writeFile('config.ini', config)
