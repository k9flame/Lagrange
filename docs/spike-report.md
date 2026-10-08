# 数据获取可行性验证 · Spike 报告

> 阶段：`build-lagrange-fleet-assistant` 第一期（数据获取可行性 Demo）
> 日期：2026-10-08
> 说明：本报告分为两部分——① 已在沙箱内完成的工程交付与验证；② 必须由用户在**本地真实环境（手机/模拟器 + 游戏账号）**执行的真机验证。**沙箱内无法真实抓包，因此真机数据结论待用户回填。**

---

## 一、结论摘要

| 维度 | 结论 |
| --- | --- |
| 工程侧 | 采集工具链、协议解析器、双渠道配置、iOS 风格 Demo 前端、共享数据契约均已交付并通过验证 |
| 真机侧 | **待用户本地验证**（沙箱无账号/设备/游戏网络） |
| 架构建议 | 已给出初步建议（见第五节），最终选型待真机验证结果确认 |

---

## 二、已交付的工程产物

```
/workspace/
├─ shared/
│  ├─ data-model.md              # 标准角色数据模型（共享契约）
│  └─ character.sample.json      # 样例数据
├─ capture/                      # 采集 + 解析
│  ├─ mitmproxy_addon.py         # mitmproxy 只读落盘 addon
│  ├─ scan.py                    # 抓包扫描 / 接口定位
│  ├─ parse.py                   # 归一化 + 结构校验
│  ├─ channels.yaml              # 官服 / B服 渠道配置（域名/路径待抓包确认）
│  ├─ mapping.yaml               # 字段映射模板（待抓包确认）
│  ├─ requirements.txt
│  ├─ README.md                  # 中文运行手册（证书/模拟器/双渠道/合规）
│  └─ out/character.json         # 由样例产出的标准数据
└─ web/                          # iOS 风格 Demo 前端（Vue3 + TS + Vite）
   ├─ public/data/character.json # 运行时数据源
   └─ src/                       # 设计令牌 / 组件 / 三个视图
```

---

## 三、沙箱内已验证项（已通过）

- `mitmproxy_addon.py` / `scan.py` / `parse.py` 全部 `py_compile` 通过，`--help` 可用。
- `parse.py` 样例模式产出符合共享契约的 `character.json`，`--validate` **校验通过**。
- 空 mapping 解析不崩溃：`completeness` 置 false、`missingFields` 正确填充、数组字段降级为空。
- 渠道解析正确：`--channel bili` → 显示名「B服」，`--channel official` → 「官服」。
- 敏感头（Cookie/Authorization）在落盘时已脱敏为 `<redacted>`；文本/二进制体分流正确。
- Demo 前端 `npm install`、`npm run build`（含 `vue-tsc` 类型检查）**0 错误**；`npm run dev` 启动后 `/` 与 `/data/character.json` 均返回 200。
- 设计系统抽查：系统色板、squircle 圆角（卡片 18px / hero 28px）、毛玻璃、弹簧曲线、SF 字体栈、深浅色双套令牌均已落地。

> 注：沙箱为 root 环境，Chrome 无法启动，故前端**未做像素级截图复核**；已通过构建与源码抽查确认实现。

---

## 四、待用户本地验证项（真机抓包）

按 `capture/README.md` 执行，核心步骤：

1. 本机安装依赖并运行 `mitmdump -s mitmproxy_addon.py`（先**全量抓包**，规则留空）。
2. 手机/模拟器 WiFi 代理指向 PC，安装并**信任 mitmproxy CA 证书**（Android 7+ 需系统证书；若遇 SSL Pinning 则记录为不可解析）。
3. 登录游戏（**官服、B服 分别执行**），进入/刷新 **角色、蓝图、加点、模块、舰队、仓库** 界面触发请求。
4. `python3 scan.py --grep <关键字>` 定位承载角色数据的接口。
5. 回填 `channels.yaml`（域名/路径关键字）与 `mapping.yaml`（字段映射）——**真实值以抓包为准**。
6. `python3 parse.py --input <响应.json> --mapping mapping.yaml --channel official --validate --out character.json`。
7. 用 `web/?data=character.json` 在 Demo 前端查看真机数据。

**需回填的结论字段**：可行性(是/否)、协议稳定性、字段覆盖矩阵（角色/蓝图/加点/模块/指挥值）、官服与 B服 的鉴权与字段差异、是否存在加密/签名/SSL Pinning。

---

## 五、最终架构建议（初步，待真机确认）

### 5.1 采集通道策略
- **建议以「Android 模拟器同机抓包」为主方案，PC 代理为备选**。理由：模拟器与采集器同机，环境可控、可复现、便于自动化；PC 代理需手机配合、受 WiFi/证书限制更多。
- **官方授权通道**：本次未能确认是否存在可用的官方角色数据授权；若存在，则升级为主通道（合规、稳定），抓包降级为辅。**此项为下一步调研重点**。
- 采集层已按 `channels.yaml`（渠道）× 落盘格式（采集方式）解耦，切换/新增渠道或采集方式不影响解析与前端。

### 5.2 客户端形态
- 本期 Demo 用 **Web 前端（Vue3+TS）** 验证，验证结果良好且可复用。
- **初步建议最终形态：PC 桌面端（Tauri + 复用本套 Web UI）为主**。理由：抓包/重计算/大屏可视化都在 PC 更顺；UI 层可直接复用，迁移成本低。
- 若用户强需求手机端，则建议在此基础上用同一套 Web 资产做移动端壳（Capacitor/uni-app），但抓包仍在 PC/模拟器侧完成。

### 5.3 计算引擎
- 战斗模拟与配舰优化属计算密集型，**建议 Python（numpy/scipy）实现核心算法，作为本地 sidecar**；后续若性能不足，再将热点下沉到 Rust。本期未涉及，仅作方向。

---

## 六、风险与合规

- **协议稳定性**：移动端接口可能随版本变动、存在加密/签名/SSL Pinning，抓包方案具有脆弱性；需在真机验证后评估维护成本。
- **账号安全**：抓包需信任第三方 CA，存在**封号与隐私风险**，必须由用户自行评估并承担。
- **合规**：工具**全程只读**——只观察流量，不改包、不重放、不代替玩家操作，仅用于个人学习研究。

---

## 七、下一步（待用户回填真机结果后）

1. 依据真机结论确认采集通道与客户端形态，冻结架构。
2. 立项第二阶段：蓝图知识库 → 单舰数值计算 → 舰队战斗模拟 → 配舰优化器。
