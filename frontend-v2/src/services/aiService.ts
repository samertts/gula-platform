import { apiPost } from "../api/client";

type AiGatewayResponse = {
  response?: unknown;
  rag_response?: unknown;
  answer?: unknown;
  output?: unknown;
  text?: unknown;
};

async function queryAiGateway(prompt: string, fallback: string): Promise<string> {
  try {
    const data = await apiPost<AiGatewayResponse>("/ai/v2/orchestrate", {
      query: prompt,
    });
    const candidate = data?.response ?? data?.rag_response ?? data?.answer ?? data?.output ?? data?.text;
    return typeof candidate === "string" && candidate.trim() ? candidate : fallback;
  } catch (error) {
    console.error("AI gateway request failed:", error);
    return fallback;
  }
}

export const generateSmartDiagnosis = async (patientData: string, symptoms: string) =>
  queryAiGateway(
    [
      "You are a specialized medical intelligence assistant.",
      "Analyze the following patient data and reported symptoms to provide clinical insights, possible differential diagnoses, and recommended next steps for the physician.",
      "Patient Data:",
      patientData,
      "Symptoms:",
      symptoms,
      "Output should be professional, structured, prioritize urgent findings, and include a disclaimer that this is decision support rather than a final diagnosis.",
    ].join("\n\n"),
    "AI insight is currently unavailable. Please try again later.",
  );

export const analyzeLabTrends = async (labResults: unknown[]) =>
  queryAiGateway(
    [
      "Analyze these laboratory results for potential clinical trends or anomalies.",
      "Provide a summary of significant changes over time.",
      `Results: ${JSON.stringify(labResults)}`,
      "At the end, provide 3 suggested follow-up questions using the SUGGESTED_QUESTIONS format.",
    ].join("\n\n"),
    "Trend analysis is currently unavailable. Please try again later.",
  );

export const askFollowUp = async (context: string, question: string) =>
  queryAiGateway(
    [
      "You are a clinical intelligence assistant.",
      "Previous analysis:",
      context,
      "Follow-up question:",
      question,
      "Provide a concise, professional answer based on clinical evidence and the current context.",
      "At the end, provide 2 or 3 new suggested follow-up questions using the SUGGESTED_QUESTIONS format.",
    ].join("\n\n"),
    "The follow-up response is currently unavailable. Please try again later.",
  );
