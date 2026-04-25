import { Link, NavLink, Route, Routes } from "react-router-dom";
import { BarChart3, CreditCard, Gauge, Goal, Home, ReceiptText, ScanLine, Settings } from "lucide-react";

import { Button } from "./components/ui/Button";
import { DashboardPage } from "./pages/DashboardPage";
import { GoalSettingsPage } from "./pages/GoalSettingsPage";
import { InstantSummaryPage } from "./pages/InstantSummaryPage";
import { MonthlySummaryPage } from "./pages/MonthlySummaryPage";
import { ReceiptReviewPage } from "./pages/ReceiptReviewPage";
import { ScanUploadPage } from "./pages/ScanUploadPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TransactionsPage } from "./pages/TransactionsPage";
import { cn } from "./lib/utils";

const nav = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/monthly", label: "Monthly", icon: BarChart3 },
  { to: "/goals", label: "Goals", icon: Goal },
  { to: "/transactions", label: "Transactions", icon: CreditCard },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function App() {
  return (
    <div className="min-h-screen bg-cloud text-ink">
      <header className="sticky top-0 z-20 border-b border-ink/10 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-ink text-white">
              <Gauge size={22} />
            </span>
            <span>
              <span className="block text-sm font-semibold leading-none">Bunq Bite Balance</span>
              <span className="text-xs text-ink/55">Tracked calories and food spend</span>
            </span>
          </Link>
          <Link to="/scan" className="hidden sm:block">
            <Button>
              <ScanLine size={18} />
              Scan receipt
            </Button>
          </Link>
        </div>
        <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 pb-3 sm:px-6">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-ink/65 transition hover:bg-ink/5 hover:text-ink",
                  isActive && "bg-ink text-white hover:bg-ink hover:text-white",
                )
              }
            >
              <item.icon size={16} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:py-8">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/scan" element={<ScanUploadPage />} />
          <Route path="/receipts/:id/review" element={<ReceiptReviewPage />} />
          <Route path="/receipts/:id/summary" element={<InstantSummaryPage />} />
          <Route path="/monthly" element={<MonthlySummaryPage />} />
          <Route path="/goals" element={<GoalSettingsPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>

      <Link to="/scan" className="fixed bottom-4 right-4 z-30 sm:hidden" aria-label="Scan receipt">
        <Button className="h-14 w-14 rounded-full p-0 shadow-panel">
          <ReceiptText size={22} />
        </Button>
      </Link>
    </div>
  );
}

