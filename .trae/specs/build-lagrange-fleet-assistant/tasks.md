# Tasks

> 状态说明：`[x]` 为已完成；沙箱无游戏账号/手机/游戏网络，凡涉及**真机抓包**的步骤已交付工具与手册，但实际执行需用户在本地完成，标注为「待用户本地执行」。

- [x] Task 1: 采集环境搭建与技术探针
  - [x] SubTask 1.1: 交付 `mitmproxy_addon.py`（只读落盘）+ PC 代理运行手册（含 CA 证书、脱敏、全量/筛选两种模式）
  - [x] SubTask 1.2: 交付 Android 模拟器抓包方案与步骤（写入 `capture/README.md`）
  - [x] SubTask 1.3: 官服/B服 鉴权差异在 `channels.yaml` 中建模为待确认项
  - [ ] SubTask 1.4（待用户本地执行）: 在本地真实搭建代理/模拟器环境并安装信任证书

- [x] Task 2: 协议定位与角色数据解析
  - [x] SubTask 2.1: 交付 `scan.py`，支持按 host+path 聚合、关键字过滤、JSON 顶层字段探测、疑似角色数据启发式标注
  - [x] SubTask 2.2: `mitmproxy_addon.py` 处理 gzip/deflate 解压、二进制分流；不可解析项记录机制已就位
  - [x] SubTask 2.3: 交付 `parse.py` 归一化，输出符合共享契约的标准模型，`--validate` 校验通过
  - [ ] SubTask 2.4（待用户本地执行）: 用真实抓包数据定位接口并回填 `mapping.yaml`

- [x] Task 3: 双渠道验证
  - [x] SubTask 3.1: 官服渠道适配（`channels.yaml` official，显示名「官服」）
  - [x] SubTask 3.2: B服渠道适配（`channels.yaml` bili，显示名「B服」）
  - [ ] SubTask 3.3（待用户本地执行）: 官服、B服 分别真机抓包并记录鉴权与字段差异

- [x] Task 4: Demo 前端（iOS 风格）
  - [x] SubTask 4.1: 搭建 Vue3 + TS + Vite 工程，建立 iOS 风格设计系统（色板 / 字体 / 圆角 / 毛玻璃 / 动效 / 深浅色）
  - [x] SubTask 4.2: 实现角色概览、蓝图列表、蓝图详情界面（含搜索/筛选/模块/加点进度），支持深浅色
  - [x] SubTask 4.3: 接入解析结果（`/data/character.json`，支持 `?data=`），并处理缺失字段降级与空态

- [x] Task 5: 验证结论与最终架构建议
  - [x] SubTask 5.1: 汇总沙箱已验证项、待真机验证项与风险（见 `docs/spike-report.md`）
  - [x] SubTask 5.2: 产出最终架构建议（客户端形态 / 计算引擎选型 / 采集通道主辅策略，初步）

# Task Dependencies
- Task 2 依赖 Task 1
- Task 3 依赖 Task 2
- Task 4 依赖 Task 2（有样例数据后即可并行开发界面）
- Task 5 依赖 Task 3、Task 4
- 可并行：Task 1 完成后，Task 4.1 设计系统搭建可与 Task 2/3 并行

# 待用户本地执行（沙箱环境限制，无法在此完成）
- 本地搭建代理/模拟器抓包环境并信任 CA 证书
- 官服、B服 分别真机抓包，定位接口并回填 `channels.yaml` / `mapping.yaml`
- 用 `parse.py` 产出真实 `character.json` 并在 Demo 前端查看
- 回填验证结论（可行性/稳定性/字段覆盖/渠道差异）至 `docs/spike-report.md` 第四节
