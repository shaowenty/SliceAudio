#!/usr/bin/python
# -*- coding: UTF-8 -*-
from ToolFile import Tool
from numpy import unicode
from SliceAudioFile import SliceAudio

if __name__ == "__main__":
    step = input('请输入 1（开始裁切） | 2（已裁切 修改配置文件）:')
    Tool.logTime("ready")
    if step == "1":
        mp3_path = input("输入音频源地址：")
        SliceAudio.playStepOne(mp3_path)
    SliceAudio.playStepTwo()
    print("end")
