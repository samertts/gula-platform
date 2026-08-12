import { apiPost } from "../api/client";

type AiGatewayResponse = {
  response?: unknown;
  rag_response?: unknown;
  answer?: unknown;
  output?: unknown;
  text?: unknown;
};

export async function getClinicalInsight(prompt: string, context: string, imageData?: string) {
  if (imageData) {
    return "Image-based clinical insight is temporarily unavailable while the secure upload gateway is being configured.";
  }

  try {
    const data = await apiPost<AiGatewayResponse>("/ai/v2/orchestrate", {
      query: [
        "You are GULA AI, a clinical decision support assistant.",
        "Provide evidence-based, precise, and professional insights for physicians and lab technicians.",
        "Use the supplied context, maintain clinical rigor, and include a cautious disclaimer.",
        "Supported languages: Arabic, English, Kurdish, Turkmen, Syriac.",
        "Context:",
        context,
        "Question:",
        prompt,
      ].join("\n\n"),
    });
    const candidate = data?.response ?? data?.rag_response ?? data?.answer ?? data?.output ?? data?.text;
    return typeof candidate === "string" && candidate.trim()
      ? candidate
      : "Clinical insight is currently unavailable. Please try again later.";
  } catch (error) {
    console.error("Clinical insight gateway request failed:", error);
    return "I'm sorry, the clinical insight service is currently unavailable.";
  }
}
