# DRIDE: Drone Relative Identification of Distance using Embedded Light Sources (IAVI 2024 Fall)

## 1. 引言

本实验旨在利用计算机视觉技术估算夜间飞行器的高度和相对位置。通过拍摄飞行器的图像，结合已知技术参数（如导航灯之间的距离），我们可以运用几何推导方法来确定飞行器相对于相机的距离及其高度信息。实验主要包含图像处理、特征检测、几何推导以及实时数据处理等步骤，以提高在夜间条件下识别飞行器光源的准确性。

## 2. 实验背景与意义

在 `lecture4.depth` 中，我们已经了解了很多测算深度 / 距离的方式，例如 ToF (direct)、ToF (cw) 和 Stereo Depth Estimation。近年来，夜间目标检测在多个领域均有应用，例如航空航天、自动驾驶及无人机的导航系统。本项目参考已有的夜间目标检测研究成果，旨在通过实验验证能否利用飞行器的已知特征进行距离估算，以提升夜间飞行器定位精度。

<div align="center">
    <img src='assets/image.png' width="30%">
    <img src='assets/image-1.png' width="40%">
</div>

## 3. 实验步骤

项目的 pipeline 如下：

<div align="center">
    <img src='assets/image-2.png' width="70%">
</div>

实验重点：
- `solvePnP` 算法在该任务上的适配
- 抗城市光源干扰及干扰后修正

### 3.1 设备与环境

<div align="center">
    <img src='assets/image-3.png' width="50%">
    <img src='assets/image-4.png' width="30%">
</div>

- 相机：Basler 工业相机（进行标定以减少图像失真）
- 标定工具：棋盘格标定板
- 飞行器：DJI 无人机 mini2se，附带红色、蓝色和白色导航灯
- 环境：室内环境与室外环境

### 3.2 图像采集与预处理

首先要进行相机标定，获取相机的内参，包括焦距、畸变系数等。光源检测分为以下几步：

1. **预处理**：对每一帧的图像进行去噪。
2. **颜色空间转换**：将图像转换到 HSV 空间，用于提取符合颜色阈值的区域。我们主要限制 H 和 V，通过划定颜色的范围上下限来判断最好的检测效果。其中红色的色温跨越了 0 点，导致需要多个范围限制。我们最终通过参数调整，在室内环境下最大化了光源检测的准确度。
3. **形态学操作滤波**：采用 HSV 编码蒙版辅助颜色识别，特别是亮度限制来辅助灯光的检测。对蒙版处理后的所有轮廓按轮廓大小进行筛选和滤波。
4. **轮廓检测**：识别出符合条件的区域并计算中心点和边界框。最终，对于红色和蓝色光源取出最大的轮廓进行识别，而对于白色光源则使用特定的识别方案。

<div align="center">
    <img src='assets/image-5.png' width="70%">
</div>

我们最终实现了在光照环境、非光照环境以及干扰环境下的稳定光源锁定。在黑暗环境中效果尤其明显。

### 3.3 距离与位置计算

<div align="center">
    <img src='assets/image-6.png' width="70%">
</div>

**几何推导与求解**：利用 `SolvePnP` 算法，根据灯光建立无人机模型。计算飞行器导航灯的像素距离及相机与飞行器的相对位置，结合相机的俯仰角进一步估算飞行器的具体位置。

<div align="center">
    <img src='assets/image-7.png' width="30%">
</div>
`solvePnP` 至少需要 4 个特征点，提供 $4*2=8$ 个方程方可唯一确定相对位姿。而我们有的是红、蓝、白 3 种颜色的灯，因此需要通过对角放置来唯一识别两个同颜色的灯。我们可以通过判断向量 $ v $ 分别与 $ u_1 $、$ u_2 $ 的叉乘结果是否大于 0 来确定两个白灯的身份。

### 3.4 抗干扰

#### 3.4.1 帧修正

考虑每一帧之间无人机的移动距离不会过大，利用这个原理设置前后两帧的光源点位置不能偏差过大（< error），否则用上一帧数据替代。这样可以在大多数情况下保证准确性，避免二维点位置突然变化导致最终距离剧烈波动。第一帧要求绝对准确。在相机帧率低时会出现两帧光源位置相差过大的问题，导致光源卡死在最后的位置。

#### 3.4.2 利用 Tracking

我们还使用了 OpenCV 的 `trackingAPI`。在第一帧选择蓝框进行框选，使用 `MILTracking` 算法限制无人机位置，要求光源点必须在蓝框中。对于慢速的无人机，位置识别和抗干扰能力较强，但在无人机快速移动时效果较差，蓝框容易脱离目标。

## 4. 实地测量数据分析与结果

<div align="center">
    <img src='assets/image-8.png' width="30%">
</div>
室外无人机实验是该项目的核心部分。相较于室内无干扰环境，室外环境更宽广、复杂且接近真实。我们以 DJI Fly 的位置数据作为参考，结合实验数据进行误差分析。

![alt text](assets/image-10.png)

### 4.1 线性处理

<div align="center">
    <img src='assets/image-11.png' width="50%">
    <img src='assets/image-12.png' width="40%">
</div>

通过对比测量距离与无人机自带的测距数据，发现测量距离与大疆无人机的输出距离在测量范围内大致呈线性关系。

### 4.2 误差分析

经过反复实验，发现大疆无人机测距系统在每次运行时存在稳定的 30-40cm 误差。通过计算均值差来得出稳态误差，分析不同距离下的误差变化。

<div align="center">
    <img src='assets/image-13.png' width="40%">
    <img src='assets/image-14.png' width="40%">
</div>

总体来看，当飞行器距离摄像头过小或过大时，测量误差较大。在无干扰和有干扰环境下测试的误差对比显示，无干扰条件下误差较低。

### 4.3 优化方案

- **跟踪与抗干扰**：采用 `MILTracking` 算法，通过在前后帧中保持光源点的相对位置稳定来提升抗干扰能力。
- **距离识别精度提升**：通过提高相机标定精度，或使用双目相机获取深度信息来进一步优化距离识别的精度。

## 5. 结论与启示

本实验成功验证了利用无人机导航灯估算夜间距离的可行性，具有一定的工程应用价值。实验提高了相机对夜间飞行器的识别精度，但在环境光干扰和无人机高速运动情况下，识别精度仍有待进一步优化。未来工作可以探索多光源几何限制，或采用更加精准的图像增强算法，以提升目标识别的稳定性。

## 6. 参考文献

i. Han, X., et al. "Low-Illumination Road Image Enhancement by Fusing Retinex Theory and Histogram Equalization," Electronics, 2023.

ii. Shi, Y., et al. "Nighttime Low Illumination Image Enhancement with Single Image Using Bright/Dark Channel Prior," EURASIP Journal on Image and Video Processing, 2018.

iii. Grest, D., et al. "A Comparison of Iterative 2D-3D Pose Estimation Methods for Real-Time Applications," Computer Vision Journal, 2010.

iv. Lepetit, V., et al. "EPnP: An Accurate O(n) Solution to the PnP Problem," IJCV, 2009.

