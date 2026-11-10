import Reveal from "@/components/Reveal";

const STATS = [
  { num: "12+", label: "年烘焙经验", en: "Years of Roasting" },
  { num: "30+", label: "合作咖啡品牌", en: "Partner Brands" },
  { num: "200+", label: "定制烘焙曲线", en: "Custom Profiles" },
  { num: "48h", label: "烘焙到发货", en: "Roast to Ship" },
];

export default function About() {
  return (
    <section id="about" className="scroll-mt-24 bg-cream">
      <div className="mx-auto max-w-7xl px-5 py-24 md:px-10 md:py-36">
        <div className="grid gap-14 md:grid-cols-12 md:gap-10">
          {/* 左：大字与文案 */}
          <div className="md:col-span-7">
            <Reveal>
              <p className="text-xs uppercase tracking-[0.4em] text-clay">
                About / 品牌
              </p>
            </Reveal>
            <Reveal delay={100}>
              <h2 className="font-display mt-6 text-4xl leading-[1.2] md:text-6xl">
                我们相信，
                <br />
                <span className="font-display-light text-gold">
                  好咖啡是可以被稳定复现的。
                </span>
              </h2>
            </Reveal>
            <Reveal delay={200}>
              <p className="mt-8 max-w-xl text-base leading-loose text-ink/75">
                迈科咖啡坐落于昆山市综合保税区，是一家专注于精品咖啡与商用咖啡烘焙的烘焙工坊。我们在10年服务与研修中，为小批量精品豆与大规模商用需求制定了一套严谨体系：拼配方案研制、生豆入库杯测、烘焙曲线记录、熟豆杯测复检、养豆期管理——每一批豆子都有据可查。
              </p>
              <p className="mt-4 max-w-xl text-base leading-loose text-ink/75">
                无论是连锁咖啡品牌的主力拼配，还是独立咖啡馆的专属
                OEM/ODM 定制，我们都以「风味稳定、交付准时、服务可追溯」为基本原则。
              </p>
            </Reveal>

            <Reveal delay={300}>
              <dl className="mt-14 grid grid-cols-2 gap-x-8 gap-y-10 md:grid-cols-4">
                {STATS.map((s) => (
                  <div key={s.label} className="border-t border-ink/15 pt-4">
                    <dd className="font-display block text-4xl text-ink md:text-5xl">
                      {s.num}
                    </dd>
                    <dt className="mt-2 block text-sm text-ink/70">{s.label}</dt>
                    <span className="mt-1 block text-[10px] uppercase tracking-[0.25em] text-clay">
                      {s.en}
                    </span>
                  </div>
                ))}
              </dl>
            </Reveal>
          </div>

          {/* 右：偏移图片 */}
          <div className="md:col-span-5">
            <Reveal delay={200} className="md:mt-24">
              <figure>
                <div className="overflow-hidden">
                  <img
                    src="/img/roastery.jpg"
                    alt="迈科咖啡烘焙师正在昆山工坊操作商用烘焙机"
                    className="aspect-[4/3] w-full object-cover transition-transform duration-700 ease-out hover:scale-[1.03]"
                  />
                </div>
                <figcaption className="mt-4 flex items-baseline justify-between text-xs text-clay">
                  <span>苏州 · 迈科烘焙工坊</span>
                  <span className="uppercase tracking-[0.25em]">Roastery</span>
                </figcaption>
              </figure>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
