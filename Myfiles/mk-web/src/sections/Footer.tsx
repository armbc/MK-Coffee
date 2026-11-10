import Logo from "@/components/Logo";

export default function Footer() {
  return (
    <footer className="border-t border-cream/10 bg-roast text-cream">
      <div className="mx-auto max-w-7xl px-5 py-14 md:px-10">
        <div className="flex flex-col gap-10 md:flex-row md:items-start md:justify-between">
          <div>
            <Logo dark />
            <p className="mt-5 max-w-sm text-sm leading-loose text-cream/60">
              精品咖啡 · 商用咖啡烘焙 · OEM/ODM 定制
              <br />
              苏州迈科咖啡有限公司
            </p>
          </div>
          <div className="text-sm text-cream/60">
            <p className="text-xs uppercase tracking-[0.3em] text-gold">Sitemap</p>
            <ul className="mt-4 space-y-2.5">
              {[
                { id: "about", label: "品牌" },
                { id: "craft", label: "商用烘焙" },
                { id: "products", label: "挂耳与礼盒系列" },
                { id: "products", label: "产品" },
                { id: "contact", label: "合作洽谈" },
              ].map((l) => (
                <li key={l.label}>
                  <button
                    onClick={() =>
                      document
                        .getElementById(l.id)
                        ?.scrollIntoView({ behavior: "smooth" })
                    }
                    className="cursor-pointer transition-colors hover:text-cream"
                  >
                    {l.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="dot-line mt-12 w-full text-cream/40" aria-hidden="true" />
        <div className="mt-6 flex flex-col gap-2 text-xs text-cream/40 md:flex-row md:items-center md:justify-between">
          <p>© {new Date().getFullYear()} 苏州迈科咖啡有限公司 · 保留所有权利</p>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <a
              href="https://beian.miit.gov.cn/"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-cream/70"
            >
              苏ICP备2026059759号-1
            </a>
            <a
              href="https://beian.mps.gov.cn/#/query/webSearch?code=32058302006935"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 transition-colors hover:text-cream/70"
            >
              <img src="/beian.png" alt="公安备案图标" className="h-4 w-auto" />
              苏公网安备32058302006935号
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
