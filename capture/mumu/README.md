# MuMu 模拟器抓包专项指南（Windows）

> 前置：你在 PC 上已用 MuMu 启动《无尽的拉格朗日-星际猎人》。
> 目标：把游戏的角色数据流量导入本仓库的采集工具（`capture/mitmproxy_addon.py`）。
> 说明：以下步骤需在**你自己的 Windows** 上执行；地址/端口请按你的实际环境替换。
> 全链路**只读观察**，不改包、不重放、不代打。

---

## 0. 先启动抓包

双击 `capture/mumu/start_capture.bat`，或在 `capture` 目录执行：

```bat
mitmdump -s mitmproxy_addon.py --listen-host 0.0.0.0 --listen-port 8080
```

窗口里会打印你**本机 IPv4**（形如 `192.168.x.x`）——记下来，下面要用。抓包数据写入 `capture/dump/`。

---

## 1. 把 MuMu 的流量指向本机 mitmproxy

### 方式 A：模拟器内手动代理（先试这个）
MuMu 12：模拟器内 `设置 → WLAN → 长按已连接网络 → 修改网络 → 高级 → 手动代理`：

- 主机名 = 上面记的**本机 IPv4**
- 端口 = `8080`

或用 adb（先连上，见第 2 节）：

```bat
adb shell settings put global http_proxy 192.168.x.x:8080
```

> ⚠️ **很多手游会绕过系统 HTTP 代理**（自建 socket / OkHttp 不读系统代理）。
> 如果第 3 节里 `dump/` 只有网页流量、没有游戏请求，改用**方式 B 透明模式**。

### 方式 B：透明模式（推荐，MuMu 默认已 root）
1. 以透明模式启动 mitmproxy：

   ```bat
   mitmdump --mode transparent -s mitmproxy_addon.py -p 8080
   ```

2. 在模拟器内重定向 80/443 到本机 mitmproxy（root 权限）：

   ```bat
   adb shell su -c "iptables -t nat -A OUTPUT -p tcp --dport 80  -j DNAT --to-destination 192.168.x.x:8080"
   adb shell su -c "iptables -t nat -A OUTPUT -p tcp --dport 443 -j DNAT --to-destination 192.168.x.x:8080"
   ```

   抓完清除规则：

   ```bat
   adb shell su -c "iptables -t nat -D OUTPUT -p tcp --dport 80  -j DNAT --to-destination 192.168.x.x:8080"
   adb shell su -c "iptables -t nat -D OUTPUT -p tcp --dport 443 -j DNAT --to-destination 192.168.x.x:8080"
   ```

> 注意：透明模式对 **UDP/KCP 类协议无效**（游戏可能部分走 UDP，那部分抓不到，属正常）。
> 模拟器与宿主机的可达地址/nat 规则因 MuMu 版本而异，若不通请按你的环境微调。

---

## 2. 连接 MuMu 的 adb

MuMu 自带 `adb.exe`（在其安装目录，如 `...\MuMuPlayer-12.0\shell\adb.exe`），
ADB 端口在 MuMu 的 `设置 → 其他` 中查看（常见 `16384`；旧版为 `7555`）。

```bat
:: 用 MuMu 自带的 adb（路径按你实际安装位置替换）
set ADB="C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe"
%ADB% connect 127.0.0.1:16384
%ADB% devices
%ADB% root
```

---

## 3. 安装 mitmproxy CA 为「系统证书」（Android 7+ 必须）

游戏这类 App 默认只信任**系统 CA**，用户证书通常无效。MuMu 已 root，可装为系统证书：

1. 拿到 CA 文件：运行过 `start_capture.bat` 后，CA 在
   `%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.pem`
2. 算出文件名（`subject_hash_old`）：

   ```bat
   openssl x509 -inform PEM -subject_hash_old -in "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.pem" -noout
   ```

   记下输出的 8 位哈希，例如 `c8750f0d`。
3. 推入系统证书目录（Android 13 及以下）：

   ```bat
   %ADB% push "%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.pem" /sdcard/mitmproxy-ca-cert.pem
   %ADB% shell su -c "mount -o rw,remount /system"
   %ADB% shell su -c "cp /sdcard/mitmproxy-ca-cert.pem /system/etc/security/cacerts/c8750f0d.0"
   %ADB% shell su -c "chmod 644 /system/etc/security/cacerts/c8750f0d.0"
   %ADB% reboot
   ```

   重启后在 设置 → 安全 → 加密与凭据 → 信任的凭据 → 系统 里能看到 mitmproxy 即成功。
4. **Android 14+**：系统证书目录改为 APEX `/apex/com.android.conscrypt/cacerts`，需另行处理。
5. **若目标 App 做了证书固定（SSL Pinning）**：即使装了系统证书也抓不到 —— 此时
   **如实记录该接口不可解析及原因**，不要尝试绕过防护。

---

## 4. 抓取角色数据

1. 保持抓包窗口运行。
2. 打开游戏并**登录账号**（官服、B服各抓一次）。
3. 主动刷新这些界面，尽量触发角色数据请求：
   **角色/我的信息、蓝图/图纸、加点/技能/模块、舰队/编队、仓库/资源**。
4. 关掉再进、切换标签，让同一接口重复请求（便于 `scan.py` 统计）。
5. 回到抓包窗口按 `Ctrl-C` 停止。`capture/dump/` 下会出现 `index.jsonl` 等文件。

---

## 5. 定位接口并产出标准数据

```bat
cd capture
python scan.py .\dump                 :: 总览，★ 标注疑似角色数据接口
python scan.py .\dump --grep role     :: 按关键字筛选
```

拿到接口后回填 `channels.yaml`（域名/路径）与 `mapping.yaml`（字段映射），再：

```bat
python parse.py --input <接口响应.json> --mapping mapping.yaml --channel official --out out\character.json --validate
```

然后把前端指向它：`web/?data=.../out/character.json`。

---

## 6. 如果卡住了

把**一个**包含角色数据的接口响应（JSON 文本）直接贴给我，我来帮你：
分析字段结构 → 写 `mapping.yaml` → 跑 `parse.py` → 接进前端。这是最快的路径。

---

## 7. 风险提示

- 仅用于**个人学习研究**，只读观察，不改包/不重放/不代打。
- 抓包可能**违反游戏用户协议**，存在**封号风险**，由你自行承担。
- `cookie/authorization` 默认脱敏；请勿把 `dump/` 原始材料随意外发。
