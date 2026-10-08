# 采集工具链运行手册（数据获取可行性验证 Demo）

本目录是「数据获取可行性验证 Demo」的**采集 / 解析**部分，用于在你**自己的电脑 +
手机/安卓模拟器**上真实抓包，从《无尽的拉格朗日-星际猎人》获取账号角色数据，并
归一化为标准模型（见 [`../shared/data-model.md`](../shared/data-model.md)）。

> **重要：** 仓库沙箱内没有游戏账号、没有手机/模拟器、也访问不到游戏服务器，因此
> 本目录**只包含工程代码与手册**，不含任何真实抓包结果，**也不含任何写死的游戏域名
> 或字段名**。所有域名、路径、字段都必须由你抓包后确认并填入配置。

---

## 0. 文件一览

| 文件 | 用途 |
| --- | --- |
| `requirements.txt` | 依赖：`mitmproxy` + `PyYAML` |
| `channels.yaml` | 渠道配置（官服 / B服 …）：域名、路径匹配关键字，**待抓包确认** |
| `mitmproxy_addon.py` | mitmproxy 落盘 addon，只读观察，产出 `dump/` 与 `index.jsonl` |
| `scan.py` | 扫描 `dump/`，聚合接口、探测 JSON 顶层字段，帮你定位角色数据接口 |
| `mapping.yaml` | 字段映射模板：源字段 → 标准模型，**待抓包确认** |
| `parse.py` | 按映射把响应归一化为标准 `character.json`，并支持结构校验 |
| `out/character.json` | 解析/样例产出的标准数据（Demo 前端消费） |
| `dump/` | 抓包落盘目录（运行时生成） |

**只读声明：** 全链路仅做只读观察，**不修改数据包、不重放、不注入、不代替玩家操作**。

---

## 1. 环境准备

### 1.1 Python 依赖

```bash
cd capture
python3 -m pip install -r requirements.txt
```

- 需要 Python 3.14（本项目按 3.14 验证）。
- `scan.py` / `parse.py` **不依赖 mitmproxy**，即使未安装 mitmproxy 也能 `--help`
  和做语法检查；只有真正抓包才需要 mitmproxy。

### 1.2 安装并确认 mitmproxy

```bash
mitmproxy --version        # 确认安装成功
```

### 1.3 启动抓包（PC 端）

```bash
# 交互界面（推荐：先看清单再决定）
mitmproxy -s mitmproxy_addon.py

# 无界面模式（推荐：长时间抓包，日志少）
mitmdump -s mitmproxy_addon.py
```

默认监听 **`0.0.0.0:8080`**（HTTP 代理端口）。可用 `-p` 改端口，例如 `-p 8888`。

常用可调参数（二选一）：

```bash
# 方式 A：mitmproxy --set 传参
mitmdump -s mitmproxy_addon.py \
  --set capture_dump_dir=./dump \
  --set capture_path_keywords=role,blueprint \
  --set capture_host_keywords= \
  --set capture_redact=true

# 方式 B：环境变量
CAPTURE_DUMP_DIR=./dump \
CAPTURE_PATH_KEYWORDS=role,blueprint \
CAPTURE_CHANNELS=./channels.yaml \
mitmdump -s mitmproxy_addon.py
```

addon 支持的配置项：

| 选项 / 环境变量 | 默认 | 说明 |
| --- | --- | --- |
| `capture_dump_dir` / `CAPTURE_DUMP_DIR` | `dump` | 落盘目录 |
| `capture_channels` / `CAPTURE_CHANNELS` | `./channels.yaml` | 渠道配置路径 |
| `capture_host_keywords` / `CAPTURE_HOST_KEYWORDS` | 空 | 额外 host 关键字（逗号分隔） |
| `capture_path_keywords` / `CAPTURE_PATH_KEYWORDS` | 空 | 额外 path 关键字（逗号分隔） |
| `capture_redact` / `CAPTURE_REDACT` | `true` | 是否脱敏 cookie/authorization 等 |
| `capture_max_text_bytes` / `CAPTURE_MAX_TEXT_BYTES` | `2000000` | 文本响应体最大保存字节 |
| `capture_preview_bytes` / `CAPTURE_PREVIEW_BYTES` | `512` | 二进制响应体预览字节 |
| `capture_save_all_when_empty` / `CAPTURE_SAVE_ALL_WHEN_EMPTY` | `true` | 规则为空时记录全部流量 |

