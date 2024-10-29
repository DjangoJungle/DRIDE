import cv2
import numpy as np

# 读取相机内参矩阵和畸变系数
with np.load('calibration.npz') as X:
    cameraMatrix, distCoeffs = [X[i] for i in ('cameraMatrix', 'distCoeffs')]

# 使用 solvePnP 求解相机的外部参数
def solveDistance(points_2d, img):
    # 定义颜色编码
    color_codes = {'red': 0, 'blue': 1, 'white': 2}

    # 将 points_2d 转换为 NumPy 数组，包含 x, y, color_code
    points_array = np.array([
        [points_2d[0]['x'], points_2d[0]['y'], color_codes[points_2d[0]['color']]],
        [points_2d[1]['x'], points_2d[1]['y'], color_codes[points_2d[1]['color']]],
        [points_2d[2]['x'], points_2d[2]['y'], color_codes[points_2d[2]['color']]],
        [points_2d[3]['x'], points_2d[3]['y'], color_codes[points_2d[3]['color']]],
    ], dtype=np.float32)

    # 提取各个颜色的点
    red_point = points_array[points_array[:, 2] == 0][0][:2]
    blue_point = points_array[points_array[:, 2] == 1][0][:2]
    white_points = points_array[points_array[:, 2] == 2][:, :2]  # 形状 (2,2)

    # 计算向量
    vector_red_blue = blue_point - red_point  # 红点到蓝点的向量
    vectors_red_white = white_points - red_point  # 红点到两个白点的向量 (2,2)

    # 使用叉积判断白点的相对位置
    cross_products = np.cross(vectors_red_white, vector_red_blue)

    # 叉积大于零的为 x 方向的白点，小于零的为 y 方向的白点
    if cross_products[0] > 0:
        white_x_point = white_points[0]
        white_y_point = white_points[1]
    else:
        white_x_point = white_points[1]
        white_y_point = white_points[0]

    # 定义实际尺寸（单位：毫米）
    length = 100  # x 方向长度
    width = 50    # y 方向长度

    # 定义 3D 坐标
    points_3d = np.array([
        [0, 0, 0],          # 红点
        [length, width, 0], # 蓝点
        [length, 0, 0],     # x 方向的白点
        [0, width, 0],      # y 方向的白点
    ], dtype=np.float32)

    # 将 2D 点按顺序排列
    points_2d_ordered = np.array([
        red_point,
        blue_point,
        white_x_point,
        white_y_point,
    ], dtype=np.float32)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, rvec, tvec = cv2.solvePnP(points_3d, points_2d_ordered, cameraMatrix, distCoeffs)
    if ret:
        # 将旋转向量转换为旋转矩阵
        R, _ = cv2.Rodrigues(rvec)
        
        # 计算相机和物品之间的距离
        distance = np.linalg.norm(tvec)
        tx, ty, tz = tvec.flatten() 
        print(f"Distance from camera to the object: {distance:.2f} mm  tx: {tx:.2f}  ty: {ty:.2f}  tz: {tz:.2f}")

        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"Distance: {distance / 10:.2f} cm  height: {tx / 10: .2f} cm"
        org = (50, 50)  # 文字位置
        font_scale = 1
        color = (0, 255, 0)  # 绿色
        thickness = 2
        cv2.putText(img, text, org, font, font_scale, color, thickness, cv2.LINE_AA)
    else:
        print("solvePnP failed.")
    
    return img, (tz, ty, tx)
