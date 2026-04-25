import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Gauge } from "lucide-react";

import { Button } from "../components/ui/Button";
import { auth } from "../lib/auth";

export function RegisterPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  if (auth.isLoggedIn()) return <Navigate to="/dashboard" replace />;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    auth.login({ name, email });
    navigate("/dashboard");
  }

  return (
    <div className="flex min-h-screen">
      {/* Left — form */}
      <div className="flex flex-1 flex-col justify-center px-8 py-12 lg:px-16">
        <div className="mx-auto w-full max-w-sm">
          <Link to="/" className="mb-10 flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-ink text-white">
              <Gauge size={18} />
            </span>
            <span className="font-semibold text-ink">Bunq Bite Balance</span>
          </Link>

          <h1 className="text-2xl font-semibold text-ink">Create your account</h1>
          <p className="mt-1 text-sm text-ink/55">Start turning grocery habits into financial insight</p>

          <form onSubmit={handleSubmit} className="mt-8 grid gap-4">
            <div className="grid gap-1.5">
              <label className="text-sm font-medium text-ink" htmlFor="name">First name</label>
              <input
                id="name"
                type="text"
                required
                autoComplete="given-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder-ink/35 outline-none focus:border-mint focus:ring-2 focus:ring-mint/20"
                placeholder="Karl"
              />
            </div>

            <div className="grid gap-1.5">
              <label className="text-sm font-medium text-ink" htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder-ink/35 outline-none focus:border-mint focus:ring-2 focus:ring-mint/20"
                placeholder="you@example.com"
              />
            </div>

            <div className="grid gap-1.5">
              <label className="text-sm font-medium text-ink" htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                required
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder-ink/35 outline-none focus:border-mint focus:ring-2 focus:ring-mint/20"
                placeholder="••••••••"
              />
            </div>

            <Button type="submit" className="mt-2 w-full bg-mint text-white hover:bg-mint/90">
              Start saving smarter →
            </Button>
          </form>

          <p className="mt-4 text-center text-xs text-ink/40">
            By signing up you agree to our Terms. We never sell your data.
          </p>

          <p className="mt-5 text-center text-xs text-ink/45">
            Already have an account?{" "}
            <Link to="/login" className="font-medium text-mint hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>

      {/* Right — value prop */}
      <div className="hidden lg:flex flex-1 flex-col justify-center bg-ink px-16 py-12 text-white">
        <p className="text-sm font-semibold uppercase tracking-wider text-mint mb-6">Why it matters</p>
        <div className="grid gap-5">
          {[
            {
              stat: "80%",
              label: "of supermarket shelf space is dedicated to products outside the Dutch dietary recommendation",
            },
            {
              stat: "€94/mo",
              label: "average Dutch household spend on discretionary food items",
            },
            {
              stat: "€0",
              label: "grocery apps that connect what you eat to what you could build financially — until now",
            },
          ].map(({ stat, label }) => (
            <div key={stat} className="flex gap-4 items-start">
              <span className="text-2xl font-semibold text-mint shrink-0 w-20">{stat}</span>
              <p className="text-sm text-white/60 leading-relaxed">{label}</p>
            </div>
          ))}
        </div>
        <p className="mt-8 text-white/30 text-sm italic">We fix the last one.</p>
      </div>
    </div>
  );
}
