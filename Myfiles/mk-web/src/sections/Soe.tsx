import Reveal from "@/components/Reveal";

const STEPS = [
  {
    title: "需求沟通",
    desc: "了解品牌定位、销售渠道与销量预期，明确风味方向与成本区间。",
  },
  {
    title: "选豆打样",
    desc: "从当季生豆库中筛选候选豆，烘焙小样并附风味描述与报价。",
  },
  {
    title: "配方与包装",
    desc: "确定拼配方案与烘焙度，配合设计贴牌包装，输出完整样品。",
  },
  {
    title: "杯测确认",
    desc: "寄样杯测，确认风味与包装后锁定生产标准与交付周期。",
  },
  {
    title: "量产交付",
    desc: "按订单排产烘焙，标注烘焙日期，支持一件代发与周期性补货。",
  },
];

export default function Soe() {
  return (
    <section id="soe" className="scroll-mt-24 bg-paper">
      <div className="mx-auto max-w-7xl px-5 py-24 md:px-10 md:py-36">
        <div className="grid gap-14 md:grid-cols-12">
          {/* 左：图 */}
          <div className="md:col-span-5">
            <Reveal>
              <figure className="md:sticky md:top-28">
                <div className="overflow-hidden">
                  <img
                    src="/img/oem.jpg"
                    alt="迈科咖啡 OEM/ODM 定制产品系列：贴牌咖啡豆袋、礼盒、挂耳包与咖啡器具"
                    className="aspect-[4/3] w-full object-cover transition-transform duration-700 ease-out hover:scale-[1.03]"
                  />
                </div>
              </figure>
            </Reveal>
          </div>

          {/* 右：流程 */}
          <div className="md:col-span-7">
            <Reveal>
              <p className="text-xs uppercase tracking-[0.4em] text-clay">
                Custom / OEM/ODM 定制
              </p>
            </Reveal>
            <Reveal delay={100}>
              <h2 className="font-display mt-6 text-4xl leading-[1.2] md:text-6xl">
                你的品牌，
                <br />
                <span className="font-display-light text-gold">
                  值得一支专属豆。
                </span>
              </h2>
            </Reveal>
            <Reveal delay={200}>
              <p className="mt-8 max-w-xl text-base leading-loose text-ink/75">
                OEM/ODM 定制服务，为连锁品牌、餐饮企业与电商客户提供从选豆、拼配、烘焙到包装贴牌的一站式代工。支持专属风味开发、自有品牌包装设计与小批量柔性起订，全流程约
                2–3 周打样确认。
              </p>
            </Reveal>

            <ol className="mt-12">
              {STEPS.map((s, i) => (
                <Reveal
                  as="li"
                  key={s.title}
                  delay={i * 90}
                  className="group flex gap-6 border-t border-ink/15 py-6 last:border-b"
                >
                  <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-ink/25 text-sm text-clay transition-colors duration-200 group-hover:border-gold group-hover:text-gold">
                    {i + 1}
                  </span>
                  <div>
                    <h3 className="font-display text-xl">{s.title}</h3>
                    <p className="mt-1.5 max-w-lg text-sm leading-loose text-ink/65">
                      {s.desc}
                    </p>
                  </div>
                </Reveal>
              ))}
            </ol>

            <Reveal delay={200}>
              <button
                onClick={() =>
                  document
                    .getElementById("contact")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
                className="mt-10 cursor-pointer rounded-full bg-ink px-8 py-3.5 text-sm tracking-wide text-cream transition-transform duration-200 hover:scale-[1.04] active:scale-95"
              >
                启动我的 OEM/ODM 定制
              </button>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
