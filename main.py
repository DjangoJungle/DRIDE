import threading
import sys
from colorThreshold import image_thread, point_queue
from Draw import ani, fig

if __name__ == "__main__":
    # 启动图像处理线程
    image_thread.start()
    
    # 启动绘图线程
    # plotting_thread = threading.Thread(target=plt.show)
    # plotting_thread.daemon = True  # 设置为守护线程
    # plotting_thread.start()
    
    # 保持主进程运行
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("程序中断")
        sys.exit(0)
    
    # 等待图像处理线程结束
    image_thread.join()
    # plotting_thread.join()