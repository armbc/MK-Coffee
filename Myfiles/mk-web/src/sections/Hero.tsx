import { useEffect, useRef, useState } from "react";
import Reveal from "@/components/Reveal";

export default function Hero() {
  const ref = useRef<HTMLElement | null>(null);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)")
      .matches;
    if (reduced) return;
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        setOffset(window.scrollY * 0.25);
      });
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  const go = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <section
      ref={ref}
      className="relative flex min-h-[100dvh] items-end overflow-hidden bg-roast"
      aria-label="迈科咖啡品牌主视觉"
    >
      {/* 背景图 + 视差 */}
      <div
        className="absolute inset-0 scale-110"
        style={{ transform: `translateY(${offset}px) scale(1.1)` }}
        aria-hidden="true"
      >
        <img
          src="/img/hero.jpg"
          alt=""
          className="h-full w-full object-cover opacity-70"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-roast via-roast/40 to-roast/30" />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-7xl px-5 pb-20 pt-40 md:px-10 md:pb-28">
        <Reveal>
          <p className="mb-6 flex items-center gap-3 text-xs uppercase tracking-[0.4em] text-gold">
            <span className="inline-block h-px w-10 bg-gold/70" />
            Specialty Coffee Roaster · Suzhou
          </p>
        </Reveal>

        <Reveal delay={120}>
          <h1 className="font-display max-w-4xl text-cream">
            <span className="block text-5xl leading-[1.1] md:text-7xl lg:text-8xl">
              为每一杯，
            </span>
            <span className="font-display-light mt-2 block text-5xl leading-[1.1] text-gold md:text-7xl lg:text-8xl">
              烘焙到恰好。
            </span>
          </h1>
        </Reveal>

        <Reveal delay={240}>
          <p className="mt-8 max-w-xl text-base leading-relaxed text-cream/80 md:text-lg">
            苏州迈科咖啡有限公司——专注精品咖啡、商用咖啡烘焙与
            OEM/ODM 定制。从生豆甄选到曲线烘焙，为咖啡馆、餐饮品牌与企业客户提供稳定而有个性的咖啡解决方案。
          </p>
        </Reveal>

        <Reveal delay={360}>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <button
              onClick={() => go("contact")}
              className="cursor-pointer rounded-full bg-gold px-8 py-3.5 text-sm font-medium tracking-wide text-ink transition-transform duration-200 hover:scale-[1.04] active:scale-95"
            >
              预约烘焙咨询
            </button>
            <button
              onClick={() => go("craft")}
              className="group cursor-pointer rounded-full border border-cream/30 px-8 py-3.5 text-sm tracking-wide text-cream transition-colors hover:border-gold hover:text-gold"
            >
              了解我们的烘焙
              <span className="ml-2 inline-block transition-transform duration-200 group-hover:translate-x-1">
                →
              </span>
            </button>
          </div>
        </Reveal>
      </div>

      {/* 底部跑马灯与内容分隔 */}
      <div className="absolute inset-x-0 bottom-0 h-px bg-cream/10" aria-hidden="true" />
    </section>
  );
}
