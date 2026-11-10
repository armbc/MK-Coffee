import { getDb } from "./connection";
import { leads } from "@db/schema";
import { log } from "../lib/logger";

// 企业微信群机器人 Webhook。必须由环境变量注入，不硬编码在源码里：
// 源码会随代码分发，硬编码的 key 等于把群机器人地址一起发出去。
// 惰性读取：模块顶层读 process.env 会早于 dotenv/config 加载 .env
// （boot.ts 里 ./router 先于 ./lib/env 求值），那样本地 .env 里的 key 读不到。
function wecomWebhook(): string {
  return process.env.WECOM_WEBHOOK ?? "";
}

const INTENT_LABELS: Record<string, string> = {
  soe: "OEM 定制",
  commercial: "商用烘焙合作",
  beans: "咖啡豆采购",
  gift: "企业礼赠",
  other: "其他合作",
};

async function notifyWecom(data: {
  name: string;
  company?: string;
  phone: string;
  intent: string;
  message?: string;
}) {
  const webhook = wecomWebhook();
  if (!webhook) {
    log.warn("WECOM_WEBHOOK 未配置，跳过企业微信通知", { name: data.name });
    return;
  }
  const lines = [
    "【官网新留言】",
    `姓名：${data.name}`,
    data.company ? `公司：${data.company}` : null,
    `电话：${data.phone}`,
    `意向：${INTENT_LABELS[data.intent] ?? data.intent}`,
    data.message ? `留言：${data.message}` : null,
  ].filter(Boolean);
  try {
    const res = await fetch(webhook, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ msgtype: "text", text: { content: lines.join("\n") } }),
      // 企业微信正常响应在 200ms 内；没有超时会拖住表单提交
      signal: AbortSignal.timeout(8000),
    });
    const body = await res.json().catch(() => null);
    if (!res.ok || (body && (body as { errcode?: number }).errcode !== 0)) {
      log.error("企业微信通知失败", { status: res.status, body });
    }
  } catch (err) {
    log.error("企业微信通知异常", {
      error: err instanceof Error ? err.message : String(err),
    });
  }
}

export async function createLead(data: {
  name: string;
  company?: string;
  phone: string;
  intent: "soe" | "commercial" | "beans" | "gift" | "other";
  message?: string;
}) {
  const db = getDb();
  const [row] = await db
    .insert(leads)
    .values({
      name: data.name,
      company: data.company ?? null,
      phone: data.phone,
      intent: data.intent,
      message: data.message ?? null,
    })
    .$returningId();
  // 必须 await：原来的 void notifyWecom() 是 fire-and-forget，进程重启/退出时
  // 未完成的 fetch 会被直接丢弃，留言入库了但群里没有任何提醒。
  // notifyWecom 内部已 catch 全部错误，通知失败不会影响入库与提交结果。
  await notifyWecom(data);
  return { id: row.id };
}
