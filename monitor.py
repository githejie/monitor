#!/usr/bin/env python
#coding: utf-8

# 导入必须的包
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import datetime
import imutils
import time
import cv2


# 初始化摄像头并且获取一个指向原始数据的引用
camera = PiCamera()
camera.resolution = tuple([640, 480])
camera.framerate = 16
rawCapture = PiRGBArray(camera, size=tuple([640, 480]))
 
# 等待摄像头模块启动, 随后初始化平均帧, 最后
# 上传时间戳, 以及运动帧计数器
print "[INFO] warming up..."
time.sleep(2.5)
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0

# 从摄像头逐帧捕获数据
for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # 抓取原始NumPy数组来表示图像并且初始化
    # 时间戳以及occupied/unoccupied文本
    frame = f.array
    timestamp = datetime.datetime.now()
    text = "Unoccupied"
 
    # 调整帧尺寸，转换为灰阶图像并进行模糊
    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
 
    # 如果平均帧是None，初始化它
    if avg is None:
        print "[INFO] starting background model..."
        avg = gray.copy().astype("float")
        rawCapture.truncate(0)
        continue
 
    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    # 对变化图像进行阀值化, 膨胀阀值图像来填补
    # 孔洞, 在阀值图像上找到轮廓线
    thresh = cv2.threshold(frameDelta, 5, 255,
        cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
 
    # 遍历轮廓线
    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < 5000:
            continue
 
        # 计算轮廓线的外框, 在当前帧上画出外框,
        # 并且更新文本
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Occupied"
 
    # 在当前帧上标记文本和时间戳
    ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
        0.35, (0, 0, 255), 1)

    # 判断安保视频是否需要显示在屏幕上
    if 1 == 1:
        # 显示安视频
        cv2.imshow("Security Feed", frame)
        key = cv2.waitKey(1) & 0xFF
 
        # 如果q被按下，跳出循环
        if key == ord("q"):
            break
 
    # 清理数据流为下一帧做准备
    rawCapture.truncate(0)
