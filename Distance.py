import cv2
import numpy as np

# 读取相机内参矩阵和畸变系数
with np.load('calibration.npz') as X:
    cameraMatrix, distCoeffs = [X[i] for i in ('cameraMatrix', 'distCoeffs')]



points_3d = np.array([
    [0, 0, 0],
    [100, 0, 0],
    [0, 100, 0],
    [100, 100, 0],
], dtype=np.float32)
# 使用 solvePnP 求解相机的外部参数
def solveDistance(points_2d, img):
    # 利用points_2d推出points_3d
    points_3d = []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, rvec, tvec = cv2.solvePnP(points_3d, points_2d, cameraMatrix, distCoeffs)
    if ret:
        # 将旋转向量转换为旋转矩阵
        R, _ = cv2.Rodrigues(rvec)
        
        # 计算相机和物品之间的距离
        distance = np.linalg.norm(tvec)
        print(f"Distance from camera to the object: {distance:.2f} mm")
        tx, ty, tz = tvec.flatten() 

        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"Distance: {distance:.2f} cm"
        org = (50, 50)  # 文字位置
        font_scale = 1
        color = (0, 255, 0)  # 绿色
        thickness = 2
        cv2.putText(img, text, org, font, font_scale, color, thickness, cv2.LINE_AA)
    else:
        print("solvePnP failed.")
    
    return img
