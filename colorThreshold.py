from pypylon import pylon
import cv2
import numpy as np
from Distance import *

# 创建摄像头实例并打开
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

# 开始抓取图像
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
converter = pylon.ImageFormatConverter()

# 将图像格式转换为OpenCV的BGR格式
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

# 设置要检测的颜色：'red'、'white'、'blue'、'all'
color_to_detect = 'red'  # 可以更改为您需要的颜色

def Light_Source_Detection(image, color_to_detect):
    # img = image.GetArray()

    # 预处理：去噪
    img_blur = cv2.GaussianBlur(img, (5, 5), 0)

    # 转换为HSV颜色空间
    hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)

    # 根据选择的颜色设置HSV范围
    if color_to_detect == 'red':
        # 红色可能出现在HSV空间的两个区域
        lower_red1 = np.array([0, 70, 150])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 150])
        upper_red2 = np.array([180, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
    elif color_to_detect == 'blue':
        lower_blue = np.array([100, 70, 150])
        upper_blue = np.array([124, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
    elif color_to_detect == 'white':
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 25, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
    else:  # 'all'表示不限制颜色
        # 假设高亮区域为光源
        lower_bright = np.array([0, 0, 200])
        upper_bright = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower_bright, upper_bright)

    # 去除噪点
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    #x, y, w, h = 0, 0, 0, 0
    N = 2  # 您想要的点的数量
    points = []  # 用于存储中心点的列表
    # 绘制检测到的光源
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:N]:
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 300:  # 设置面积阈值，过滤掉小区域
                x, y, w, h = cv2.boundingRect(cnt)
                center = (x + w // 2, y + h // 2)  # 计算中心点
                points.append([x,y,w,h])  # 添加到点的列表中
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 绘制矩形框
                cv2.circle(img, center, 5, (0, 0, 255), -1)

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1
                color = (0, 255, 0)  # 绿色
                thickness = 2
                # 绘制文本
                cv2.putText(img, color_to_detect, center, font, font_scale, color, thickness)
    # 如果符合条件的轮廓只有一个，则添加一个相同的点
    if len(points) == 1:
        points.append(points[0])

    return img, points   

last_pos_red = None
last_pos_blue = None
# 主循环
while camera.IsGrabbing():
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    if grabResult.GrabSucceeded():
        # 获取图像数据
        img = converter.Convert(grabResult)
        img = img.GetArray()
        img, pos_red = Light_Source_Detection(img, color_to_detect)
        # print(pos_red)
        img, pos_blue = Light_Source_Detection(img, 'blue')
        # print(f"X方向相距{abs(pos_blue[0]-pos_red[0]+(pos_blue[2]-pos_red[2])/2)}")
        # print(f"Y方向相距{abs(pos_blue[1]-pos_red[1]+(pos_blue[3]-pos_red[3])/2)}")
        if not pos_red:
            pos_red = last_pos_red
        if not pos_blue:
            pos_blue = last_pos_blue

        # 更新上一次的光源位置
        last_pos_red = pos_red
        last_pos_blue = pos_blue

        # print(pos_blue)
        # print(pos_red)
        if pos_red and pos_blue:
            points_2d = np.array([
                [pos_blue[0][0]+pos_blue[0][2]/2, pos_blue[0][1]+pos_blue[0][3]/2],
                [pos_red[0][0]+pos_red[0][2]/2, pos_red[0][1]+pos_red[0][3]/2],
                [pos_blue[1][0]+pos_blue[1][2]/2, pos_blue[1][1]+pos_blue[1][3]/2],
                [pos_red[1][0]+pos_red[1][2]/2, pos_red[1][1]+pos_red[1][3]/2],
            ], dtype=np.float32)
            # img = solveDistance(points_2d, img)
        ''''''
        # 显示图像
        cv2.imshow('Light Source Detection', cv2.resize(
                    img, None, None, fx=0.4, fy=0.4))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    grabResult.Release()

# 释放资源
camera.StopGrabbing()
camera.Close()
cv2.destroyAllWindows()
