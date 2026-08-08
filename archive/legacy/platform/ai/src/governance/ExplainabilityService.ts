export enum ExplanationType {
  ShapValues = 'shap_values',
  LimeValues = 'lime_values',
  FeatureImportance = 'feature_importance',
  DecisionPath = 'decision_path',
  RuleBased = 'rule_based',
  Counterfactual = 'counterfactual',
}

export interface FeatureContribution {
  featureName: string;
  featureValue: number | string | boolean;
  contribution: number;
  direction: 'positive' | 'negative' | 'neutral';
  importance: number;
}

export interface DecisionNode {
  id: string;
  rule: string;
  feature: string;
  threshold: number | string;
  decision: string;
  confidence: number;
  children: DecisionNode[];
  parentId: string | null;
}

export interface DecisionPath {
  nodes: DecisionNode[];
  finalDecision: string;
  pathConfidence: number;
  alternativePaths: DecisionNode[][];
}

export interface ExplanationResult {
  type: ExplanationType;
  modelName: string;
  modelVersion: string;
  inputSummary: Record<string, unknown>;
  prediction: unknown;
  confidence: number;
  featureContributions: FeatureContribution[];
  decisionPath?: DecisionPath;
  humanReadable: {
    ar: string;
    en: string;
  };
  generatedAt: Date;
  computationTimeMs: number;
}

export interface ConfidenceScore {
  overall: number;
  components: {
    modelConfidence: number;
    dataQuality: number;
    featureCoverage: number;
    historicalAccuracy: number;
  };
  level: 'very_high' | 'high' | 'medium' | 'low' | 'very_low';
}

export interface CounterfactualExplanation {
  originalInput: Record<string, unknown>;
  counterfactualInput: Record<string, unknown>;
  originalPrediction: unknown;
  counterfactualPrediction: unknown;
  changes: { feature: string; from: unknown; to: unknown }[];
  minimalChanges: boolean;
}

export interface ExplanationConfig {
  defaultType: ExplanationType;
  maxFeatures: number;
  includeDecisionPath: boolean;
  generateCounterfactuals: boolean;
  locale: 'ar' | 'en' | 'both';
}

export class ExplainabilityService {
  private config: ExplanationConfig;

  constructor(config: Partial<ExplanationConfig> = {}) {
    this.config = {
      defaultType: ExplanationType.FeatureImportance,
      maxFeatures: 20,
      includeDecisionPath: true,
      generateCounterfactuals: false,
      locale: 'both',
      ...config,
    };
  }

  async explain(
    modelName: string,
    modelVersion: string,
    input: Record<string, unknown>,
    prediction: unknown,
    confidence: number,
    type: ExplanationType = this.config.defaultType,
  ): Promise<ExplanationResult> {
    const startTime = Date.now();
    const featureContributions = this.computeFeatureContributions(input, confidence);
    const decisionPath = this.config.includeDecisionPath
      ? this.buildDecisionPath(featureContributions, prediction, confidence)
      : undefined;

    const result: ExplanationResult = {
      type,
      modelName,
      modelVersion,
      inputSummary: this.summarizeInput(input),
      prediction,
      confidence,
      featureContributions,
      decisionPath,
      humanReadable: this.generateHumanReadable(
        modelName,
        featureContributions,
        prediction,
        confidence,
      ),
      generatedAt: new Date(),
      computationTimeMs: Date.now() - startTime,
    };

    return result;
  }

  computeConfidenceScore(
    modelConfidence: number,
    dataQuality: number,
    featureCoverage: number,
    historicalAccuracy: number,
  ): ConfidenceScore {
    const overall =
      modelConfidence * 0.4 +
      dataQuality * 0.2 +
      featureCoverage * 0.2 +
      historicalAccuracy * 0.2;

    let level: ConfidenceScore['level'];
    if (overall >= 0.9) level = 'very_high';
    else if (overall >= 0.7) level = 'high';
    else if (overall >= 0.5) level = 'medium';
    else if (overall >= 0.3) level = 'low';
    else level = 'very_low';

    return {
      overall: Math.round(overall * 100) / 100,
      components: { modelConfidence, dataQuality, featureCoverage, historicalAccuracy },
      level,
    };
  }

