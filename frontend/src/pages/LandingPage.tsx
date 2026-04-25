import { useState } from "react";
import { Link } from "react-router-dom";
import { BarChart3, Gauge, ScanLine, TrendingUp } from "lucide-react";

import { Button } from "../components/ui/Button";

const STEPS = [
  {
    icon: "📸",
    title: "Scan your receipt",
    desc: "Photo your grocery receipt. Our AI reads every item instantly.",
  },
  {
    icon: "🥦",
    title: "See your breakdown",
    desc: "Every item classified against the Dutch Schijf van Vijf. See what's in, what's out, what it adds up to.",
  },
  {
    icon: "📈",
    title: "Watch it compound",
    desc: "Your buiten-de-Schijf spend converts to an investment projection — 1, 5, and 10 years.",
  },
];

const USE_CASES = [
  {
    id: "shopper",
    emoji: "🛒",
    title: "The Weekly Shopper",
    who: "Shops at Albert Heijn or Jumbo 2–3× per week",
    pain: "No idea how much they actually spend on snacks, energy drinks, and processed food",
    steps: [
      "Scans AH receipt after weekly shop",
      "Sees: 12 items total — 4 in de Schijf, 8 buiten de Schijf (67%)",
      "Biggest offenders: Doritos €2.49, Red Bull 4-pack €6.99, Ben & Jerry's €5.49",
      "Monthly projection: if this is typical → €54/month discretionary",
      "10-year projection at 5%: €8,396",
    ],
    punchline: "Your snack habit has a price tag. Now you can see it.",
  },
  {
    id: "bettor",
    emoji: "🎯",
    title: "The Self-Bettor",
    who: "Knows they spend too much on junk but needs external accountability",
    pain: "Good intentions, no follow-through — willpower alone doesn't work",
    steps: [
      "Views 3-month buiten-de-Schijf average: €78/month",
      "Sets a bet: reduce by 20% → target €62/month",
      "Locks €20 into their bunq Vault",
      "Scans receipts throughout the month — each scan updates progress",
      "Hits target → €20 returned + bunq premium tokens redeemed",
    ],
    punchline: "Your own money is the best coach you've ever had.",
  },
  {
    id: "investor",
    emoji: "📊",
    title: "The Long-Term Investor",
    who: "Already interested in personal finance, looking for savings to redirect",
    pain: "Knows they should invest more, but can't find where the money comes from",
    steps: [
      "Reviews 3-month discretionary grocery spend: €234 total",
      "Sees projection: €234 over 10 years at 5% = €3,624",
      "One click: \"Redirect my discretionary savings to S&P 500 ETF\"",
      "Agent proposes €78/month recurring investment via bunq",
      "Human confirms → automated",
    ],
    punchline: "The money was already there. You just couldn't see it.",
  },
];

