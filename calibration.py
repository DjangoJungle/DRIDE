import cv2
import numpy as np
import matplotlib.pyplot as plt

# 棋盘格的大小
chessboard_size = (8, 11)       # 列优先
frame_size = (2592, 1944)
square_size = 20.0

# 定义终止条件（迭代100次或者精度达到0.001）
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-6)

# 定义真实世界中的棋盘格角点坐标
obj_points = []  # 3D 点在真实世界坐标系中的位置
img_points = []  # 相机图像中的角点

# 准备棋盘格角点的3D位置，假设棋盘格每个方格边长为1个单位
objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2) * square_size

# 加载左右相机的棋盘格图像
for i in range(16):  # 至少采集10对图像
    img = cv2.imread(f'./calibration/{i}.png', 0)
    
    # 检测左、右图像中的角点
    ret, corners = cv2.findChessboardCorners(img, chessboard_size, None)
    
    if ret:
        obj_points.append(objp)
        # 优化角点位置，增加准确性
        corners = cv2.cornerSubPix(img, corners, (11,11), (-1,-1), criteria)
        img_points.append(corners)

# 初始化相机内参矩阵和畸变系数
cameraMatrix1 = np.eye(3)  # 左相机的内参矩阵
distCoeffs1 = np.zeros(5)  # 左相机的畸变系数

ret, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(
    obj_points, img_points, frame_size, cameraMatrix1, distCoeffs1
)

# 保存标定结果
np.savez('calibration.npz', 
         ret=ret, rvecs=rvecs, tvecs=tvecs,
         cameraMatrix=cameraMatrix1, distCoeffs=distCoeffs
         )

print("Stereo calibration results saved to 'calibration.npz'")