> **建议第一步：** 先**不要**填 `channels.yaml`，让规则留空跑一次「**全量抓包**」，
> addon 会记录所有流量，之后用 `scan.py` 筛选。

---

## 2. 手机 / 模拟器接入

### 2.1 WiFi 代理指向 PC

1. 让手机与 PC 处于**同一局域网**（同一 WiFi）。
2. 查 PC 的内网 IP：
   - macOS/Linux：`ifconfig` 或 `ip addr`
   - Windows：`ipconfig`
3. 手机 WiFi → 修改网络 → 手动代理 → 主机名填 PC 内网 IP，端口填 `8080`。
4. 保持 `mitmproxy`/`mitmdump` 运行。

### 2.2 安装并信任 mitmproxy CA 证书

证书下载地址：手机浏览器访问 **`http://mitm.it`**（走代理时可用），选择对应平台。

**Android：**
- **Android 7.0 及以上**：App 默认只信任**系统 CA**，用户安装的证书对多数 App
  **不生效**（会抓不到 HTTPS / 报证书错误）。方案：
  - 优先使用**安卓模拟器 + root**，把证书安装为**系统证书**（见 2.3）；
  - 或在 App 明确允许用户证书时使用用户证书（设置 → 安全 → 加密与凭据 → 安装证书 → CA 证书）。
  - 若目标 App 做了 **SSL Pinning / 证书固定**，则即便装了系统证书也可能抓不到，
    这属于「反抓包机制」，请**记录该接口不可解析及原因**，不要尝试绕过防护。
- 用户证书与系统证书是**两个位置**，注意区分。

**iOS：**
- 用 Safari 打开 `http://mitm.it` 安装描述文件 → 设置 → 通用 → VPN与设备管理 → 安装；
- 再到 设置 → 通用 → 关于本机 → 证书信任设置 → 打开对 mitmproxy 证书的完全信任。

### 2.3 Android 模拟器方案（推荐，环境可控）

- 推荐 **Android Studio 自带的 AVD 模拟器**（可选用带 Google APIs 的镜像并按需 root），
  或 MuMu / 雷电 / BlueStacks 等（是否可 root、是否可安装系统证书因版本而异）。
- 将模拟器网络代理指向 PC 的 `8080` 端口（模拟器通常有「网络代理设置」，或用
  `adb shell settings put global http_proxy <PC_IP>:8080`）。
- **系统证书方案**：把 mitmproxy 的 CA（`~/.mitmproxy/mitmproxy-ca-cert.cer`）转换后
  以 `<hash>.0` 命名放入 `/system/etc/security/cacerts/`（需 root / 可写系统分区，
  不同模拟器路径与写权限不同）。也可在模拟器内直接安装用户证书，视目标 App 策略而定。
- 模拟器方案的好处：登录、卸载重装、清数据、切账号都很方便，适合反复验证官服/B服差异。

---

## 3. 抓包流程

1. 启动 `mitmdump -s mitmproxy_addon.py`（或 `mitmproxy`）。
2. 手机/模拟器连上代理并信任证书后，**先随便打开一个网页**，确认 PC 端能看到流量。
3. 打开游戏并**登录账号**（官服账号 / B服账号各抓一次，见第 7 节）。
4. 进入并**主动刷新**这些界面，尽量触发角色数据请求：
   - **角色 / 我的信息**（uid、昵称、等级、区服、势力）；
   - **蓝图 / 图纸 / 设计图**（舰船蓝图列表、子型号、稀有度）；
   - **加点 / 技能 / 模块**（加点方案、模块解锁、技能等级）；
   - **舰队 / 编队**（指挥值占用与上限）；
   - **仓库 / 资源**（金属、晶体、重氢等）。