export function LandingPage() {
  const [activeCase, setActiveCase] = useState("shopper");
  const active = USE_CASES.find((c) => c.id === activeCase)!;

  return (
    <div className="min-h-screen bg-white text-ink">
      {/* Nav */}
      <header className="sticky top-0 z-20 border-b border-ink/8 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <Link to="/" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-ink text-white">
              <Gauge size={18} />
            </span>
            <span className="font-semibold text-ink">Bunq Bite Balance</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" className="text-sm">Sign in</Button>
            </Link>
            <Link to="/register">
              <Button className="bg-mint text-white hover:bg-mint/90 text-sm">Get started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 py-20 text-center">
        <p className="inline-flex items-center gap-2 rounded-full border border-mint/30 bg-mint/8 px-4 py-1.5 text-xs font-semibold text-mint mb-8">
          Powered by Claude AI + bunq API
        </p>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight sm:text-5xl lg:text-6xl max-w-3xl mx-auto">
          You know you could eat better.{" "}
          <span className="text-mint">We'll show you what it's costing you.</span>
        </h1>
        <p className="mt-6 text-lg text-ink/55 max-w-xl mx-auto leading-relaxed">
          Scan your grocery receipt. See exactly how much you're spending buiten de Schijf — and what that money could become.
        </p>
        <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/register">
            <Button className="bg-mint text-white hover:bg-mint/90 px-7 py-3 text-base h-auto">
              <ScanLine size={18} />
              Scan my first receipt →
            </Button>
          </Link>
          <a href="#how-it-works">
            <Button variant="secondary" className="px-7 py-3 text-base h-auto">
              See how it works ↓
            </Button>
          </a>
        </div>

        {/* Animated mockup */}
        <div className="mt-14 mx-auto max-w-sm rounded-2xl bg-ink p-5 text-left shadow-panel">
          <div className="flex items-center gap-2 mb-4">
            <div className="h-2 w-2 rounded-full bg-mint animate-pulse" />
            <span className="text-xs text-white/40">Processing your receipt...</span>
          </div>
          <div className="grid gap-2">
            {[
              { name: "Hagelslag", cat: "In Schijf", color: "text-mint" },
              { name: "Red Bull 4-pack", cat: "Buiten Schijf", color: "text-coral" },
              { name: "Doritos", cat: "Buiten Schijf", color: "text-coral" },
              { name: "Brood volkoren", cat: "In Schijf", color: "text-mint" },
              { name: "Ben & Jerry's", cat: "Dagkeuze", color: "text-amber" },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between rounded-lg bg-white/6 px-3 py-2">
                <span className="text-sm text-white">{item.name}</span>
                <span className={`text-xs font-semibold ${item.color}`}>{item.cat}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-lg bg-mint/15 border border-mint/25 p-3">
            <p className="text-xs text-white/60">10-year investment projection</p>
            <p className="text-xl font-semibold text-mint mt-1">€8,396</p>
            <p className="text-xs text-white/40">at 5% annual return</p>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="bg-ink py-20">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <h2 className="text-3xl font-semibold text-white sm:text-4xl">The system isn't designed to help you.</h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-3">
            {[
              { stat: "80%", text: "of supermarket shelf space is dedicated to products outside the Dutch dietary recommendation" },
              { stat: "€94/mo", text: "average Dutch household spend on discretionary food items" },
              { stat: "0", text: "grocery apps that connect what you eat to what you could build financially" },
            ].map(({ stat, text }) => (
              <div key={stat} className="rounded-xl border border-white/8 bg-white/5 p-8">
                <p className="text-4xl font-semibold text-coral">{stat}</p>
                <p className="mt-3 text-sm text-white/55 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
          <p className="mt-10 text-lg text-white/40 italic">We fix the last one.</p>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <p className="text-center text-sm font-semibold uppercase tracking-wider text-mint mb-3">How it works</p>
          <h2 className="text-center text-3xl font-semibold sm:text-4xl">Three steps. Thirty seconds.</h2>
          <div className="mt-12 grid gap-6 sm:grid-cols-3">
            {STEPS.map((step, i) => (
              <div key={i} className="rounded-xl border border-ink/10 bg-cloud p-6">
                <div className="text-3xl mb-4">{step.icon}</div>
                <p className="font-semibold text-ink">{step.title}</p>
                <p className="mt-2 text-sm text-ink/55 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="bg-cloud py-20">
        <div className="mx-auto max-w-6xl px-6">
          <p className="text-center text-sm font-semibold uppercase tracking-wider text-mint mb-3">Use cases</p>
          <h2 className="text-center text-3xl font-semibold sm:text-4xl">Who is this for?</h2>

          <div className="mt-10 flex flex-wrap justify-center gap-2">
            {USE_CASES.map((c) => (
              <button
                key={c.id}
                onClick={() => setActiveCase(c.id)}
                className={[
                  "rounded-full px-5 py-2 text-sm font-semibold transition",
                  activeCase === c.id
                    ? "bg-ink text-white"
                    : "border border-ink/15 bg-white text-ink hover:bg-ink/5",
                ].join(" ")}
              >
                {c.emoji} {c.title}
              </button>
            ))}
          </div>

          <div className="mt-8 rounded-2xl border border-ink/10 bg-white p-8 shadow-panel">
            <div className="grid gap-8 lg:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-ink/40 mb-1">Who</p>
                <p className="text-sm text-ink/70">{active.who}</p>
                <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-ink/40 mb-1">Pain</p>
                <p className="text-sm text-ink/70">{active.pain}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-ink/40 mb-3">Flow</p>
                <ol className="grid gap-2">
                  {active.steps.map((step, i) => (
                    <li key={i} className="flex gap-3 text-sm text-ink/70">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-mint/15 text-xs font-semibold text-mint">
                        {i + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            </div>
            <div className="mt-6 border-t border-ink/8 pt-5">
              <p className="text-sm font-semibold text-ink italic">"{active.punchline}"</p>
            </div>
          </div>
        </div>
      </section>

      {/* Self-Bet Callout */}
      <section className="py-20">
        <div className="mx-auto max-w-6xl px-6 grid gap-10 lg:grid-cols-2 items-center">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-mint mb-3">The differentiator</p>
            <h2 className="text-3xl font-semibold sm:text-4xl">Bet on yourself. With your own money.</h2>
            <p className="mt-4 text-ink/55 leading-relaxed">
              Most apps tell you what to do. This one asks if you're ready to commit — and puts a small, refundable stake on the answer. Nobody loses money. But the commitment changes everything.
            </p>
          </div>
          <div className="rounded-2xl border border-ink/10 bg-cloud p-6 font-mono text-sm shadow-panel">
            <div className="grid gap-3">
              <div className="flex justify-between">
                <span className="text-ink/50">📊 Buiten-Schijf spend last month</span>
                <span className="font-semibold text-ink">€94</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink/50">🎯 Your target this month</span>
                <span className="font-semibold text-mint">€75 (−20%)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink/50">💰 Your stake</span>
                <span className="font-semibold text-ink">€20 locked in vault</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink/50">⏳ Days remaining</span>
                <span className="font-semibold text-ink">14</span>
              </div>
              <div className="mt-2 rounded-lg bg-white p-3 border border-ink/10">
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-ink/50">Progress</span>
                  <span className="font-semibold text-mint">73% on track ✅</span>
                </div>
                <div className="h-2 rounded-full bg-ink/8 overflow-hidden">
                  <div className="h-full w-[73%] rounded-full bg-mint" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Credibility */}
      <section className="bg-cloud py-16">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-6 sm:grid-cols-3 text-center">
            <div className="rounded-xl bg-white border border-ink/8 p-6">
              <div className="flex justify-center mb-3">
                <BarChart3 size={24} className="text-mint" />
              </div>
              <p className="text-xs text-ink/50 leading-relaxed">
                Classification based on <strong className="text-ink">Voedingscentrum's Schijf van Vijf</strong> — the Dutch national dietary standard since 1953
              </p>
            </div>
            <div className="rounded-xl bg-white border border-ink/8 p-6">
              <div className="flex justify-center mb-3">
                <TrendingUp size={24} className="text-mint" />
              </div>
              <p className="text-sm font-semibold text-ink">€75/month → €11,628</p>
              <p className="mt-1 text-xs text-ink/50">in 10 years at 5% annual return</p>
            </div>
            <div className="rounded-xl bg-white border border-ink/8 p-6">
              <div className="flex justify-center mb-3 gap-2 items-center">
                <span className="text-xs font-semibold text-ink/60">Powered by</span>
              </div>
              <p className="text-sm font-semibold text-ink">Anthropic Claude AI</p>
              <p className="text-sm font-semibold text-mint">+ bunq API</p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-24 text-center">
        <div className="mx-auto max-w-2xl px-6">
          <h2 className="text-3xl font-semibold sm:text-4xl">Your next grocery trip is worth more than you think.</h2>
          <p className="mt-4 text-ink/50">The money was already there. You just couldn't see it — until now.</p>
          <Link to="/register" className="mt-8 inline-block">
            <Button className="bg-mint text-white hover:bg-mint/90 px-8 py-3 text-base h-auto">
              Scan your first receipt — it takes 30 seconds →
            </Button>
          </Link>
          <div className="mt-5 flex items-center justify-center gap-6 text-xs text-ink/40">
            <span>🔒 No card required</span>
            <span>🇳🇱 Built for Dutch households</span>
            <span>💚 Powered by bunq</span>
          </div>
        </div>
      </section>
    </div>
  );
}
