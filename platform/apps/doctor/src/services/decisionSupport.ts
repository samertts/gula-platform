import { apiRequest } from './api';

export interface DecisionSupportQuery {
  patientId: string;
  query: string;
  context?: {
    symptoms?: string[];
    diagnoses?: string[];
    medications?: string[];
    labResults?: string[];
    vitalSigns?: Record<string, number>;
  };
}

export interface DecisionSupportResult {
  id: string;
  patientId: string;
  query: string;
  summary: string;
  summaryAr: string;
  recommendations: AiRecommendation[];
  differentialDiagnosis: DifferentialDiagnosis[];
  relevantGuidelines: ClinicalGuideline[];
  drugInteractions?: DrugInteractionAlert[];
  riskFactors: RiskFactor[];
  evidenceLevel: 'high' | 'moderate' | 'low' | 'expert_opinion';
  confidence: number;
  createdAt: string;
}

export interface AiRecommendation {
  id: string;
  title: string;
  titleAr: string;
  description: string;
  descriptionAr: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  category: 'diagnosis' | 'medication' | 'test' | 'referral' | 'monitoring' | 'lifestyle';
  evidence: string;
  evidenceAr: string;
  references: string[];
}

export interface DifferentialDiagnosis {
  condition: string;
  conditionAr: string;
  icdCode?: string;
  probability: number;
  supportingFactors: string[];
  supportingFactorsAr: string[];
  rulingOutFactors: string[];
  rulingOutFactorsAr: string[];
}

export interface ClinicalGuideline {
  id: string;
  title: string;
  titleAr: string;
  source: string;
  year: number;
  recommendations: string[];
  recommendationsAr: string[];
  url?: string;
}

export interface DrugInteractionAlert {
  drug1: string;
  drug2: string;
  severity: 'minor' | 'moderate' | 'major' | 'contraindicated';
  description: string;
  descriptionAr: string;
  management: string;
  managementAr: string;
}

export interface RiskFactor {
  factor: string;
  factorAr: string;
  risk: 'low' | 'moderate' | 'high' | 'very_high';
  description: string;
  descriptionAr: string;
  mitigations: string[];
  mitigationsAr: string[];
}

export interface ExplainableResult {
  queryId: string;
  explanation: string;
  explanationAr: string;
  reasoning: string;
  reasoningAr: string;
  dataSources: string[];
  limitations: string[];
  confidenceBreakdown: {
    factor: string;
    weight: number;
  }[];
}

export async function queryDecisionSupport(query: DecisionSupportQuery): Promise<DecisionSupportResult> {
  return apiRequest<DecisionSupportResult>('/decision-support/query', {
    method: 'POST',
    body: JSON.stringify(query),
    offlinePriority: 'high',
  });
}

export async function getDecisionHistory(patientId: string): Promise<DecisionSupportResult[]> {
  return apiRequest<DecisionSupportResult[]>(`/decision-support/history/${patientId}`);
}

export async function getExplainableResult(queryId: string): Promise<ExplainableResult> {
  return apiRequest<ExplainableResult>(`/decision-support/explain/${queryId}`);
}

export async function provideFeedback(
  queryId: string,
  feedback: {
    helpful: boolean;
    accurate: boolean;
    comments?: string;
  },
): Promise<void> {
  return apiRequest(`/decision-support/feedback/${queryId}`, {
    method: 'POST',
    body: JSON.stringify(feedback),
  });
}

export async function getClinicalGuidelines(
  condition?: string,
): Promise<ClinicalGuideline[]> {
  const query = condition ? `?condition=${encodeURIComponent(condition)}` : '';
  return apiRequest<ClinicalGuideline[]>(`/clinical-guidelines${query}`);
}
