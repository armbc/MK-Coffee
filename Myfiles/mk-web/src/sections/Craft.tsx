import { useEffect, useRef, useState } from "react";
import Reveal from "@/components/Reveal";

const FEATURES = [
  {
    title: "批次杯测复检",
    desc: "每批熟豆出库前进行杯测，风味偏离即整批重烘，不让瑕疵豆流向客户吧台。",
  },
  {
    title: "曲线数字化管理",
    desc: "烘焙全程记录温度曲线，每条曲线可复现、可回溯，换豆季也能平稳过渡。",
  },
  {
    title: "商用产能保障",
    desc: "商用拼配支持周度稳定供货，下单后 48 小时内完成烘焙与发货。",
  },
];

/** 烘焙温度曲线：随滚动进度描画 */
function RoastCurve() {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)")
      .matches;
    if (reduced) {
      setProgress(1);
      return;
    }
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const el = wrapRef.current;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const vh = window.innerHeight;
        const p = (vh * 0.85 - rect.top) / (vh * 0.8);
        setProgress(Math.min(1, Math.max(0, p)));
      });
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  const LEN = 1000;
  const drawn = LEN * progress;

  return (
    <div ref={wrapRef} className="relative">
      <svg
        viewBox="0 0 640 300"
        className="w-full"
        role="img"
        aria-label="烘焙温度曲线示意图：回温点、梅纳反应、一爆与发展期"
      >
        {/* 网格 */}
        {[60, 120, 180, 240].map((y) => (
          <line
            key={y}
            x1="0"
            x2="640"
            y1={y}
            y2={y}
            stroke="#F8F7E5"
            strokeOpacity="0.08"
            strokeDasharray="2 6"
          />
        ))}
        {/* 曲线 */}
        <path
          d="M 10 50 C 55 120, 110 252, 150 252 C 190 252, 250 226, 310 196 C 368 170, 420 142, 470 118 C 522 92, 572 62, 614 42 L 630 38"
          fill="none"
          stroke="#b39c4f"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray={LEN}
          strokeDashoffset={LEN - drawn}
        />
        {/* 关键节点 */}
        {[
          { x: 150, y: 252, t: "回温点", en: "Turning Point" },
          { x: 310, y: 196, t: "梅纳反应", en: "Maillard" },
          { x: 470, y: 118, t: "一爆", en: "First Crack" },
          { x: 614, y: 42, t: "发展期", en: "Development" },
        ].map((n) => {
          const anchor = n.x > 560 ? "end" : "middle";
          return (
            <g key={n.t} opacity={progress > n.x / 640 - 0.05 ? 1 : 0.15}>
              <circle cx={n.x} cy={n.y} r="4" fill="#b39c4f" />
              <circle cx={n.x} cy={n.y} r="9" fill="none" stroke="#b39c4f" strokeOpacity="0.4" />
              <text
                x={n.x}
                y={n.y - 18}
                textAnchor={anchor}
                fill="#F8F7E5"
                fontSize="13"
              >
                {n.t}
              </text>
              <text
                x={n.x}
                y={n.y - 34}
                textAnchor={anchor}
                fill="#b39c4f"
                fontSize="9"
                letterSpacing="2"
              >
                {n.en.toUpperCase()}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default function Craft() {
  return (
    <section id="craft" className="scroll-mt-24 bg-roast text-cream">
      <div className="mx-auto max-w-7xl px-5 py-24 md:px-10 md:py-36">
        <div className="grid items-end gap-10 md:grid-cols-12">
          <div className="md:col-span-8">
            <Reveal>
              <p className="text-xs uppercase tracking-[0.4em] text-gold">
                Roasting / 商用烘焙
              </p>
            </Reveal>
            <Reveal delay={100}>
              <h2 className="font-display mt-6 text-4xl leading-[1.2] md:text-6xl">
                温度有曲线，
                <br />
                <span className="font-display-light text-gold">
                  风味有秩序。
                </span>
              </h2>
            </Reveal>
          </div>
          <Reveal delay={200} className="md:col-span-4">
            <p className="max-w-sm text-sm leading-loose text-cream/70 md:justify-self-end">
              商用烘焙的标准不只是把豆子烘熟，而是在产能、成本与风味之间找到可长期复现的平衡点。我们把每一个关键节点都写进曲线里，确保第1杯与第100杯口感相同。
            </p>
          </Reveal>
        </div>

        <div className="mt-16">
          <Reveal delay={150}>
            <RoastCurve />
          </Reveal>
        </div>

        <div className="mt-16 grid gap-px overflow-hidden border border-cream/10 bg-cream/10 md:grid-cols-3">
          {FEATURES.map((f, i) => (
            <Reveal key={f.title} delay={i * 120} className="bg-roast p-8 md:p-10">
              <div className="dot-line mb-8 w-16 text-gold" aria-hidden="true" />
              <h3 className="font-display text-xl">{f.title}</h3>
              <p className="mt-3 text-sm leading-loose text-cream/65">
                {f.desc}
              </p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
