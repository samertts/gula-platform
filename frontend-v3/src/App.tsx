import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { router } from "@/routes";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { LocaleProvider } from "@/contexts/LocaleContext";
import { ToastContainer } from "@/components/shared/ToastContainer";
import { UpdateGate } from "@/components/shared/UpdateGate";
import { AccessibilityProvider } from "@/contexts/AccessibilityContext";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      staleTime: 30_000,
      gcTime: 600_000,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LocaleProvider>
          <UpdateGate>
            <AuthProvider>
              <AccessibilityProvider>
                <RouterProvider router={router} />
                <ToastContainer />
              </AccessibilityProvider>
            </AuthProvider>
          </UpdateGate>
        </LocaleProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