5. 关掉页面再进、或切换标签，同一接口通常会重复请求，便于 `scan.py` 统计。
6. 停止抓包（Ctrl-C）。此时 `dump/` 下应有 `index.jsonl` 及若干 `*.resp.txt` 等文件。

**落盘内容：** 命中的请求/响应会保存为 `<id>.meta.json`（含脱敏后的 headers）、
`<id>.req.bin`（请求体）、`<id>.resp.txt`（文本响应，gzip/br/deflate 已解压）或
`<id>.resp.preview.bin`（二进制只存前若干字节并标注）。`index.jsonl` 每行一条摘要。

---

## 4. 用 `scan.py` 定位承载角色数据的接口

```bash
cd capture

# 1) 总览：按 host+path 聚合，★ 标注疑似角色数据接口
python3 scan.py ./dump

# 2) 只看出现最多的前 20 组
python3 scan.py ./dump --top 20

# 3) 按关键字过滤（匹配 URL/host/path/method/content-type/响应体，大小写不敏感，可多次）
python3 scan.py ./dump --grep role --grep blueprint

# 4) 机器可读输出，便于二次处理
python3 scan.py ./dump --json
```

输出包含：出现次数、平均/最大响应大小、status、content-type、是否 JSON、
JSON 响应**顶层字段名**、示例 URL，并对疑似角色数据接口打 ★。

判断建议：
- 关注 `content-type` 为 `application/json` 且响应体较大、字段名含
  `role/player/blueprint/ship/fleet/currency/...` 的接口；
- 若响应是**数组**，`scan.py` 会展示首元素的字段名；
- 若响应被**加密/签名**（字段是密文或不可读），记录该接口并视作「不可解析」，跳过；
- 命中的接口 host/path 就是下一步要写进 `channels.yaml` 与 `mapping.yaml` 的值。

> 提示：`scan.py` 的「疑似」判断基于启发式关键词（见脚本内 `ROLE_HINTS`），
> **仅作提示**，最终以你人工确认为准。

---

## 5. 回填 `channels.yaml`（渠道匹配规则）

打开 `capture/channels.yaml`，把上一步确认的域名/路径关键字填入对应渠道：

```yaml
channels:
  official:
    displayName: 官服
    hostPatterns: ["<你抓到的官服API域名片段>"]
    pathKeywords: ["<你抓到的角色接口路径片段>"]
    loginNotes: "<记录官服登录域名与 token 形态>"
  bili:
    displayName: B服
    hostPatterns: ["<你抓到的B服API域名片段>"]
    pathKeywords: ["<...>"]
    loginNotes: "<记录B服差异>"
```

匹配规则：host / path 的**子串匹配**（大小写不敏感），任一渠道命中即命中；
命中流量会在 `index.jsonl` 的 `channel` 字段标注归属。全部规则为空时记录全部流量。

---

## 6. 回填 `mapping.yaml` 并产出 `character.json`

### 6.1 填写字段映射

用 `scan.py` 看到某接口的 JSON 顶层字段后，打开 `capture/mapping.yaml`，把**源字段路径**
填到对应**标准模型路径**右侧（路径语法：点路径 `a.b`、下标 `a[0].b`、通配 `a[].b`）：

```yaml
map:
  role.uid: "data.player.id"          # 示例格式，请替换为你抓到的真实路径
  role.nickname: "data.player.name"
  role.level: "data.player.lv"
  currencies.metal: "data.res.metal"
  # ...
blueprints:
  root: "data.blueprints"
  fields:
    id: "id"
    name: "name"
    modules.root: "modules"
    modules.fields.slot: "slot"
    # ...
```

### 6.2 生成标准数据

```bash
# 用抓到的响应 JSON 产出（建议加 --validate 自检）
python3 parse.py --input resp.json --mapping mapping.yaml \
    --channel official --out out/character.json --validate
```

- `--channel official|bili`：读取 `channels.yaml` 的 `displayName`，写入
  `meta.channel` / `meta.channelName`。
- 未配置或找不到的字段**不会导致崩溃**：对应 `meta.completeness` 分组置 `false`，
  键名写入 `meta.missingFields`，缺失项用安全默认值（字符串 `""`、数值 `0`、数组 `[]`）。
