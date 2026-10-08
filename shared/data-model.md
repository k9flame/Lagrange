# 标准角色数据模型（采集/解析 ↔ 前端的共享契约）

所有采集通道与解析器最终都必须归一化为本模型；Demo 前端只消费本模型。
样例见 [character.sample.json](./character.sample.json)。

```ts
interface CharacterData {
  meta: {
    channel: "official" | "bili" | string;  // 渠道标识
    channelName: string;                    // 渠道显示名，如 "官服" / "B服"
    source: "mitmproxy" | "emulator" | "sample" | "manual";
    capturedAt: string;                     // ISO8601
    protocolNote?: string;
    completeness: Record<string, boolean>;  // 各模块是否采集到
    missingFields: string[];                // 缺失字段键
  };
  role: {
    uid: string;
    nickname: string;
    level: number;
    serverName: string;
    unionName?: string;
    power?: number;
    updatedAt?: string;
  };
  currencies: {
    metal: number;
    crystal: number;
    deuterium: number;
    commandPoints: number;   // 已占用指挥值
    commandLimit: number;    // 指挥值上限
    blueprintPoints?: number;// 蓝图点数(如可获取)
  };
  blueprints: Array<{
    id: string;
    name: string;
    alias?: string;
    shipClass: string;       // 护卫舰/驱逐舰/巡洋舰/战巡/航母...
    rarity: string;          // 普通/稀有/罕见/史诗/传说
    subModel: string;        // 子型号，如 通用型/重炮型
    defaultPosition: "前排" | "中排" | "后排";
    owned: boolean;
    level: number;
    locked: boolean;
    pointsAllocated: number;
    pointsTotal: number;
    modules: Array<{ slot: string; name: string; unlocked: boolean }>;
    skills: Array<{ system: string; name: string; level: number; max: number }>;
  }>;
}
```

## 约定
- 字段缺失时：`meta.completeness` 对应键置 `false`，键名写入 `meta.missingFields`，并允许前端提示"可手动补录"。
- 渠道差异（官服/B服）只体现在 `meta.channel`，其余字段结构完全一致。
- 数值单位：资源类为整数；指挥值为整数；能力值(power)可为大整数。
