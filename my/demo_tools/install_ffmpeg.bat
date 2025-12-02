```batch
@echo off
echo ========================================
echo FFmpeg 安装助手
echo ========================================
echo.

REM 检查是否已安装
```
if %ERRORLEVEL% EQU 0 (
    echo [OK] FFmpeg 已经安装！
    ffmpeg -version | findstr "ffmpeg version"
    pause
    exit /b 0
)

echo [提示] FFmpeg 未安装，准备下载...
echo.
echo 请选择安装方式：
echo 1. 使用 Chocolatey 自动安装（推荐）
echo 2. 手动下载安装
echo 3. 退出
echo.
set /p choice=请输入选项 (1/2/3):

if "%choice%"=="1" goto chocolatey
if "%choice%"=="2" goto manual
if "%choice%"=="3" exit /b 0

:chocolatey
echo.
echo [步骤1] 检查 Chocolatey...
where choco >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [提示] 未检测到 Chocolatey，正在安装...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

    if %ERRORLEVEL% NEQ 0 (
        echo [错误] Chocolatey 安装失败，请尝试手动安装方式
        pause
        exit /b 1
    )

    REM 刷新环境变量
    call refreshenv
)

echo [步骤2] 使用 Chocolatey 安装 FFmpeg...
choco install ffmpeg -y

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] FFmpeg 安装完成！
    echo [提示] 请关闭并重新打开命令行窗口使其生效
) else (
    echo [错误] 安装失败，请尝试手动安装方式
)
pause
exit /b 0

:manual
echo.
echo ========================================
echo 手动安装步骤：
echo ========================================
echo.
echo 1. 访问：https://github.com/BtbN/FFmpeg-Builds/releases
echo 2. 下载：ffmpeg-master-latest-win64-gpl.zip
echo 3. 解压到：C:\ffmpeg
echo 4. 运行本脚本的"方法三：添加环境变量"部分
echo.
echo 是否现在打开下载页面？(Y/N)
set /p open=
if /i "%open%"=="Y" (
    start https://github.com/BtbN/FFmpeg-Builds/releases
)
pause
exit /b 0
```

## 方法二：手动配置环境变量

### 图形界面方式（推荐）

1. **打开环境变量设置**：
   - 右键点击"此电脑" → 属性
   - 点击"高级系统设置"
   - 点击"环境变量"按钮

2. **编辑 Path 变量**：
   - 在"系统变量"区域找到 `Path`
   - 点击"编辑"
   - 点击"新建"
   - 输入：`C:\ffmpeg\bin`（假设你解压到了C:\ffmpeg）
   - 点击"确定"保存

3. **验证安装**：
   - 打开新的命令行窗口（必须是新窗口！）
   - 运行：`ffmpeg -version`
   - 如果显示版本信息，说明安装成功

### 命令行方式（快速）

以管理员身份打开PowerShell，运行：

```powershell
# 假设你解压到了 C:\ffmpeg
$ffmpegPath = "C:\ffmpeg\bin"

# 添加到系统 Path
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "Machine") + ";$ffmpegPath",
    "Machine"
)

Write-Host "已添加到系统 Path，请重新打开命令行窗口使其生效"
```

## 方法三：验证安装

运行以下命令检查：

```bash
# 检查是否安装成功
ffmpeg -version

# 应该看到类似输出：
# ffmpeg version N-109234-g7815a49f1b Copyright (c) 2000-2023 the FFmpeg developers
# ...
```

## 常见问题

### Q1: 运行 ffmpeg 提示"不是内部或外部命令"

**解决方案**：
1. 确认环境变量是否添加正确
2. **重启命令行窗口**（环境变量修改后需要重启）
3. 如果还不行，重启电脑

### Q2: 下载速度太慢

**解决方案**：
使用国内镜像或代理，或者使用以下备用下载链接：
- https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

### Q3: 不想配置环境变量

**临时方案**：
1. 将 `ffmpeg.exe` 直接复制到你的项目文件夹
2. 或者在Python脚本中指定完整路径：
```python
import matplotlib.animation as animation
Writer = animation.writers['ffmpeg']
writer = Writer(
    fps=2,
    metadata=dict(artist='Property Rights Simulation'),
    bitrate=1800,
    extra_args=['-vcodec', 'libx264'],
    # 指定 ffmpeg 路径
    # executable='C:/ffmpeg/bin/ffmpeg.exe'
)
```