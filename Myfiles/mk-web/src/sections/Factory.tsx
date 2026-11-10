import Reveal from "@/components/Reveal";

// 图片为占位图，待替换为工厂实拍
const PHOTOS = [
  {
    src: "/img/factory-materials.jpg",
    alt: "迈科咖啡包材仓库，纸箱与内包材整齐码放于货架",
    title: "包材仓储",
    en: "Packaging Storage",
    span: "md:col-span-7",
    ratio: "aspect-[16/10]",
  },
  {
    src: "/img/factory-storage.jpg",
    alt: "迈科咖啡生豆仓库，麻袋装生豆整齐码放于托盘上",
    title: "生豆仓储",
    en: "Green Bean Storage",
    span: "md:col-span-5",
    ratio: "aspect-[16/10]",
  },
  {
    src: "/img/factory-packing.jpg",
    alt: "迈科咖啡全自动挂耳包装设备",
    title: "全自动挂耳包装设备",
    en: "Auto Drip Bag Packing",
    span: "md:col-span-5",
    ratio: "aspect-[16/10]",
  },
  {
    src: "/img/factory-workshop.jpg",
    alt: "迈科咖啡工厂洁净车间走廊与工作环境",
    title: "工作环境",
    en: "Work Environment",
    span: "md:col-span-7",
    ratio: "aspect-[16/10]",
  },
];

export default function Factory() {
  return (
    <section id="factory" className="scroll-mt-24 bg-paper">
      <div className="mx-auto max-w-7xl px-5 py-24 md:px-10 md:py-36">
        <div className="grid gap-10 md:grid-cols-12 md:items-end">
          <div className="md:col-span-8">
            <Reveal>
              <p className="text-xs uppercase tracking-[0.4em] text-clay">
                Factory / 工厂展示
              </p>
            </Reveal>
            <Reveal delay={100}>
              <h2 className="font-display mt-6 text-4xl leading-[1.2] md:text-6xl">
                走进迈科的
                <span className="font-display-light text-gold">烘焙工厂</span>
              </h2>
            </Reveal>
          </div>
          <Reveal delay={200} className="md:col-span-4">
            <p className="text-base leading-loose text-ink/70">
              生豆与包材分区仓储，挂耳自动包装，全程洁净生产——每一道工序都在同一座工坊内可追溯地完成。
            </p>
          </Reveal>
        </div>

        <div className="mt-14 grid gap-6 md:grid-cols-12 md:gap-8">
          {PHOTOS.map((p, i) => (
            <Reveal key={p.title} delay={i * 120} className={p.span}>
              <figure className="group">
                <div className="overflow-hidden">
                  <img
                    src={p.src}
                    alt={p.alt}
                    className={`${p.ratio} w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.03]`}
                  />
                </div>
                <figcaption className="mt-4 flex items-baseline justify-between text-xs text-clay">
                  <span>{p.title}</span>
                  <span className="uppercase tracking-[0.25em]">{p.en}</span>
                </figcaption>
              </figure>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
