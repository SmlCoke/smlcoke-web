# Conda

## Windows11 Anaconda 配置

Andaconda 路径：`D:\Anaconda`
为了保持整机 Python 环境干净，**所有与 Andaconda 相关的环境变量均未添加进入系统环境变量 Path 中**。Anaconda 的使用仅限于在 Anaconda Prompt 中，或者在其他命令行工具中激活了 Anaconda 环境后使用。
VS Code 中，通过在 `settings.json` 中添加以下配置，将 Anaconda Prompt 集成进入 VS Code 终端中：
```json
"terminal.integrated.profiles.windows": {
    "Anaconda Prompt": {
        "path": "C:\\Windows\\System32\\cmd.exe",
        "args": ["/K", "D:\\Anaconda\\Scripts\\activate.bat"]
    },
}
```

## Conda 常用命令
创建虚拟环境: `conda create -n <env_name> python=xx.xx.xx -y`
查看所有环境: `conda info -e`
激活环境: `conda activate <env_name>`
激活环境后，在当前环境中安装包：`conda install <package_name>` 或者 `pip install <package_name>`
直接在指定环境中安装包：`conda install -n <env_name> <package_name>`
查看当前环境的所有包：`conda list`
退出当前环境: `conda deactivate`
删除指定环境: `conda remove -n <env_name> --all -y`（谨慎）
删除当前环境的包：`conda remove <package_name>`
删除指定环境的包：`conda remove -n <env_name> <package_name>`
更新当前conda版本：`conda update conda -y`
更新包版本：`conda update <package_name> -y`
更新所有包：`conda update --all` 或 `conda upgrade --all`
克隆环境：`conda create --name <new_env_name> --clone <old_env_name>`
查找可供安装的包版本/精确查找：`conda search --exact <package_name>`
查找可供安装的包版本/模糊查找：`conda search <package_name>`
