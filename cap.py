from pypylon import pylon
from pypylon import genicam
import sys
import cv2
import os
import numpy as np
from datetime import datetime
import time  # 导入 time 模块

# ================================================================================

default_cameraSettings = {
    'r_balance': 1,
    'g_balance': 1,
    'b_balance': 1,
    'gain_db': 0,
    'exposure_time': 20000,
    'PixelFormat': 'RGB8',
    'gamma': 1.0
}

def OpenFirstCamera():
    devices = pylon.TlFactory.GetInstance().EnumerateDevices()
    if len(devices) == 0:
        return None
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(devices[0]))
    camera.Open()
    return camera

def SetCamera(camera, cameraSettings):
    camera.BalanceWhiteAuto.SetValue("Off")
    camera.GainAuto.SetValue("Off")      # 禁用自动增益
    camera.PixelFormat.SetValue(cameraSettings['PixelFormat'])
    camera.UserSetLoad.Execute()
    camera.BalanceWhiteAuto.SetValue("Off")
    camera.BalanceRatioSelector.SetValue = "Red"
    camera.BalanceRatio.SetValue(cameraSettings['r_balance'])
    camera.BalanceRatioSelector.SetValue = "Green"
    camera.BalanceRatio.SetValue(cameraSettings['g_balance'])
    camera.BalanceRatioSelector.SetValue = "Blue"
    camera.BalanceRatio.SetValue(cameraSettings['b_balance'])
    camera.ExposureTime.SetValue(cameraSettings['exposure_time'])
    camera.ExposureAuto.SetValue("Continuous")
    # 设置曝光时间上限
    camera.AutoExposureTimeUpperLimit.SetValue(20000)
    camera.Gain.Value = cameraSettings['gain_db']

def Ycbcr422_to_rgb(ycbcr422):
    height, width, _ = ycbcr422.shape
    y_plane = ycbcr422[:, :, 0]
    cbcr_plane = ycbcr422[:, :, 1]

    cb_plane = np.zeros((height, width), dtype=np.uint8)
    cr_plane = np.zeros((height, width), dtype=np.uint8)

    cb_plane[:, ::2] = cbcr_plane[:, ::2]
    cr_plane[:, ::2] = cbcr_plane[:, 1::2]
    cb_plane[:, 1::2] = cbcr_plane[:, ::2]
    cr_plane[:, 1::2] = cbcr_plane[:, 1::2]

    ycbcr_full = np.dstack((y_plane, cb_plane, cr_plane))
    rgb = cv2.cvtColor(ycbcr_full, cv2.COLOR_YCrCb2RGB)
    return rgb


if __name__ == '__main__':
    time.sleep(0.5)
    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M")
    save_root = os.path.join(os.getcwd(), f"{folder_name}/")
    exitCode = 0
    try:
        Img = pylon.PylonImage()
        camera = OpenFirstCamera()
        if camera is None:
            print("WRONG, no camera connected")
            sys.exit(1)
        SetCamera(camera, default_cameraSettings)

        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        image_count = 0
        last_save_time = time.time()  # 获取当前时间

        while camera.IsGrabbing():
            # SetCamera(camera, default_cameraSettings)
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                img = Ycbcr422_to_rgb(grabResult.Array)
                cv2.imshow('Grabbed Image', cv2.resize(img, None, None, fx=0.2, fy=0.2))

                current_time = time.time()
                if current_time - last_save_time >= 1:  # 检查是否已经过了一秒
                    os.makedirs(save_root, exist_ok=True)
                    filename = f"{save_root}/image_{image_count:04}.png"
                    Img.AttachGrabResultBuffer(grabResult)
                    Img.Save(pylon.ImageFileFormat_Png, filename)
                    image_count += 1
                    last_save_time = current_time  # 更新最后保存的时间
                    print(f"已保存图像: {filename}")

                k = cv2.waitKey(1)
                if k == ord('q') or k == ord('Q'):
                    print(f"保存到 {save_root}")
                    break
            else:
                print("错误: ", grabResult.ErrorCode, grabResult.ErrorDescription)

            grabResult.Release()
    except genicam.GenericException as e:
        print("发生异常.")
        print(e)
        exitCode = 1
    sys.exit(exitCode)
