import queue
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from colorThreshold import point_queue, cameraThread

# 初始化函数
def init():
    global ax
    ax.set_xlim3d([-20, 200])
    ax.set_ylim3d([-20, 200])
    ax.set_zlim3d([-20, 200])

    # 设置轴标签
    ax.set_xlabel('X Axis')
    ax.set_ylabel('Y Axis')
    ax.set_zlabel('Z Axis')
    
    return []

# 更新函数，每一帧都会调用
def update(frame):
    global data, ax
    # 从队列中获取所有可用的点
    while not point_queue.empty():
        new_point = point_queue.get_nowait()
        data.append(new_point)
    
    # 清除之前的绘图
    ax.clear()
    
    # 重新设置坐标轴范围
    ax.set_xlim3d([-20, 100])
    ax.set_ylim3d([-20, 100])
    ax.set_zlim3d([-20, 1000])
    
    # 绘制数据点
    if data:
        x, y, z = zip(*data)
        line, = ax.plot(x, y, z, color='b', marker='o')
        return [line]
    else:
        return []

camera_thread = threading.Thread(target=cameraThread)
camera_thread.daemon = True  # 设置为守护线程
camera_thread.start()

data = []

# 设置图形界面
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 创建动画对象
ani = FuncAnimation(fig, update, frames=np.arange(0, 100), init_func=init, blit=True)

plt.show()

# 等待图像处理线程结束
camera_thread.join()