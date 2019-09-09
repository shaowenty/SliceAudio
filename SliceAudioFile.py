#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
import wave
import struct
from pylab import specgram, zeros, show
import configparser

import concurrent.futures
from pydub import AudioSegment
from ToolFile import Tool
import os
THREAD_COUNT = os.cpu_count() * 5


class SliceAudio:

    @classmethod
    def readAudioFile(self, filePath, format="mp3"):
        return AudioSegment.from_file(filePath, format=format)  # 读取文件

    @classmethod
    def exportMp3(self, audio, path, format="mp3"):
        audio.export(path, format=format)

    @classmethod
    def analysis(self, audio, config):
        frame_count = int(audio.frame_count())
        # 每帧时长  毫秒级 （duration_seconds 秒） * 1000
        per_frame_time = audio.duration_seconds / frame_count * 1000
        start = False
        start_index = -1
        hight_count = 0
        low_count = 0
        time_slice_list = []
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
                    if len(time_slice_list) > 0:  # 修正 结束位置
                        time_slice_list[len(time_slice_list) -
                                        1]["long_end"] = per_frame_time * start_index-1
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
                        time_slice_list.append({
                            "start": per_frame_time * start_index,
                            "end": per_frame_time * i,
                            "long_end": per_frame_time * i
                        })
                        start_index = -1
                        start = 0
                        low_count = 0
                        hight_count = 0
        if start == True:
            time_slice_list.append({
                "start": per_frame_time * start_index,
                "end": per_frame_time * frame_count-1,
                "long_end": per_frame_time * frame_count-1
            })
        return time_slice_list

    @classmethod
    def sliceAudio(self, audio, time_slice_list, export_folder):
        audio_list = []
        export_path_list = []
        for i in range(0, len(time_slice_list)):
            time = time_slice_list[i]
            audio_list.append(
                audio[time["start"]: time["long_end"] or time["end"]])
            export_path_list.append(export_folder+str(i)+'.mp3')
        with concurrent.futures.ThreadPoolExecutor(THREAD_COUNT) as executor:
            executor.map(self.exportMp3, audio_list, export_path_list)

    @classmethod
    def readAudidWithList(self, path, fileList):
        file_list = []
        for file in fileList:
            file_list.append(path+file)
        audioList = []
        with concurrent.futures.ThreadPoolExecutor(THREAD_COUNT) as executor:
            for audio in executor.map(self.readAudioFile, file_list):
                audioList.append(audio)
        return audioList

    @classmethod
    def mergeAudioWithConfig(self, audio_list, audio_path_list, config_list, config):

        silence_audio = AudioSegment.silent(duration=3000)
        out_put_path = config['OUT_PUT_PATH'] or "mp3/"
        time_list = []
        count = 0
        out_audio_list = []
        out_audio_path_list = []
        start_index = 0
        fileName = ''
        for i in range(0, len(config_list)):
            if config_list[i] in audio_path_list:
                j = start_index
                while not audio_path_list[j] in config_list:
                    j += 1
                out_audio = audio_list[start_index]
                for m in range(start_index+1, j):
                    out_audio += audio_list[m]
                # 修正空音
                slice_list = self.analysis(audio_list[j], config)
                if j != start_index:
                    out_audio += audio_list[j][0:slice_list[len(
                        slice_list)-1]['end']]
                else:
                    out_audio = audio_list[j][0:slice_list[len(
                        slice_list)-1]['end']]

                time_list.append(out_audio.duration_seconds)

                if out_audio.duration_seconds < config["MIN_AUDIO_TIME"]:
                    out_audio += silence_audio
                out_audio_list.append(out_audio)
                out_audio_path_list.append(
                    out_put_path+fileName+"-"+str(count)+'.mp3')
                count += 1
                start_index = j+1
            else:
                fileName = config_list[i]
                count = 0

        Tool.delFolder(out_put_path)
        time.sleep(0.1)
        os.makedirs(out_put_path, mode=0o777, exist_ok=True)
        with concurrent.futures.ThreadPoolExecutor(THREAD_COUNT) as executor:
            executor.map(self.exportMp3, out_audio_list, out_audio_path_list)
        Tool.exportJsonData(out_put_path+"time.json", time_list)
        Tool.logTime('export audio')

    @classmethod
    def playStepOne(self, filePath):
        config = Tool.importJsonData("config.ini")

        audio = self.readAudioFile(filePath)
        Tool.logTime('read audio used')

        time_slice_list = self.analysis(audio, config)
        Tool.logTime('analysis audio used')
        # 检测 TEMP_PATH 文件夹
        export_path = config["TEMP_PATH"] or "temp/"
        Tool.delFolder(export_path)
        time.sleep(0.1)
        os.mkdir(export_path)
        export_path += "mp3/"
        os.mkdir(export_path)
        self.sliceAudio(audio, time_slice_list, export_path)
        Tool.logTime('slice audio used')

    @classmethod
    def playStepTwo(self):
        config = Tool.importJsonData("config.ini")
        temp_path = config["TEMP_PATH"] or "temp/"

        mp3_file_list = Tool.readFileListWithSuffix(temp_path+"mp3")
        Tool.exportJsonData(temp_path+'config.json', mp3_file_list)

        input('配置配置文件 config config.json')
        Tool.logTime("read config.json")

        mp3_file_list = Tool.readFileListWithSuffix(temp_path+"mp3")
        Tool.exportJsonData(temp_path+'config.json', mp3_file_list)

        audio_list = self.readAudidWithList(
            temp_path+"mp3/", mp3_file_list)
        Tool.logTime("read audio")

        config_list = Tool.importJsonData(temp_path+'config.json')
        self.mergeAudioWithConfig(
            audio_list, mp3_file_list, config_list, config)
