import { useState } from "react";
import Header from "@/sections/Header";
import Hero from "@/sections/Hero";
import Marquee from "@/sections/Marquee";
import About from "@/sections/About";
import Factory from "@/sections/Factory";
import Craft from "@/sections/Craft";
import Soe from "@/sections/Soe";
import Products from "@/sections/Products";
import Contact from "@/sections/Contact";
import Footer from "@/sections/Footer";

type Intent = "soe" | "commercial" | "beans" | "gift" | "other";

export default function Home() {
  const [intent, setIntent] = useState<Intent>("soe");
  const [intentSignal, setIntentSignal] = useState(0);

  const consult = (i: "soe" | "commercial" | "beans") => {
    setIntent(i);
    setIntentSignal((n) => n + 1);
    requestAnimationFrame(() => {
      document.getElementById("contact")?.scrollIntoView({ behavior: "smooth" });
    });
  };

  return (
    <div className="min-h-screen bg-cream">
      <div className="grain-overlay" aria-hidden="true" />
      <Header />
      <main>
        <Hero />
        <Marquee />
        <About />
        <Factory />
        <Craft />
        <Soe />
        <Products onConsult={consult} />
        <Contact initialIntent={intent} intentSignal={intentSignal} />
      </main>
      <Footer />
    </div>
  );
}
