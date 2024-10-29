import queue
import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# 导入摄像头处理脚本中的队列
from colorThreshold import point_queue

# 数据列表用于存储点
data = []

# 设置图形界面
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 初始化函数
def init():
    ax.set_xlim3d([-1000, 1000])
    ax.set_ylim3d([-1000, 1000])
    ax.set_zlim3d([-1000, 1000])
    return []

# 更新函数，每一帧都会调用
def update(frame):
    global data
    # 从队列中获取所有可用的点
    while not point_queue.empty():
        new_point = point_queue.get_nowait()
        data.append(new_point)
    
    # 清除之前的绘图
    ax.clear()
    
    # 重新设置坐标轴范围
    ax.set_xlim3d([-1000, 1000])
    ax.set_ylim3d([-1000, 1000])
    ax.set_zlim3d([-1000, 1000])
    
    # 绘制数据点
    if data:
        x, y, z = zip(*data)
        line, = ax.plot(x, y, z, color='b', marker='o')
        return [line]
    else:
        return []

# 创建动画对象
ani = FuncAnimation(fig, update, frames=np.arange(0, 100), init_func=init, blit=True)

# 显示图像
plt.show()