import { create } from "zustand";

export interface AuthUser {
  id:    string;
  name:  string;
  email: string;
  role:  "admin" | "lab_staff" | "doctor" | "patient" | "citizen";
}

interface AuthStore {
  user:     AuthUser | null;
  token:    string | null;
  setAuth:  (user: AuthUser, token: string) => void;
  logout:   () => void;
  isRole:   (...roles: string[]) => boolean;
}

/* hydrate from localStorage */
function loadUser(): AuthUser | null {
  try { return JSON.parse(localStorage.getItem("nhop_user") || "null"); }
  catch { return null; }
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user:  loadUser(),
  token: localStorage.getItem("nhop_token"),

  setAuth(user, token) {
    localStorage.setItem("nhop_token", token);
    localStorage.setItem("nhop_user", JSON.stringify(user));
    set({ user, token });
  },

  logout() {
    localStorage.removeItem("nhop_token");
    localStorage.removeItem("nhop_user");
    set({ user: null, token: null });
  },

  isRole(...roles) {
    const u = get().user;
    return !!u && roles.includes(u.role);
  },
}));
