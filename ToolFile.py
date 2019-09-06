#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import json
import shutil
import os
import numpy as np
import re


class Tool:

    @classmethod
    def logTime(self, message=''):
        now = time.time()
        print(message+": " if (message) else "", now - Tool.duration_time)
        Tool.duration_time = now

    @classmethod
    def exportJsonData(self, filePath, data):
        with open(filePath, 'w') as f:
            f.write(json.dumps(data,  indent=4))

    @classmethod
    def importJsonData(self, filePath):
        with open(filePath, 'r') as f:
            data = json.loads(f.read())
            return data

    @classmethod  # 删除文件夹
    def delFolder(self, folderPath):
        if os.path.exists(folderPath) and os.path.isdir(folderPath):
            shutil.rmtree(folderPath)

    @classmethod
    def readFileListWithSuffix(self, folderPath, suffix=".mp3"):
        if os.path.isdir(folderPath):
            filelist = os.listdir(folderPath)
            i = 0
            while i < len(filelist):
                filepath = filelist[i]
                if not filepath.endswith(suffix):
                    filelist.pop(i)
                else:
                    i += 1
            return Tool.sortStringList(filelist, 3)
        return []

    @classmethod
    def sortStringList(self, stringList, deep):
        while deep > 0:
            deep -= 1
            stringList.sort(key=lambda x: int(re.findall(r"\d+", x)
                                              [deep] if len(re.findall(r"\d+", x)) > deep else 0))
        return stringList


Tool.duration_time = time.time()
