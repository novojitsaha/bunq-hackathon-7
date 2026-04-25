import { Link, NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { BarChart3, CreditCard, Gauge, Goal, Home, LogOut, ReceiptText, ScanLine, Settings } from "lucide-react";

import { Button } from "./components/ui/Button";
import { DashboardPage } from "./pages/DashboardPage";
import { GoalSettingsPage } from "./pages/GoalSettingsPage";
import { InstantSummaryPage } from "./pages/InstantSummaryPage";
import { LandingPage } from "./pages/LandingPage";
import { LoginPage } from "./pages/LoginPage";
import { MonthlySummaryPage } from "./pages/MonthlySummaryPage";
import { ReceiptReviewPage } from "./pages/ReceiptReviewPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ScanUploadPage } from "./pages/ScanUploadPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TransactionsPage } from "./pages/TransactionsPage";
import { auth } from "./lib/auth";
import { cn } from "./lib/utils";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: Home },
  { to: "/monthly", label: "Monthly", icon: BarChart3 },
  { to: "/goals", label: "Goals", icon: Goal },
  { to: "/transactions", label: "Transactions", icon: CreditCard },
  { to: "/settings", label: "Settings", icon: Settings },
];

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!auth.isLoggedIn()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppShell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const user = auth.get();

  function handleLogout() {
    auth.logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-cloud text-ink">
      <header className="sticky top-0 z-20 border-b border-ink/10 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <Link to="/dashboard" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-ink text-white">
              <Gauge size={22} />
            </span>
            <span>
              <span className="block text-sm font-semibold leading-none">Bunq Bite Balance</span>
              <span className="text-xs text-ink/55">
                {user ? `Hi ${user.name.split(" ")[0]}` : "Tracked calories and food spend"}
              </span>
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <Link to="/scan" className="hidden sm:block">
              <Button>
                <ScanLine size={18} />
                Scan receipt
              </Button>
            </Link>
            <Button variant="ghost" onClick={handleLogout} className="hidden sm:inline-flex gap-1.5 text-ink/50 hover:text-ink">
              <LogOut size={16} />
              <span className="sr-only sm:not-sr-only text-xs">Sign out</span>
            </Button>
          </div>
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

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:py-8">{children}</main>

      <Link to="/scan" className="fixed bottom-4 right-4 z-30 sm:hidden" aria-label="Scan receipt">
        <Button className="h-14 w-14 rounded-full p-0 shadow-panel">
          <ReceiptText size={22} />
        </Button>
      </Link>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected — wrapped in AppShell */}
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <AppShell>
              <DashboardPage />
            </AppShell>
          </RequireAuth>
        }
      />
      <Route
        path="/scan"
        element={
          <RequireAuth>
            <AppShell>
              <ScanUploadPage />
            </AppShell>
          </RequireAuth>
        }
      />
      <Route
        path="/receipts/:id/review"
        element={
          <RequireAuth>
            <AppShell>
              <ReceiptReviewPage />
            </AppShell>
          </RequireAuth>
        }
      />
      <Route
        path="/receipts/:id/summary"
        element={
          <RequireAuth>
            <AppShell>
              <InstantSummaryPage />
            </AppShell>
          </RequireAuth>
        }
      />
      <Route
        path="/monthly"
        element={
          <RequireAuth>
            <AppShell>
              <MonthlySummaryPage />
            </AppShell>
          </RequireAuth>
        }
      />
      <Route
        path="/goals"
        element={
          <RequireAuth>
            <AppShell>
              <GoalSettingsPage />
            </AppShell>
          </RequireAuth>
        }
      />
      <Route
        path="/transactions"
        element={
          <RequireAuth>
            <AppShell>
              <TransactionsPage />
            </AppShell>
          </RequireAuth>
        }
      />
      <Route
        path="/settings"
        element={
          <RequireAuth>
            <AppShell>
              <SettingsPage />
            </AppShell>
          </RequireAuth>
        }
      />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
