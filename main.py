import threading
import sys
from colorThreshold import point_queue, cameraThread
from Draw import DrawThread

if __name__ == "__main__":
    camera_thread = threading.Thread(target=cameraThread)
    camera_thread.daemon = True  # 设置为守护线程
    camera_thread.start()

    draw_thread = threading.Thread(target=DrawThread)
    draw_thread.daemon = True
    draw_thread.start()
    
    # 保持主进程运行
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("程序中断")
        sys.exit(0)
    
    # 等待图像处理线程结束
    camera_thread.join()
    draw_thread.join()