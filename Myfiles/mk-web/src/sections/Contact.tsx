import { useEffect, useState, type FormEvent } from "react";
import Reveal from "@/components/Reveal";
import { trpc } from "@/providers/trpc";

const INTENTS = [
  { value: "soe", label: "OEM/ODM 定制" },
  { value: "commercial", label: "商用烘焙合作" },
  { value: "beans", label: "咖啡豆采购" },
  { value: "gift", label: "企业礼赠" },
  { value: "other", label: "其他合作" },
] as const;

type Intent = (typeof INTENTS)[number]["value"];

export default function Contact({
  initialIntent,
  intentSignal,
}: {
  initialIntent: Intent;
  intentSignal: number;
}) {
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [phone, setPhone] = useState("");
  const [intent, setIntent] = useState<Intent>(initialIntent);
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);

  useEffect(() => {
    setIntent(initialIntent);
  }, [initialIntent, intentSignal]);

  const mutation = trpc.leads.create.useMutation({
    onSuccess: () => setDone(true),
    onError: () =>
      setErrors({ form: "提交失败，请稍后重试，或直接致电我们。" }),
  });

  const validate = () => {
    const e: Record<string, string> = {};
    if (!name.trim()) e.name = "请填写您的称呼";
    if (!/^1[3-9]\d{9}$/.test(phone.trim()) && !/^[\d\s+-]{5,}$/.test(phone.trim()))
      e.phone = "请填写有效的联系电话";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const submit = (ev: FormEvent) => {
    ev.preventDefault();
    if (!validate()) return;
    mutation.mutate({
      name: name.trim(),
      company: company.trim() || undefined,
      phone: phone.trim(),
      intent,
      message: message.trim() || undefined,
    });
  };

  const reset = () => {
    setDone(false);
    setName("");
    setCompany("");
    setPhone("");
    setMessage("");
    setErrors({});
  };

  const inputCls = (key: string) =>
    `w-full border-0 border-b bg-transparent py-3 text-cream placeholder:text-cream/35 focus:outline-none transition-colors ${
      errors[key] ? "border-destructive" : "border-cream/25 focus:border-gold"
    }`;

  return (
    <section id="contact" className="scroll-mt-24 bg-roast text-cream">
      <div className="mx-auto max-w-7xl px-5 py-24 md:px-10 md:py-36">
        <div className="grid gap-14 md:grid-cols-12">
          <div className="md:col-span-5">
            <Reveal>
              <p className="text-sm uppercase tracking-[0.4em] text-gold">
                Contact / 合作洽谈
              </p>
            </Reveal>
            <Reveal delay={100}>
              <h2 className="font-display mt-6 text-4xl leading-[1.2] md:text-6xl">
                聊聊你的
                <br />
                <span className="font-display-light text-gold">咖啡计划。</span>
              </h2>
            </Reveal>
            <Reveal delay={200}>
              <p className="mt-8 max-w-md text-base leading-loose text-cream/70">
                留下您的需求，我们的烘焙顾问会在 1
                天内与您联系，为您推荐合适的豆单与烘焙方案。您也可以直接来昆山工坊参观 cupping。
              </p>
            </Reveal>
            <Reveal delay={300}>
              <dl className="mt-12 space-y-5 text-sm">
                <div className="flex gap-4">
                  <dt className="w-16 shrink-0 text-cream/45">公司</dt>
                  <dd className="font-hei">苏州迈科咖啡有限公司</dd>
                </div>
                <div className="flex gap-4">
                  <dt className="w-16 shrink-0 text-cream/45">地址</dt>
                  <dd className="font-hei">
                    江苏省昆山市综合保税区外河泾路177号1号厂房2F
                  </dd>
                </div>
                <div className="flex gap-4">
                  <dt className="w-16 shrink-0 text-cream/45">响应</dt>
                  <dd className="font-hei">1 天内回复</dd>
                </div>
                <div className="flex gap-4">
                  <dt className="w-16 shrink-0 text-cream/45">联系</dt>
                  <dd className="font-hei">
                    陈先生{" "}
                    <a
                      href="tel:18047204207"
                      className="underline decoration-cream/30 underline-offset-4 transition-colors hover:text-gold hover:decoration-gold"
                    >
                      18047204207
                    </a>
                    <br />
                    马先生{" "}
                    <a
                      href="tel:15661451225"
                      className="underline decoration-cream/30 underline-offset-4 transition-colors hover:text-gold hover:decoration-gold"
                    >
                      15661451225
                    </a>
                  </dd>
                </div>
              </dl>
            </Reveal>
          </div>

          <div className="md:col-span-7">
            <Reveal delay={150}>
              {done ? (
                <div className="flex h-full min-h-[420px] flex-col items-start justify-center border border-cream/15 p-10">
                  <span
                    className="flex h-12 w-12 items-center justify-center rounded-full border border-gold text-gold"
                    aria-hidden="true"
                  >
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M5 13l4 4L19 7"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <h3 className="font-display mt-6 text-3xl">
                    已收到您的需求。
                  </h3>
                  <p className="mt-3 max-w-md text-sm leading-loose text-cream/70">
                    感谢您的留言，我们的烘焙顾问会尽快与您联系。若需求紧急，欢迎通过官网预约到坊 cupping，现场沟通更高效。
                  </p>
                  <button
                    onClick={reset}
                    className="mt-8 cursor-pointer rounded-full border border-cream/30 px-6 py-3 text-sm text-cream transition-colors hover:border-gold hover:text-gold"
                  >
                    再提交一条
                  </button>
                </div>
              ) : (
                <form onSubmit={submit} noValidate className="border border-cream/15 p-8 md:p-10">
                  <div className="grid gap-8 md:grid-cols-2">
                    <div>
                      <label htmlFor="lead-name" className="text-xs uppercase tracking-[0.25em] text-cream/50">
                        您的称呼 *
                      </label>
                      <input
                        id="lead-name"
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="王小姐 / Kevin"
                        className={inputCls("name")}
                        aria-invalid={!!errors.name}
                      />
                      {errors.name && (
                        <p className="mt-1.5 text-xs text-destructive">{errors.name}</p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="lead-company" className="text-xs uppercase tracking-[0.25em] text-cream/50">
                        公司 / 门店
                      </label>
                      <input
                        id="lead-company"
                        type="text"
                        value={company}
                        onChange={(e) => setCompany(e.target.value)}
                        placeholder="选填"
                        className={inputCls("company")}
                      />
                    </div>
                    <div>
                      <label htmlFor="lead-phone" className="text-xs uppercase tracking-[0.25em] text-cream/50">
                        联系电话 *
                      </label>
                      <input
                        id="lead-phone"
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="用于顾问回访"
                        className={inputCls("phone")}
                        aria-invalid={!!errors.phone}
                      />
                      {errors.phone && (
                        <p className="mt-1.5 text-xs text-destructive">{errors.phone}</p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="lead-intent" className="text-xs uppercase tracking-[0.25em] text-cream/50">
                        合作意向
                      </label>
                      <select
                        id="lead-intent"
                        value={intent}
                        onChange={(e) => setIntent(e.target.value as Intent)}
                        className={`${inputCls("intent")} cursor-pointer appearance-none`}
                      >
                        {INTENTS.map((o) => (
                          <option key={o.value} value={o.value} className="bg-roast text-cream">
                            {o.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="mt-8">
                    <label htmlFor="lead-message" className="text-xs uppercase tracking-[0.25em] text-cream/50">
                      需求描述
                    </label>
                    <textarea
                      id="lead-message"
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="例如：想为自有品牌定制一支中深烘拼配，月需求约 200 公斤……"
                      rows={4}
                      className={`${inputCls("message")} resize-y`}
                    />
                  </div>
                  {errors.form && (
                    <p className="mt-4 text-sm text-destructive">{errors.form}</p>
                  )}
                  <button
                    type="submit"
                    disabled={mutation.isPending}
                    className="mt-10 w-full cursor-pointer rounded-full bg-gold py-4 text-sm font-medium tracking-wide text-ink transition-all duration-200 hover:scale-[1.01] active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60 md:w-auto md:px-12"
                  >
                    {mutation.isPending ? "提交中……" : "提交需求"}
                  </button>
                </form>
              )}
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
