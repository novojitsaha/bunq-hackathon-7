import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Gauge } from "lucide-react";

import { Button } from "../components/ui/Button";
import { auth } from "../lib/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [forgotToast, setForgotToast] = useState(false);

  if (auth.isLoggedIn()) return <Navigate to="/dashboard" replace />;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    auth.login({ name: email.split("@")[0], email });
    navigate("/dashboard");
  }

  function handleDemo() {
    auth.loginDemo();
    navigate("/dashboard");
  }

  function handleForgot(e: React.MouseEvent) {
    e.preventDefault();
    setForgotToast(true);
    setTimeout(() => setForgotToast(false), 3000);
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

          <h1 className="text-2xl font-semibold text-ink">Welcome back</h1>
          <p className="mt-1 text-sm text-ink/55">Sign in to see your grocery insights</p>

          <form onSubmit={handleSubmit} className="mt-8 grid gap-4">
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
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-ink" htmlFor="password">Password</label>
                <a href="#" onClick={handleForgot} className="text-xs text-mint hover:underline">
                  Forgot password?
                </a>
              </div>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder-ink/35 outline-none focus:border-mint focus:ring-2 focus:ring-mint/20"
                placeholder="••••••••"
              />
            </div>

            <Button type="submit" className="mt-2 w-full bg-mint text-white hover:bg-mint/90">
              Sign in →
            </Button>
          </form>

          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-ink/10" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-white px-3 text-xs text-ink/40">or</span>
            </div>
          </div>

          <Button
            type="button"
            variant="secondary"
            onClick={handleDemo}
            className="w-full"
          >
            Try the demo →
          </Button>

          <p className="mt-6 text-center text-xs text-ink/45">
            No account?{" "}
            <Link to="/register" className="font-medium text-mint hover:underline">
              Sign up free
            </Link>
          </p>
        </div>
      </div>

      {/* Right — value prop */}
      <div className="hidden lg:flex flex-1 flex-col justify-center bg-ink px-16 py-12 text-white">
        <p className="text-4xl font-semibold leading-tight">
          The average Dutch household spends{" "}
          <span className="text-mint">€94/month</span> on items outside the Schijf van Vijf.
        </p>
        <p className="mt-4 text-lg text-white/60">
          That's <span className="text-white font-semibold">€18,800 in 20 years</span> — compounding at 5%.
        </p>
        <div className="mt-10 rounded-xl bg-white/8 border border-white/10 p-6">
          <p className="text-sm text-white/50 mb-3">Your discretionary spend, visualised</p>
          <div className="grid grid-cols-3 gap-4 text-center">
            {[
              { label: "1 year", value: "€1,222" },
              { label: "5 years", value: "€6,558" },
              { label: "10 years", value: "€14,629" },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-lg bg-white/5 p-3">
                <p className="text-xl font-semibold text-mint">{value}</p>
                <p className="mt-1 text-xs text-white/45">{label} at 5%</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {forgotToast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-ink px-5 py-3 text-sm text-white shadow-panel">
          Password reset link sent (demo mode — check your inbox)
        </div>
      )}
    </div>
  );
}
