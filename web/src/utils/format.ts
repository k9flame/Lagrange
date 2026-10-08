/** 数值/文本格式化工具 */

/** 千分位整数，例：128500000 -> 128,500,000 */
export function formatNumber(value: number | undefined | null): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return Math.round(value).toLocaleString('en-US')
}

/** 大数值缩写，例：128500000 -> 1.29亿 / 12345 -> 1.2万 */
export function formatCompact(value: number | undefined | null): string {
  if (value == null || !Number.isFinite(value)) return '—'
  const abs = Math.abs(value)
  if (abs >= 1e8) return `${(value / 1e8).toFixed(2)}亿`
  if (abs >= 1e4) return `${(value / 1e4).toFixed(1)}万`
  return formatNumber(value)
}

/** 百分比，0–100 之间的比例 */
export function percent(part: number, total: number): number {
  if (!Number.isFinite(part) || !Number.isFinite(total) || total <= 0) return 0
  return Math.min(100, Math.max(0, (part / total) * 100))
}

/** ISO8601 -> 本地可读时间 */
export function formatDateTime(iso: string | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(
    d.getMinutes()
  )}`
}

/** 采集来源的展示名 */
export function sourceLabel(source: string): string {
  const map: Record<string, string> = {
    mitmproxy: '代理抓包',
    emulator: '模拟器抓包',
    sample: '样例数据',
    manual: '手动补录'
  }
  return map[source] ?? source
}
