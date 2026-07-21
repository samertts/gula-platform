import type { AxiosError } from "axios";
import { useToast } from "./useToast";

export function useApiError() {
  const { toast } = useToast();

  const handleError = (err: AxiosError<{ detail?: string }>, fallback?: string) => {
    const message =
      err.response?.data?.detail ||
      err.message ||
      fallback ||
      "حدث خطأ غير متوقع";
    toast({ variant: "destructive", title: "خطأ", description: message });
    return message;
  };

  return { handleError };
}
