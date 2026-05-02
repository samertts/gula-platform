import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || '' });

export const generateSmartDiagnosis = async (patientData: string, symptoms: string) => {
  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `You are a specialized medical intelligence assistant. Analyze the following patient data and reported symptoms to provide clinical insights, possible differential diagnoses, and recommended next steps for the physician. 
      
      Patient Data: ${patientData}
      Symptoms: ${symptoms}
      
      Output should be professional, structured, and prioritize urgent findings. Always include a disclaimer that this is a decision support tool and not a final diagnosis.`,
    });
    
    return response.text;
  } catch (error) {
    console.error("Gemini Error:", error);
    return "Error generating AI insight. Please try again later.";
  }
};

export const analyzeLabTrends = async (labResults: any[]) => {
  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `Analyze these laboratory results for potential clinical trends or anomalies. Provide a summary of significant changes over time.
      
      Results: ${JSON.stringify(labResults)}
      
      At the end of your response, provide 3 suggested follow-up questions that a physician might want to ask. Format them exactly like this:
      ---
      SUGGESTED_QUESTIONS:
      - [Question 1]
      - [Question 2]
      - [Question 3]`,
    });
    
    return response.text;
  } catch (error) {
    console.error("Gemini Error:", error);
    return "Trend analysis unavailable.";
  }
};

export const askFollowUp = async (context: string, question: string) => {
  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: `You are a clinical intelligence assistant. You previously provided an analysis:
      "${context}"
      
      The user (a medical professional) has a follow-up question:
      "${question}"
      
      Provide a concise, professional answer based on clinical evidence and the current context.
      
      At the end of your response, provide 2 or 3 NEW suggested follow-up questions. Format them exactly like this:
      ---
      SUGGESTED_QUESTIONS:
      - [Question 1]
      - [Question 2]
      - [Question 3]`,
    });
    
    return response.text;
  } catch (error) {
    console.error("Gemini Error:", error);
    return "Error generating response to follow-up question.";
  }
};
