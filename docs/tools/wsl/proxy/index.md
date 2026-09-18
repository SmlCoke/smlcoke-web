# 代理

在**用户根目录**下配置了脚本 `Windows_IP_Proxy_Setup.sh`，用于在 WSL2 中设置 Windows 主机的 IP 代理，以便在 WSL2 内部访问外部网络资源。
```bash
#!/bin/bash
PROXY_PORT=7897
WIN_IP=$(grep nameserver /etc/resolv.conf | awk '{print $2}')
case "$1" in
    on)
        export http_proxy="http://$WIN_IP:$PROXY_PORT"
        export https_proxy="http://$WIN_IP:$PROXY_PORT"
        export all_proxy="socks5://$WIN_IP:$PROXY_PORT"
        echo " Info: Proxy enabled: $WIN_IP:$PROXY_PORT"
        curl -I -m 5 https://www.google.com 2>/dev/null | head -n 1
        ;;
    off)
        unset http_proxy https_proxy all_proxy
        echo "Warning: Proxy disabled"
        ;;
    *)
        echo "Usage: $0 {on|off}"
        ;;
esac
```

其中 `PROXY_PORT` 是 Windows 主机上代理服务的端口号，可以在 `Clash` 设置界面查看与修改。
`https://www.google.com` 是一个测试 URL，用于验证代理是否生效。可以根据需要替换为其他 URL。

脚本 `Windows_IP_Proxy_Setup.sh` 在任何用户下都能够直接使用：
```bash
Windows_IP_Proxy_Setup.sh on # 开启代理
Windows_IP_Proxy_Setup.sh off # 关闭代理
```
因为脚本`Windows_IP_Proxy_Setup.sh`被放到了系统级目录 `usr/local/bin`