export type AuthUser = { name: string; email: string };

const KEY = "bbb_user";

export const auth = {
  get(): AuthUser | null {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? (JSON.parse(raw) as AuthUser) : null;
    } catch {
      return null;
    }
  },
  login(user: AuthUser) {
    localStorage.setItem(KEY, JSON.stringify(user));
  },
  loginDemo() {
    localStorage.setItem(KEY, JSON.stringify({ name: "Demo User", email: "demo@bunq.com" }));
  },
  logout() {
    localStorage.removeItem(KEY);
  },
  isLoggedIn(): boolean {
    return auth.get() !== null;
  },
};
