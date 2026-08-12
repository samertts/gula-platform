import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "./components/ErrorBoundary";
import LabShell from "./components/LabShell";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Orders from "./pages/Orders";
import Patients from "./pages/Patients";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import { Route, Switch } from "wouter";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return <LabShell>{children}</LabShell>;
}

export default function App() {
  return <ErrorBoundary><TooltipProvider><Toaster position="top-center" richColors /><Switch>
    <Route path="/login" component={Login} />
    <Route path="/" component={() => <ProtectedRoute><Dashboard /></ProtectedRoute>} />
    <Route path="/dashboard" component={() => <ProtectedRoute><Dashboard /></ProtectedRoute>} />
    <Route path="/orders" component={() => <ProtectedRoute><Orders /></ProtectedRoute>} />
    <Route path="/patients" component={() => <ProtectedRoute><Patients /></ProtectedRoute>} />
    <Route path="/reports" component={() => <ProtectedRoute><Reports /></ProtectedRoute>} />
    <Route path="/settings" component={() => <ProtectedRoute><Settings /></ProtectedRoute>} />
    <Route component={Login} />
  </Switch></TooltipProvider></ErrorBoundary>;
}
