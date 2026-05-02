import { GoogleGenAI, GenerateContentResponse } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

export async function getClinicalInsight(prompt: string, context: string, imageData?: string) {
  try {
    const contents: any[] = [];
    
    if (imageData) {
      // Remove data:image/xxx;base64, prefix if present
      const base64Data = imageData.split(',')[1] || imageData;
      contents.push({
        parts: [
          {
            inlineData: {
              mimeType: "image/jpeg",
              data: base64Data
            }
          },
          { text: `Context: ${context}\n\nQuestion: ${prompt}` }
        ]
      });
    } else {
      contents.push({
        parts: [{ text: `Context: ${context}\n\nQuestion: ${prompt}` }]
      });
    }

    const response: GenerateContentResponse = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: contents[0].parts ? contents[0] : contents,
      config: {
        systemInstruction: `You are GULA AI, a highly advanced clinical decision support system. 
        Your goal is to provide evidence-based, precise, and professional insights to physicians and lab technicians.
        
        GULA Vision Capability:
        When an image (like a lab report or medical document) is provided, your first priority is to extract key clinical data (values, units, ranges, flags) and then provide analysis.
        
        Always maintain clinical rigor. Use provided context (patient data, lab values) to ground your answers.
        If a user asks for personal health advice in the Citizen Wing, provide empathetic but cautious guidance, always recommending professional consultation.
        Supported languages: Arabic, English, Kurdish, Turkmen, Syriac. Reply in the language of the prompt.`,
        temperature: 0.1,
      },
    });

    return response.text;
  } catch (error) {
    console.error("Clinical Insight Error:", error);
    return "I'm sorry, I'm experiencing a technical issue analyzing this clinical data.";
  }
}
