import { useEffect, useState } from "react";
import Logo from "@/components/Logo";

const NAV = [
  { id: "about", label: "品牌", en: "About" },
  { id: "factory", label: "工厂展示", en: "Factory" },
  { id: "craft", label: "烘焙", en: "Roasting" },
  { id: "soe", label: "OEM/ODM 定制", en: "Custom" },
  { id: "products", label: "产品", en: "Products" },
  { id: "contact", label: "合作洽谈", en: "Contact" },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const go = (id: string) => {
    setOpen(false);
    requestAnimationFrame(() => {
      document
        .getElementById(id)
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  return (
    <>
      <header
        className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
          scrolled
            ? "bg-cream/90 backdrop-blur-md border-b border-ink/10"
            : "bg-transparent"
        }`}
      >
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 md:h-20 md:px-10">
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            aria-label="回到顶部"
            className="cursor-pointer"
          >
            <Logo dark={!scrolled} iconBig={!scrolled} />
          </button>

          <nav className="hidden items-center gap-8 md:flex" aria-label="主导航">
            {NAV.map((item) => (
              <button
                key={item.id}
                onClick={() => go(item.id)}
                className={`group cursor-pointer text-sm transition-colors ${
                  scrolled
                    ? "text-ink/80 hover:text-ink"
                    : "text-cream/85 hover:text-cream"
                }`}
              >
                <span className="font-display">
                  {item.id === "soe" ? (
                    <>
                      <span className="font-normal">OEM/ODM</span> 定制
                    </>
                  ) : (
                    item.label
                  )}
                </span>
                <span
                  className={`ml-1.5 text-[10px] uppercase tracking-[0.2em] transition-colors group-hover:text-gold ${
                    scrolled ? "text-clay" : "text-cream/50"
                  }`}
                >
                  {item.en}
                </span>
              </button>
            ))}
            <button
              onClick={() => go("contact")}
              className="cursor-pointer whitespace-nowrap rounded-full bg-gold px-5 py-2 text-sm font-medium text-ink transition-transform duration-200 hover:scale-[1.04] active:scale-95"
            >
              预约烘焙咨询
            </button>
          </nav>

          <button
            className="flex h-11 w-11 cursor-pointer flex-col items-center justify-center gap-1.5 md:hidden"
            aria-label={open ? "关闭菜单" : "打开菜单"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <span
              className={`h-0.5 w-6 transition-transform duration-200 ${
                open || scrolled ? "bg-ink" : "bg-cream"
              } ${
                open ? "translate-y-1 rotate-45" : ""
              }`}
            />
            <span
              className={`h-0.5 w-6 transition-transform duration-200 ${
                open || scrolled ? "bg-ink" : "bg-cream"
              } ${open ? "-translate-y-1 -rotate-45" : ""}`}
            />
          </button>
        </div>
      </header>

      {/* 移动端全屏菜单 */}
      {open && (
        <div
          className="fixed inset-0 z-40 flex flex-col bg-roast px-8 pb-10 pt-28 text-cream md:hidden"
          role="dialog"
          aria-modal="true"
          onClick={(e) => {
            if (e.target === e.currentTarget) setOpen(false);
          }}
        >
          <nav className="flex flex-col gap-2" aria-label="移动端导航">
            {NAV.map((item, i) => (
              <button
                key={item.id}
                onClick={() => go(item.id)}
                className="cursor-pointer border-b border-cream/10 py-4 text-left"
                style={{ transitionDelay: `${i * 40}ms` }}
              >
                <span className="font-display text-2xl">{item.label}</span>
                <span className="ml-3 text-xs uppercase tracking-[0.3em] text-gold">
                  {item.en}
                </span>
              </button>
            ))}
          </nav>
          <button
            onClick={() => go("contact")}
            className="mt-auto cursor-pointer rounded-full bg-gold py-4 text-base font-medium text-ink"
          >
            预约烘焙咨询
          </button>
        </div>
      )}
    </>
  );
}
