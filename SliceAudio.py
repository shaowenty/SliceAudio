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
import shutil

THREAD_COUNT = os.cpu_count() * 5


def readTempAudioFile(filePath):
    return readAudioFile(config["TEMP_PATH"]+"mp3/"+str(filePath)+'.mp3')


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
        right = value[2:4]
        vl = struct.unpack('h', left)[0]
        vr = struct.unpack('h', right)[0]
        v = max(abs(vl), abs(vr))
        # 高帧
        if v >= config['MIN_HEIGH']:
            hight_count += 1
            low_count = 0
            if start_index == -1:
                start_index = i
            # 连续 MIN_HIGHT_COUNT 高帧 开始
            if hight_count == config['MIN_HIGHT_COUNT']:
                start = True
                if len(time_config_list) > 0:  # 修正 结束位置
                    time_config_list[len(time_config_list) -
                                     1][1] = per_fram_time * start_index-1
        # 低帧
        else:
            # 还没开始
            if start == False:
                start_index = -1
                hight_count = 0
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
    if start == True:
        time_config_list.append([
            per_fram_time * start_index,
            per_fram_time * frame_count-1,
            count
        ])
    return time_config_list


def outputTempMp3(_time):
    out = audio[_time[0]:_time[1]]
    outputMp3(out, config["TEMP_PATH"]+"mp3/"+str(_time[2])+".mp3")


def outputMp3(_audio, path):
    _audio.export(path, format="mp3")
    return _audio


def writeFile(filePath, data):
    f = open(filePath, 'w')
    f.write(json.dumps(data,  indent=4))
    f.close


def readFile(filePath):
    f = open(filePath, 'r')
    data = json.loads(f.read())
    f.close()
    return data


global duration_time
duration_time = time.time()


def logTime(message=''):
    global duration_time
    now = time.time()
    print(message, " : ", now - duration_time)
    duration_time = now


if __name__ == "__main__":

    temp = int(input('请输入 1（开始裁切） | 2（已裁切 修改配置文件）:')or 1)
    logTime("ready")
    config = readFile('config.ini')
    logTime("readconfig")
    if temp == 1:
        mp3_path_origin = input("输入音频源地址：")
        audio = readAudioFile(mp3_path_origin)
        # 删除temp/文件夹下文件
        if not os.path.exists(config["TEMP_PATH"]):
            os.makedirs(config["TEMP_PATH"])
        for filepath in os.listdir(config["TEMP_PATH"]):
            if os.path.isfile(config["TEMP_PATH"]+filepath):
                os.remove(config["TEMP_PATH"]+filepath)
            if os.path.isdir(config["TEMP_PATH"]+filepath):
                shutil.rmtree(config["TEMP_PATH"]+filepath)
        # 解析音频文件
        logTime('read audio file')
        time_config_list = analysis(audio, config)
        logTime('analysis audio')
        # 切割临时音频文件
        if not os.path.exists(config["TEMP_PATH"]+"mp3/"):
            os.makedirs(config["TEMP_PATH"]+"mp3/")
        with concurrent.futures.ThreadPoolExecutor(THREAD_COUNT) as executor:
            executor.map(outputTempMp3, time_config_list)
        logTime('slice audio')
    # 读取 config["TEMP_PATH"]+"mp3/" 下 mp3文件
    filelist = os.listdir(config["TEMP_PATH"]+"mp3/")
    i = 0
    while i < len(filelist):
        filepath = filelist[i]
        if not filepath.endswith('.mp3'):
            filelist.pop(i)
        else:
            filelist[i] = int(filepath[0: -4])
            i += 1
    filelist.sort()  # 排序
    writeFile(config["TEMP_PATH"]+'config.json', filelist)
    logTime("write config.json")
    input('配置配置文件 config config.json')
    logTime("input config config.json")

    audioList = []
    with concurrent.futures.ThreadPoolExecutor(THREAD_COUNT) as executor:
        for audio in executor.map(readTempAudioFile, filelist):
            audioList.append(audio)
    # silence audio
    silence_audio = AudioSegment.silent(duration=3000)
    config_audio_path = readFile(config["TEMP_PATH"]+'config.json')
    logTime("read config.json")

    fileName = ''
    count = 0
    time_config = {}
    out_audio_list = []
    out_audio_path_list = []
    start_index = 0
    for i in config_audio_path:
        if type(i) == int:
            out_audio = audioList[start_index]
            for j in range(start_index+1, i+1):
                out_audio += audioList[j]
            time_config[fileName+str(count)] = out_audio.duration_seconds
            if out_audio.duration_seconds < config["MIN_AUDIO_TIME"]:
                out_audio += silence_audio
            out_audio_list.append(out_audio)
            out_audio_path_list.append(
                config['OUT_PUT_PATH']+fileName+"-"+str(count)+'.mp3')
            count += 1
            start_index = i + 1
        else:
            fileName = i
            count = 0
    logTime('analysis config')
    if not os.path.exists(config['OUT_PUT_PATH']):
        os.makedirs(config['OUT_PUT_PATH'])
    for filepath in os.listdir(config['OUT_PUT_PATH']):
        if os.path.isfile(config['OUT_PUT_PATH']+filepath):
            os.remove(config['OUT_PUT_PATH']+filepath)
        elif os.path.isdir(config['OUT_PUT_PATH']+filepath):
            shutil.rmtree(config['OUT_PUT_PATH']+filepath)
    with concurrent.futures.ThreadPoolExecutor(THREAD_COUNT) as executor:
        executor.map(outputMp3, out_audio_list, out_audio_path_list)
    logTime('export audio')
