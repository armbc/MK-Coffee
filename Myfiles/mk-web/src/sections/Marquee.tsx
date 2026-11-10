const WORDS = [
  "精品咖啡",
  "Specialty",
  "商用烘焙",
  "Commercial Roasting",
  "OEM/ODM 定制",
  "Private Label",
  "新鲜烘焙",
  "Fresh Roasted",
  "杯测品控",
  "Cupping QC",
];

export default function Marquee() {
  const row = [...WORDS, ...WORDS];
  return (
    <div
      className="marquee overflow-hidden border-y border-ink/10 bg-paper py-4"
      aria-hidden="true"
    >
      <div className="marquee-track flex w-max items-center gap-8 whitespace-nowrap">
        {row.map((w, i) => (
          <span key={i} className="flex items-center gap-8">
            <span
              className={`${
                /[\u4e00-\u9fa5]/.test(w)
                  ? "font-display text-lg"
                  : "text-xs uppercase tracking-[0.35em] text-clay"
              }`}
            >
              {w}
            </span>
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-gold" />
          </span>
        ))}
      </div>
    </div>
  );
}