- 若暂时没有真实数据，可用样例联调（**原样输出**，`source=sample`）：

```bash
python3 parse.py --from-sample --out out/character.json --validate
# 或指定路径
python3 parse.py --from-sample ../shared/character.sample.json --out out/character.json
```

---

## 7. 官服 vs B服 的差异（需分别抓包确认）

两渠道的**输出结构完全一致**，差异只体现在 `meta.channel` / `meta.channelName`。需要你分别记录：

| 维度 | 官服（`official`） | B服（`bili`） |
| --- | --- | --- |
| 账号体系 | 网易账号（待确认） | 哔哩哔哩账号（待确认） |
| 登录域名 / SDK | **待抓包确认** | **待抓包确认** |
| token 形态（header/字段名） | **待抓包确认** | **待抓包确认** |
| 业务接口域名/路径 | **待抓包确认** | **待抓包确认** |
| 字段命名差异 | **待抓包确认** | **待抓包确认** |

建议做法：用**同一个 `mapping.yaml` 的副本**分别适配两个渠道（若字段名不同），
或先把各自响应字段记录清楚再统一映射。分别执行：

```bash
python3 parse.py --input official_resp.json --mapping mapping.yaml --channel official --out out/character.official.json --validate
python3 parse.py --input bili_resp.json     --mapping mapping.yaml --channel bili     --out out/character.bili.json     --validate
```

---

## 8. 风险与合规提示

- 本工具**仅用于个人学习与研究**，仅做**只读观察**：不改包、不重放、不注入、不代打。
- 抓包/改包可能**违反游戏用户协议**，存在**账号封禁风险**，风险由使用者**自行承担**。
- 请勿抓取、存储、传播他人数据；`cookie/authorization` 等敏感信息默认脱敏，
  请勿将 `dump/` 中的原始材料随意外发。
- 若接口存在**加密/签名/证书固定**等反抓包机制，请**如实记录该接口不可解析及原因**，
  不要尝试绕过防护。
- 本项目不提供、也不包含任何真实游戏域名/字段；一切以你自己抓包确认为准。

---

## 9. 产出物位置

| 产出 | 位置 | 说明 |
| --- | --- | --- |
| 抓包原始材料 | `capture/dump/` | `index.jsonl` + 每条 flow 的 meta/body 文件 |
| 标准角色数据 | `capture/out/character.json` | 交由 Demo 前端消费 |
| 渠道配置 | `capture/channels.yaml` | 抓包后回填 |
| 字段映射 | `capture/mapping.yaml` | 抓包后回填 |

Demo 前端只需读取 `out/character.json`（结构见 `shared/data-model.md`）；
也可以用 `parse.py --from-sample` 的样例数据先联调界面。

---

## 10. 常见问题

- **抓不到 HTTPS / 证书错误**：证书未安装或未信任；Android 7+ 需系统证书；App 可能有
  证书固定（Pinning）→ 记录不可解析，不强行绕过。
- **`scan.py` 没有输出**：确认 `dump/index.jsonl` 存在；未填规则时会记录全部流量，
  若已填规则可能过滤过严，先清空 `channels.yaml` 规则重抓。
- **响应打不开/乱码**：可能是加密或二进制；`index.jsonl` 的 `resp_binary` 为 `true`
  表示二进制（只存了预览）。加密响应请记录为不可解析项。
- **`parse.py` 输出全空**：`mapping.yaml` 未填或路径不对 → `meta.completeness` 全 `false`，
  对照 `meta.missingFields` 逐项补映射。
- **缺少 `PyYAML`**：`pip install -r requirements.txt`。

---

## 11. 沙箱内可自测的验证命令

以下命令**不联网、不访问游戏**，可在任意环境自检工具链是否正常：

```bash
cd capture
python3 -m py_compile mitmproxy_addon.py scan.py parse.py    # 语法检查
python3 scan.py --help                                        # scan 帮助
python3 parse.py --help                                       # parse 帮助
python3 parse.py --from-sample --out out/character.json --validate   # 样例→标准模型→校验
```