  private computeFeatureContributions(
    input: Record<string, unknown>,
    confidence: number,
  ): FeatureContribution[] {
    const contributions: FeatureContribution[] = [];
    const entries = Object.entries(input).slice(0, this.config.maxFeatures);
    const baseContribution = (confidence - 0.5) * 2;

    for (const [key, value] of entries) {
      const numericValue = typeof value === 'number' ? value : 0;
      const contribution = baseContribution * (numericValue / (Math.abs(numericValue) + 1));
      const direction: FeatureContribution['direction'] =
        contribution > 0.01 ? 'positive' : contribution < -0.01 ? 'negative' : 'neutral';
      const importance = Math.abs(contribution) / entries.length;

      contributions.push({
        featureName: key,
        featureValue: value,
        contribution: Math.round(contribution * 1000) / 1000,
        direction,
        importance: Math.round(importance * 1000) / 1000,
      });
    }

    return contributions.sort((a, b) => b.importance - a.importance);
  }

  private buildDecisionPath(
    contributions: FeatureContribution[],
    prediction: unknown,
    confidence: number,
  ): DecisionPath {
    const rootNode: DecisionNode = {
      id: 'root',
      rule: `confidence >= ${Math.round(confidence * 100)}%`,
      feature: 'aggregate',
      threshold: 0.5,
      decision: String(prediction),
      confidence,
      children: [],
      parentId: null,
    };

    const children: DecisionNode[] = contributions
      .filter((c) => c.importance > 0.1)
      .map((c, i) => ({
        id: `node_${i}`,
        rule: `${c.featureName} contributes ${c.direction === 'positive' ? '+' : ''}${c.contribution}`,
        feature: c.featureName,
        threshold: typeof c.featureValue === 'number' ? c.featureValue : 0,
        decision: c.direction,
        confidence: Math.abs(c.contribution),
        children: [],
        parentId: 'root',
      }));

    rootNode.children = children;

    return {
      nodes: [rootNode, ...children],
      finalDecision: String(prediction),
      pathConfidence: confidence,
      alternativePaths: [],
    };
  }

  async generateCounterfactual(
    input: Record<string, unknown>,
    originalPrediction: unknown,
    modelPredictFn: (input: Record<string, unknown>) => Promise<unknown>,
    maxIterations: number = 100,
  ): Promise<CounterfactualExplanation> {
    const counterfactualInput = { ...input };
    const changes: CounterfactualExplanation['changes'] = [];
    const numericKeys = Object.entries(counterfactualInput).filter(
      ([, v]) => typeof v === 'number',
    );

    for (let i = 0; i < Math.min(numericKeys.length, maxIterations); i++) {
      const [key, originalValue] = numericKeys[i];
      const step = typeof originalValue === 'number' ? originalValue * 0.1 || 1 : 1;
      const newValue = (originalValue as number) + step;
      counterfactualInput[key] = newValue;

      try {
        const newPrediction = await modelPredictFn(counterfactualInput);
        if (String(newPrediction) !== String(originalPrediction)) {
          changes.push({
            feature: key,
            from: originalValue,
            to: newValue,
          });
        }
      } catch {
        counterfactualInput[key] = originalValue;
      }
    }

    const counterfactualPrediction = changes.length
      ? await modelPredictFn(counterfactualInput).catch(() => originalPrediction)
      : originalPrediction;

    return {
      originalInput: input,
      counterfactualInput,
      originalPrediction,
      counterfactualPrediction,
      changes,
      minimalChanges: changes.length <= 3,
    };
  }

  private summarizeInput(input: Record<string, unknown>): Record<string, unknown> {
    const summary: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(input)) {
      if (typeof value === 'string' && value.length > 100) {
        summary[key] = value.substring(0, 100) + '...';
      } else if (Array.isArray(value) && value.length > 10) {
        summary[key] = `[${value.length} items]`;
      } else {
        summary[key] = value;
      }
    }
    return summary;
  }

  private generateHumanReadable(
    modelName: string,
    contributions: FeatureContribution[],
    prediction: unknown,
    confidence: number,
  ): { ar: string; en: string } {
    const topFeatures = contributions.slice(0, 5);

    const en = `The model "${modelName}" made the prediction "${String(prediction)}" with ${Math.round(confidence * 100)}% confidence. ` +
      `The top factors influencing this decision were: ${topFeatures.map(
        (f) => `${f.featureName} (${f.direction} contribution: ${f.contribution})`,
      ).join(', ')}.`;

    const ar = `النموذج "${modelName}" أصدر التنبؤ "${String(prediction)}" بثقة ${Math.round(confidence * 100)}%. ` +
      `أهم العوامل المؤثرة في هذا القرار: ${topFeatures.map(
        (f) => `${f.featureName} (تأثير ${f.direction === 'positive' ? 'إيجابي' : f.direction === 'negative' ? 'سلبي' : 'محايد'}: ${f.contribution})`,
      ).join('، ')}.`;

    return { ar, en };
  }
}
