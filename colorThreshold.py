from pypylon import pylon
import cv2
import numpy as np
from Distance import *
from scipy.optimize import linear_sum_assignment
import threading
import queue

# 定义一个队列用于线程间通信
point_queue = queue.Queue()

# 创建摄像头实例并打开
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

# 开始抓取图像
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
converter = pylon.ImageFormatConverter()

# 将图像格式转换为OpenCV的BGR格式
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

def frameAmend(old_points_2d, new_points_2d):
    error = 200

    # 修正红色点
    if abs(new_points_2d[0]['x'] - old_points_2d[0]['x']) > error or abs(new_points_2d[0]['y'] - old_points_2d[0]['y']) > error:
        new_points_2d[0] = old_points_2d[0].copy()  # 使用字典的复制

    # 修正蓝色点
    if abs(new_points_2d[1]['x'] - old_points_2d[1]['x']) > error or abs(new_points_2d[1]['y'] - old_points_2d[1]['y']) > error:
        new_points_2d[1] = old_points_2d[1].copy()

    # 修正白色点，白色点在 new_points_2d[2] 和 new_points_2d[3]
    distance_matrix = np.zeros((2, 2))
    for i in range(2):
        for j in range(2):
            dx = new_points_2d[i + 2]['x'] - old_points_2d[j + 2]['x']
            dy = new_points_2d[i + 2]['y'] - old_points_2d[j + 2]['y']
            distance_matrix[i, j] = np.hypot(dx, dy)

    row_ind, col_ind = linear_sum_assignment(distance_matrix)

    for i in range(2):
        if distance_matrix[row_ind[i], col_ind[i]] > error:
            new_points_2d[row_ind[i] + 2] = old_points_2d[col_ind[i] + 2].copy()

    old_points_2d = [pt.copy() for pt in new_points_2d]

    return old_points_2d, new_points_2d

def Light_Source_Detection(img, color_to_detect, N):
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

    points = []  # 用于存储中心点的列表
    # 绘制检测到的光源
    for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:N]:
        area = cv2.contourArea(cnt)
        if area > 300:  # 设置面积阈值，过滤掉小区域
            x, y, w, h = cv2.boundingRect(cnt)
            # center = (x + w // 2, y + h // 2)  # 计算中心点
            points.append([x, y, w, h])  # 添加到点的列表中
            # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 绘制矩形框
            # cv2.circle(img, center, 5, (0, 0, 255), -1)

            # font = cv2.FONT_HERSHEY_SIMPLEX
            # font_scale = 1
            # color = (0, 255, 0)  # 绿色
            # thickness = 2
            # # 绘制文本
            # cv2.putText(img, color_to_detect, center, font, font_scale, color, thickness)
    # 如果符合条件的轮廓只有一个，则添加一个相同的点
    if len(points) == 1:
        points.append(points[0])

    return img, points

cnt = 0
# 初始化 old_points_2d 为一个包含 4 个空字典的列表
old_points_2d = [{'x': 0, 'y': 0, 'color': ''} for _ in range(4)]

# 图像处理线程
def process_images():
    global cnt, old_points_2d
    while camera.IsGrabbing():
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if grabResult.GrabSucceeded():
            # 获取图像数据
            img = converter.Convert(grabResult)
            img = img.GetArray()
            img, pos_red = Light_Source_Detection(img, 'red', 1)
            img, pos_blue = Light_Source_Detection(img, 'blue', 1)
            img, pos_white = Light_Source_Detection(img, 'white', 2)
            if cnt == 0 and (not pos_red or not pos_blue or len(pos_white) < 2):
                # 如果第一帧就没有检测到符合条件的光源就重新检测
                continue
            if not pos_red:
                pos_red = old_points_2d[0]
            if not pos_blue:
                pos_blue = old_points_2d[1]
            if len(pos_white) < 2:
                pos_white = [old_points_2d[2], old_points_2d[3]]

            # 定义颜色编码
            color_codes = {'red': 0, 'blue': 1, 'white': 2}

            # 创建 points_2d，包含坐标和颜色信息
            points_2d = [
                {'x': pos_red[0][0] + pos_red[0][2] / 2, 'y': pos_red[0][1] + pos_red[0][3] / 2, 'color': 'red'},
                {'x': pos_blue[0][0] + pos_blue[0][2] / 2, 'y': pos_blue[0][1] + pos_blue[0][3] / 2, 'color': 'blue'},
                {'x': pos_white[0][0] + pos_white[0][2] / 2, 'y': pos_white[0][1] + pos_white[0][3] / 2, 'color': 'white'},
                {'x': pos_white[1][0] + pos_white[1][2] / 2, 'y': pos_white[1][1] + pos_white[1][3] / 2, 'color': 'white'},
            ]

            if cnt == 0:
                old_points_2d = [pt.copy() for pt in points_2d]
                cnt = 1

            old_points_2d, points_2d = frameAmend(old_points_2d, points_2d)

            # 帧修正完以后再画框
            w = 100
            h = 100
            for point in points_2d:
                cv2.rectangle(img, (int(point['x']), int(point['y'])), (int(point['x']) + w, int(point['y']) + h), (0, 255, 0), 2)  # 绘制矩形框
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1
                color = (0, 255, 0)  # 绿色
                thickness = 2
                # 绘制文本
                cv2.putText(img, point['color'], (int(point['x'])+w//2, int(point['y'])+h//2), font, font_scale, color, thickness)

            img, pos = solveDistance(points_2d, img)

            # 将点放入队列
            # for point in points_2d:
            point_queue.put((pos[0], pos[1], pos[2]))  # 假设 z 坐标为 0

            # 显示图像
            cv2.imshow('Light Source Detection', cv2.resize(img, None, None, fx=0.4, fy=0.4))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        grabResult.Release()

    # 释放资源
    camera.StopGrabbing()
    camera.Close()
    cv2.destroyAllWindows()

    # 释放资源
    camera.StopGrabbing()
    camera.Close()
    cv2.destroyAllWindows()

# 启动图像处理线程
image_thread = threading.Thread(target=process_images)
image_thread.daemon = True  # 设置为守护线程
image_thread.start()