import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui/Button";
import { AlertTriangle } from "lucide-react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console -- error boundary must surface render errors to the console
    console.error("Unhandled render error:", error, info.componentStack);
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, message: "" });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-6 text-center"
          role="alert"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10">
            <AlertTriangle className="h-7 w-7 text-destructive" />
          </div>
          <div>
            <h2 className="text-lg font-bold">حدث خطأ غير متوقع</h2>
            <p className="mt-1 max-w-md text-sm text-muted-foreground">
              {this.state.message || "تعذر عرض هذه الصفحة حالياً"}
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={this.handleRetry}>إعادة المحاولة</Button>
            <Button variant="outline" onClick={() => window.location.assign("/dashboard")}>
              الصفحة الرئيسية
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
