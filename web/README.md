# 无尽的拉格朗日 · 星际猎人 —— 数据获取可行性验证 Demo 前端

用 **Vue 3 + TypeScript + Vite** 构建、**iOS 风格 UX** 的 Web Demo，用于展示「采集 → 解析 → 归一化」后的角色数据，验证数据可用性与完整性。

> 本工程只消费共享数据契约 [`/workspace/shared/data-model.md`](../shared/data-model.md) 中定义的标准角色数据模型，不扩展契约之外的字段。

## 环境要求

- Node.js ≥ 20（推荐 24）
- npm ≥ 10（推荐 11）

## 快速开始

```bash
# 1. 安装依赖
npm install

# 2. 本地开发（默认 http://localhost:5173）
npm run dev

# 3. 生产构建（先做 TypeScript 类型检查，再打包到 dist/）
npm run build

# 4. 预览生产构建产物（默认 http://localhost:4173）
npm run preview

# 仅做类型检查
npm run type-check
```

## 数据来源

前端运行时通过 `fetch` 加载 JSON：

- **默认**：`/data/character.json`（即 `public/data/character.json`，由样例数据 `shared/character.sample.json` 复制而来）。
- **自定义**：通过 URL 查询参数 `?data=` 指定任意可访问的 JSON 地址，用于切换到真实采集结果。

```text
# 使用内置样例
http://localhost:5173/

# 指向同源下的另一份采集结果
http://localhost:5173/?data=/data/character.real.json

# 指向任意可访问的地址（需目标服务允许跨域 CORS）
http://localhost:5173/?data=https://example.com/captured/character.json
```

> 说明：路由采用 hash 模式，`?data=` 位于 hash 之前，切换页面不会丢失该参数。

### 降级与空态

- 加载失败（网络错误 / HTTP 非 2xx / JSON 解析失败）会展示错误空态，并提供「重新加载」。
- 契约字段缺失时会做安全降级（缺省值），视图不会崩溃；若 `meta.missingFields` 非空，概览页会显示「部分字段缺失，可手动补录」提示条。

## 页面与功能

- **概览页**（`/`）：iOS Large Title 大标题；顶部角色卡（昵称 / UID / 等级 / 区服 / 联盟 / 战力）；渠道徽标（`meta.channelName`）与采集时间；资源与指挥值卡片（含指挥值占用进度条）；缺失字段提示条；采集信息与数据完整性。
- **蓝图列表页**（`/blueprints`）：搜索框 + 两个 iOS 分段控件（按舰种 / 按稀有度）；Inset Grouped 列表卡片，展示名称 / 别名 / 舰种 / 稀有度徽章 / 加点进度；点击进入详情。
- **蓝图详情页**（`/blueprints/:id`）：子型号、默认站位、等级、加点进度、模块列表（已解锁 / 未解锁）、技能加点列表（每项 `level/max` 进度条）。
- **底部 Tab Bar**：概览 / 蓝图切换，毛玻璃底栏。

## iOS 风格设计系统

- **布局**：Large Title 大标题、Inset Grouped 分组卡片、Segmented Control 分段控件、Tab Bar。
- **视觉**：squircle 连续圆角（卡片 18px 等）、充足留白、系统色板（蓝为主色）、柔和阴影。
- **层次**：毛玻璃 `backdrop-filter: blur()`（Tab Bar / 导航栏 / 渠道徽标）、卡片分层。
- **字体**：`-apple-system, "SF Pro Text", Inter, system-ui, sans-serif`，字重层级清晰。
- **动效**：列表项错峰进入动画、点击缩放反馈、页面平滑转场，使用弹簧/缓动曲线（纯 CSS）。
- **深浅色**：跟随系统 + 手动切换（左下角主题按钮，循环 系统 → 浅色 → 深色），两套配色。
- **响应式**：窄屏为原生 App 全屏体验；桌面端（≥900px）渲染为居中「设备框」。

## 目录结构

```text
web/
├─ index.html
├─ package.json
├─ tsconfig.json
├─ vite.config.ts
├─ public/
│  └─ data/
│     └─ character.json      # 运行时数据源（样例）
└─ src/
   ├─ main.ts                # 应用入口
   ├─ router.ts              # 路由（hash 模式）
   ├─ App.vue                # 骨架：设备框 / 滚动区 / Tab Bar
   ├─ types.ts               # 数据契约类型定义
   ├─ components/            # TabBar / PageShell / SegmentedControl / ProgressBar / ...
   ├─ composables/
   │  ├─ useCharacter.ts     # 数据加载 + 归一化（含 ?data= 支持）
   │  └─ useTheme.ts         # 主题模式（system/light/dark）
   ├─ utils/                 # normalize / format / tone
   ├─ views/                 # OverviewView / BlueprintsView / BlueprintDetailView
   └─ styles/                # theme.css（设计令牌）/ base.css（布局与工具类）
```
