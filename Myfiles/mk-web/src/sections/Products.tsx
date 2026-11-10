import Reveal from "@/components/Reveal";

type Product = {
  img: string;
  alt: string;
  tag: string;
  name: string;
  en: string;
  desc: string;
  intent: "soe" | "commercial" | "beans";
  offset: string;
};

const PRODUCTS: Product[] = [
  {
    img: "/img/product-soe.jpg",
    alt: "迈克尔咖啡小罐豆系列实拍：耶加雪菲、意式拼配、曼特宁与哥伦比亚低因",
    tag: "OEM/ODM 定制",
    name: "品牌专属定制豆",
    en: "Private Label",
    desc: "从选豆、烘焙到包装设计的一站式贴牌服务，支持专属风味开发与柔性起订。",
    intent: "soe",
    offset: "md:mt-0",
  },
  {
    img: "/img/product-blend.jpg",
    alt: "迈克尔咖啡意式拼配咖啡豆袋实拍，玫瑰金与黑色包装",
    tag: "商用烘焙",
    name: "商用稳定拼配",
    en: "Commercial House Blend",
    desc: "为连锁与餐饮客户设计的日耗主力豆，风味稳定、供货准时、成本可控。",
    intent: "commercial",
    offset: "md:mt-16",
  },
  {
    img: "/img/product-drip.jpg",
    alt: "昆咖咖啡礼盒套装实拍：品山系列小罐、礼盒与手提袋",
    tag: "零售周边",
    name: "挂耳与礼盒系列",
    en: "Drip & Gift Box",
    desc: "同款烘焙豆延伸的零售产品线，适合企业礼赠与品牌周边开发。",
    intent: "beans",
    offset: "md:mt-32",
  },
];

export default function Products({
  onConsult,
}: {
  onConsult: (intent: "soe" | "commercial" | "beans") => void;
}) {
  return (
    <section id="products" className="scroll-mt-24 bg-cream">
      <div className="mx-auto max-w-7xl px-5 py-24 md:px-10 md:py-36">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <Reveal>
              <p className="text-xs uppercase tracking-[0.4em] text-clay">
                Beans / 产品
              </p>
            </Reveal>
            <Reveal delay={100}>
              <h2 className="font-display mt-6 text-4xl leading-[1.2] md:text-6xl">
                三条产品线，
                <br />
                <span className="font-display-light text-gold">
                  覆盖从吧台到礼盒。
                </span>
              </h2>
            </Reveal>
          </div>
          <Reveal delay={200}>
            <p className="max-w-xs text-sm leading-loose text-ink/65">
              所有产品在下单后烘焙，包装标注烘焙日期；企业礼赠与大批量采购支持专属方案。
            </p>
          </Reveal>
        </div>

        <div className="mt-16 grid gap-10 md:grid-cols-3 md:gap-8">
          {PRODUCTS.map((p, i) => (
            <Reveal key={p.name} delay={i * 120} className={p.offset}>
              <figure className="group">
                <div className="overflow-hidden bg-paper">
                  <img
                    src={p.img}
                    alt={p.alt}
                    className="aspect-square w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.04]"
                  />
                </div>
                <figcaption className="mt-5">
                  <span className="text-[10px] uppercase tracking-[0.3em] text-gold">
                    {p.tag}
                  </span>
                  <h3 className="font-display mt-2 text-2xl">
                    {p.name}
                    <span className="font-display-light ml-2 text-sm text-clay">
                      {p.en}
                    </span>
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink/65">
                    {p.desc}
                  </p>
                  <button
                    onClick={() => onConsult(p.intent)}
                    className="group/btn mt-4 inline-flex cursor-pointer items-center gap-2 text-sm text-ink underline decoration-gold decoration-2 underline-offset-4 transition-colors hover:text-gold"
                  >
                    咨询此款
                    <span className="transition-transform duration-200 group-hover/btn:translate-x-1">
                      →
                    </span>
                  </button>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
