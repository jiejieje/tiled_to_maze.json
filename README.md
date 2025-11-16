# Tiled地图转Maze工具

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

这是一个简单的工具，可以把Tiled地图编辑器做的地图转换成可以使用的Maze格式和空间树结构。

## 这个工具能做什么？

- 把Tiled编辑器导出的地图文件(.json)转换成游戏能用的格式
- 一键生成两种文件：Maze格式和空间树结构
- 转换大地图时不会卡顿
- 有进度条显示，让你知道转换到哪一步了
- 简单易用的界面，点几下鼠标就能完成

## 详细使用教程

****[📘 点击这里查看详细使用说明PDF](使用教程.pdf)****

我们提供了一份详细的PDF使用手册，包含了图文并茂的操作指南。

## 怎么安装和使用

### 需要先安装的东西
- Python 3.6或以上版本 (如果没有，去[Python官网](https://www.python.org/downloads/)下载)
- tkinter (一般Python安装时就自带了)

### 下载方式



 **直接下载ZIP压缩包**
   - 在GitHub页面上点击绿色的"Code"按钮
   - 选择"Download ZIP"
   - 下载完成后解压到任意文件夹


### 运行程序

下载后，你可以这样运行：

1. 双击`tiled_to_maze.py`文件（如果你的系统已将.py文件关联到Python）

2. 或者打开命令提示符/终端，进入程序所在文件夹，然后运行：
   ```bash
   python tiled_to_maze.py
   ```

### 使用方法

1. 打开程序
2. 点"选择文件"按钮，找到你的Tiled地图文件(.json)
3. 选择你想保存结果的文件夹
4. 如果需要，可以修改输出文件的名字
5. 点"一键转换"按钮
6. 等待完成即可！转换过程会在下方显示

更详细的操作指南请查看[使用教程PDF](使用教程.pdf)。

## 支持什么样的地图？

目前只测试了tiled导出的json地图，其他地图软件请谨慎使用。
另外这个项目更新了一个[示例地图](示例地图/tilemap.json)，你可以通过tiled打开编辑地图或者参考里面的数据结构，也可以通过我的脚本直接转换成maze.json验证这个脚本

## 常见问题


**问: 我的地图太大，会不会卡住?**  
答: 不会。程序使用了先进的多线程技术，转换再大的地图界面也不会卡住。

**问: 我不太懂编程，能用这个工具吗?**  
答: 完全可以！这个工具设计得非常简单，只需点击几个按钮就能完成转换。


## 协议说明

本项目采用 Apache 2.0 许可证。这意味着你可以:

- 自由使用、修改和分享这个工具
- 用于商业项目
- 按你的需要修改源代码


## 需要帮助？

如果你有任何问题或建议，可以通过以下方式联系我：

- 在GitHub上提交Issue

---

希望这个小工具能帮你节省时间！

## 我的其他相关开源项目

**[GenerativeAgents: Alien Town 外星小镇](https://github.com/jiejieje/GenerativeAgents-Alien-Town)** 

**[为小镇打造的 LoRA 模型](https://github.com/jiejieje/top-down-flux-lora)** 
