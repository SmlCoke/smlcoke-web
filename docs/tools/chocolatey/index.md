# Chocolatey: Package Manager for Windows

> update: 2026-07-10

## I. Chocolatey 介绍

## II. Chocolatey 安装流程

### 2.1 检查是否已经安装了 choco

```powershell
Get-Command choco -ErrorAction SilentlyContinue
```

如果没有任何输出，说明尚未安装，可以继续。

### 2.2 安装 choco

在 powershell 管理员模式中，执行：

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

默认安装位置通常为：

```text
C:\ProgramData\chocolatey
```

安装完成后，一般会输出：

```powershell
You can call choco from anywhere, command line or PowerShell by typing choco. 
Run choco /? for a list of functions. 
You may need to shut down and restart PowerShell and/or consoles first prior to using choco. Ensuring Chocolatey commands are on the path 
Ensuring chocolatey.nupkg is in the lib folder
```

可以重启 powershell 并且输入 `choco --version` 验证是否安装成功。正常情况下会输出版本号，例如 `2.x.x`。也可以通过 `where choco` 来查看实际路径。

## III. 利用 Chocolatey 工具安装其他工具

### 3.1 make

> update date: 2026-07-10

打开 powershell 管理员模式，然后：

```powershell
choco install make -y
```

安装成功时会输出：

```powershell
The install of make was successful.
Deployed to 'C:\ProgramData\chocolatey\lib\make'
```

安装目录一般在 `choco` 的 `lib` 文件夹下，例如：

```text
C:\ProgramData\chocolatey\lib\make
```

之后刷新一下环境变量并且检验 make 是否安装成功：

```powershell
refreshenv
make --version
where make
```

输出：

```powershell
PS C:\WINDOWS\system32> refreshenv
Refreshing environment variables from the registry for powershell.exe. Please wait...
Finished
PS C:\WINDOWS\system32> make --version
GNU Make 4.4.1
Built for Windows32
Copyright (C) 1988-2023 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
PS C:\WINDOWS\system32> where.exe make
C:\ProgramData\chocolatey\bin\make.exe
```