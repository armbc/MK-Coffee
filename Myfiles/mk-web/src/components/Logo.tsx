export default function Logo({
  dark = false,
  iconBig = false,
}: {
  dark?: boolean;
  iconBig?: boolean;
}) {
  const ink = dark ? "#F8F7E5" : "#1D1D1D";
  const gold = "#b39c4f";
  return (
    <span className="inline-flex items-center gap-3">
      <span
        className={`inline-flex origin-center transition-transform duration-300 ease-out ${
          iconBig ? "scale-125" : "scale-100"
        }`}
      >
        <svg
          width="34"
          height="34"
          viewBox="0 0 40 40"
          fill="none"
          aria-hidden="true"
        >
        {/* 咖啡豆外形 */}
        <ellipse
          cx="20"
          cy="20"
          rx="13"
          ry="17"
          transform="rotate(28 20 20)"
          stroke={ink}
          strokeWidth="2"
          fill="none"
        />
        {/* 豆中线 */}
        <path
          d="M13.5 10.5 C 17 16, 15 24, 23 31"
          transform="rotate(28 20 20)"
          stroke={gold}
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
        </svg>
      </span>
      <span className="leading-none">
        <span
          className="font-display block text-lg tracking-wide"
          style={{ color: ink }}
        >
          苏州迈科咖啡
        </span>
        <span
          className="block whitespace-nowrap text-[8px] uppercase tracking-[0.16em] sm:text-[9px] sm:tracking-[0.2em]"
          style={{ color: dark ? "#b39c4f" : "#6b6552" }}
        >
          Suzhou Michael Coffee Co., LTD
        </span>
      </span>
    </span>
  );
}
