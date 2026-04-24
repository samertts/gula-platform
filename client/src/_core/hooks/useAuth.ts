export interface AuthState {
  user: { id: string; name: string; role: string } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export function useAuth(): AuthState {
  return {
    user: null,
    isAuthenticated: false,
    isLoading: false,
  };
}

export default useAuth;
