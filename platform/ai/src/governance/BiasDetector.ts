export enum BiasType {
  Demographic = 'demographic',
  Selection = 'selection',
  Measurement = 'measurement',
  Confirmation = 'confirmation',
  Labeling = 'labeling',
  Algorithmic = 'algorithmic',
}

export enum ProtectedAttribute {
  Age = 'age',
  Gender = 'gender',
  Ethnicity = 'ethnicity',
  Socioeconomic = 'socioeconomic',
  Region = 'region',
  Disability = 'disability',
}

export interface BiasResult {
  type: BiasType;
  attribute: ProtectedAttribute;
  severity: 'low' | 'medium' | 'high' | 'critical';
  score: number;
  description: string;
  affectedGroups: string[];
  statisticalSignificance: number;
  mitigationSuggestions: string[];
  timestamp: Date;
}

export interface DemographicParityResult {
  attribute: ProtectedAttribute;
  groups: { name: string; positiveRate: number; sampleSize: number }[];
  maxDisparity: number;
  parityThreshold: number;
  passesParity: boolean;
  description: string;
}

export interface EqualOpportunityResult {
  attribute: ProtectedAttribute;
  groups: { name: string; truePositiveRate: number; falsePositiveRate: number }[];
  maxTPRDisparity: number;
  maxFPRDisparity: number;
  threshold: number;
  passesCheck: boolean;
}

export interface DisparateImpactResult {
  attribute: ProtectedAttribute;
  impactRatio: number;
  threshold: number;
  adverseImpact: 'none' | 'moderate' | 'significant';
  groups: { name: string; selectionRate: number; impactRatio: number }[];
}

export interface BiasMitigationSuggestion {
  type: string;
  description: string;
  expectedImprovement: number;
  implementationDifficulty: 'easy' | 'moderate' | 'difficult';
  affectedBiasType: BiasType;
}

export interface DatasetBiasAnalysis {
  datasetName: string;
  totalSamples: number;
  protectedAttributes: ProtectedAttribute[];
  results: BiasResult[];
  overallBiasScore: number;
  timestamp: Date;
}

export interface ModelPredictionBiasAnalysis {
  modelName: string;
  modelVersion: string;
  results: BiasResult[];
  demographicParity: DemographicParityResult[];
  equalOpportunity: EqualOpportunityResult[];
  disparateImpact: DisparateImpactResult[];
  overallBiasScore: number;
  timestamp: Date;
}

export class BiasDetector {
  private readonly DISPARATE_IMPACT_THRESHOLD = 0.8;
  private readonly DEMOGRAPHIC_PARITY_THRESHOLD = 0.1;
  private readonly EQUAL_OPPORTUNITY_THRESHOLD = 0.05;

  analyzeDataset(
    datasetName: string,
    data: Record<string, unknown>[],
    protectedAttributes: ProtectedAttribute[],
  ): DatasetBiasAnalysis {
    const results: BiasResult[] = [];

    for (const attr of protectedAttributes) {
      const attrResults = this.detectDatasetBias(data, attr);
      results.push(...attrResults);
    }

    const overallBiasScore = this.computeOverallScore(results);

    return {
      datasetName,
      totalSamples: data.length,
      protectedAttributes,
      results,
      overallBiasScore,
      timestamp: new Date(),
    };
  }

  analyzePredictions(
    modelName: string,
    modelVersion: string,
    predictions: { input: Record<string, unknown>; prediction: unknown; actual?: unknown }[],
    protectedAttributes: ProtectedAttribute[],
  ): ModelPredictionBiasAnalysis {
    const results: BiasResult[] = [];
    const demographicParity: DemographicParityResult[] = [];
    const equalOpportunity: EqualOpportunityResult[] = [];
    const disparateImpact: DisparateImpactResult[] = [];

    for (const attr of protectedAttributes) {
      const biasResults = this.detectPredictionBias(predictions, attr);
      results.push(...biasResults);
      demographicParity.push(this.checkDemographicParity(predictions, attr));
      equalOpportunity.push(this.checkEqualOpportunity(predictions, attr));
      disparateImpact.push(this.calculateDisparateImpact(predictions, attr));
    }

    const overallBiasScore = this.computeOverallScore(results);

    return {
      modelName,
      modelVersion,
      results,
      demographicParity,
      equalOpportunity,
      disparateImpact,
      overallBiasScore,
      timestamp: new Date(),
    };
  }

  generateMitigationSuggestions(biasResults: BiasResult[]): BiasMitigationSuggestion[] {
    const suggestions: BiasMitigationSuggestion[] = [];
    const biasTypesPresent = [...new Set(biasResults.map((r) => r.type))];
    const highSeverity = biasResults.filter(
      (r) => r.severity === 'high' || r.severity === 'critical',
    );

    if (highSeverity.length > 0) {
      suggestions.push({
        type: 'reweighting',
        description: 'Apply instance reweighting to balance the influence of under-represented groups in training data',
        expectedImprovement: 0.3,
        implementationDifficulty: 'moderate',
        affectedBiasType: BiasType.Demographic,
      });
    }

    if (biasTypesPresent.includes(BiasType.Demographic)) {
      suggestions.push(
        {
          type: 'adversarial_debiasing',
          description: 'Train an adversarial network to remove protected attribute information from learned representations',
          expectedImprovement: 0.4,
          implementationDifficulty: 'difficult',
          affectedBiasType: BiasType.Demographic,
        },
        {
          type: 'data_augmentation',
          description: 'Augment training data to ensure balanced representation across demographic groups',
          expectedImprovement: 0.25,
          implementationDifficulty: 'easy',
          affectedBiasType: BiasType.Demographic,
        },
      );
    }

    if (biasTypesPresent.includes(BiasType.Selection)) {
      suggestions.push({
        type: 'sample_weighting',
        description: 'Adjust sample weights to correct for selection bias in the training dataset',
        expectedImprovement: 0.35,
        implementationDifficulty: 'moderate',
        affectedBiasType: BiasType.Selection,
      });
    }

    if (biasTypesPresent.includes(BiasType.Labeling)) {
      suggestions.push({
        type: 'label_audit',
        description: 'Conduct an independent audit of training labels to identify and correct biased labeling patterns',
        expectedImprovement: 0.5,
        implementationDifficulty: 'moderate',
        affectedBiasType: BiasType.Labeling,
      });
    }

    suggestions.push({
      type: 'fairness_constraint',
      description: 'Add fairness constraints to the model optimization objective to enforce equal treatment',
      expectedImprovement: 0.2,
      implementationDifficulty: 'moderate',
      affectedBiasType: BiasType.Algorithmic,
    });

    return suggestions;
  }

  private detectDatasetBias(
    data: Record<string, unknown>[],
    attribute: ProtectedAttribute,
  ): BiasResult[] {
    const results: BiasResult[] = [];
    const groups = this.groupByAttribute(data, attribute);
    const groupSizes = Object.entries(groups).map(([name, records]) => ({
      name,
      count: records.length,
    }));

    const maxCount = Math.max(...groupSizes.map((g) => g.count));
    const minCount = Math.min(...groupSizes.map((g) => g.count));

    if (groupSizes.length >= 2) {
      const ratio = minCount / maxCount;
      const severity: BiasResult['severity'] =
        ratio < 0.1 ? 'critical' : ratio < 0.3 ? 'high' : ratio < 0.5 ? 'medium' : 'low';

      const smallestGroup = groupSizes.find((g) => g.count === minCount);
      const largestGroup = groupSizes.find((g) => g.count === maxCount);

      results.push({
        type: BiasType.Demographic,
        attribute,
        severity,
        score: 1 - ratio,
        description: [
          'Group representation imbalance: ',
          'smallest group (', smallestGroup?.name, ') has ', minCount,
          ' samples vs largest (', largestGroup?.name, ') has ', maxCount,
          ' samples (ratio: ', ratio.toFixed(2), ')',
        ].join(''),
        affectedGroups: groupSizes
          .filter((g) => g.count < maxCount * 0.5)
          .map((g) => g.name),
        statisticalSignificance: this.computeSignificance(groupSizes),
        mitigationSuggestions: this.getDefaultMitigations(attribute),
        timestamp: new Date(),
      });
    }

    return results;
  }

  private detectPredictionBias(
    predictions: { input: Record<string, unknown>; prediction: unknown; actual?: unknown }[],
    attribute: ProtectedAttribute,
  ): BiasResult[] {
    const results: BiasResult[] = [];
    const groups = this.groupPredictionsByAttribute(predictions, attribute);

    const positiveRates: { name: string; rate: number }[] = [];
    for (const [name, preds] of Object.entries(groups)) {
      const positive = preds.filter(
        (p) => String(p.prediction) === 'true' || p.prediction === 1,
      ).length;
      positiveRates.push({
        name,
        rate: preds.length > 0 ? positive / preds.length : 0,
      });
    }

    if (positiveRates.length >= 2) {
      const maxRate = Math.max(...positiveRates.map((r) => r.rate));
      const minRate = Math.min(...positiveRates.map((r) => r.rate));
      const disparity = maxRate - minRate;

      const severity: BiasResult['severity'] =
        disparity > 0.3
          ? 'critical'
          : disparity > 0.2
            ? 'high'
            : disparity > 0.1
              ? 'medium'
              : 'low';

      const highestGroup = positiveRates.find((r) => r.rate === maxRate);
      const lowestGroup = positiveRates.find((r) => r.rate === minRate);

      results.push({
        type: BiasType.Algorithmic,
        attribute,
        severity,
        score: disparity,
        description: [
          'Prediction rate disparity of ',
          (disparity * 100).toFixed(1), '% between groups. ',
          'Highest: ', highestGroup?.name, ' (', (maxRate * 100).toFixed(1), '%), ',
          'Lowest: ', lowestGroup?.name, ' (', (minRate * 100).toFixed(1), '%)',
        ].join(''),
        affectedGroups: positiveRates
          .filter((r) => r.rate < maxRate * 0.8)
          .map((r) => r.name),
        statisticalSignificance: 0.95,
        mitigationSuggestions: this.getDefaultMitigations(attribute),
        timestamp: new Date(),
      });
    }

    return results;
  }

  private checkDemographicParity(
    predictions: { input: Record<string, unknown>; prediction: unknown }[],
    attribute: ProtectedAttribute,
  ): DemographicParityResult {
    const groups = this.groupPredictionsByAttribute(predictions, attribute);
    const groupResults = Object.entries(groups).map(([name, preds]) => {
      const positive = preds.filter(
        (p) => p.prediction === 1 || p.prediction === true,
      ).length;
      return {
        name,
        positiveRate: preds.length > 0 ? positive / preds.length : 0,
        sampleSize: preds.length,
      };
    });

    const rates = groupResults.map((g) => g.positiveRate);
    const maxDisparity = Math.max(...rates) - Math.min(...rates);

    return {
      attribute,
      groups: groupResults,
      maxDisparity,
      parityThreshold: this.DEMOGRAPHIC_PARITY_THRESHOLD,
      passesParity: maxDisparity <= this.DEMOGRAPHIC_PARITY_THRESHOLD,
      description:
        maxDisparity <= this.DEMOGRAPHIC_PARITY_THRESHOLD
          ? [
              'Demographic parity satisfied (max disparity ',
              (maxDisparity * 100).toFixed(1), '% <= ',
              (this.DEMOGRAPHIC_PARITY_THRESHOLD * 100).toFixed(1), '%)',
            ].join('')
          : [
              'Demographic parity violated (max disparity ',
              (maxDisparity * 100).toFixed(1), '% > ',
              (this.DEMOGRAPHIC_PARITY_THRESHOLD * 100).toFixed(1), '%)',
            ].join(''),
    };
  }

  private checkEqualOpportunity(
    predictions: { input: Record<string, unknown>; prediction: unknown; actual?: unknown }[],
    attribute: ProtectedAttribute,
  ): EqualOpportunityResult {
    const groups = this.groupPredictionsByAttribute(predictions, attribute);
    const withActual = predictions.filter((p) => p.actual !== undefined);

    const groupResults = Object.entries(groups).map(([name, preds]) => {
      const withLabels = preds.filter((p) => p.actual !== undefined);
      const truePositives = withLabels.filter(
        (p) => p.prediction === 1 && p.actual === 1,
      ).length;
      const falsePositives = withLabels.filter(
        (p) => p.prediction === 1 && p.actual === 0,
      ).length;
      const actualPositives = withLabels.filter((p) => p.actual === 1).length;
      const actualNegatives = withLabels.filter((p) => p.actual === 0).length;

      return {
        name,
        truePositiveRate: actualPositives > 0 ? truePositives / actualPositives : 0,
        falsePositiveRate: actualNegatives > 0 ? falsePositives / actualNegatives : 0,
      };
    });

    const tprs = groupResults.map((g) => g.truePositiveRate);
    const fprs = groupResults.map((g) => g.falsePositiveRate);
    const maxTPRDisparity = withActual.length > 0 ? Math.max(...tprs) - Math.min(...tprs) : 0;
    const maxFPRDisparity = withActual.length > 0 ? Math.max(...fprs) - Math.min(...fprs) : 0;
    const passesCheck =
      maxTPRDisparity <= this.EQUAL_OPPORTUNITY_THRESHOLD &&
      maxFPRDisparity <= this.EQUAL_OPPORTUNITY_THRESHOLD;

    return {
      attribute,
      groups: groupResults,
      maxTPRDisparity,
      maxFPRDisparity,
      threshold: this.EQUAL_OPPORTUNITY_THRESHOLD,
      passesCheck,
    };
  }

  private calculateDisparateImpact(
    predictions: { input: Record<string, unknown>; prediction: unknown }[],
    attribute: ProtectedAttribute,
  ): DisparateImpactResult {
    const groups = this.groupPredictionsByAttribute(predictions, attribute);
    const groupEntries = Object.entries(groups);

    if (groupEntries.length < 2) {
      return {
        attribute,
        impactRatio: 1.0,
        threshold: this.DISPARATE_IMPACT_THRESHOLD,
        adverseImpact: 'none',
        groups: groupEntries.map(([name, preds]) => ({
          name,
          selectionRate: 0,
          impactRatio: 1.0,
        })),
      };
    }

    const referenceGroup = groupEntries[0];
    const referenceRate =
      referenceGroup[1].length > 0
        ? referenceGroup[1].filter(
            (p) => p.prediction === 1 || p.prediction === true,
          ).length / referenceGroup[1].length
        : 0;

    const groupResults = groupEntries.map(([name, preds]) => {
      const selectionRate =
        preds.length > 0
          ? preds.filter((p) => p.prediction === 1 || p.prediction === true).length /
            preds.length
          : 0;
      const impactRatio = referenceRate > 0 ? selectionRate / referenceRate : 1.0;
      return { name, selectionRate, impactRatio };
    });

    const minImpactRatio = Math.min(...groupResults.map((g) => g.impactRatio));
    const adverseImpact: DisparateImpactResult['adverseImpact'] =
      minImpactRatio < 0.8 ? 'significant' : minImpactRatio < 1.0 ? 'moderate' : 'none';

    return {
      attribute,
      impactRatio: minImpactRatio,
      threshold: this.DISPARATE_IMPACT_THRESHOLD,
      adverseImpact,
      groups: groupResults,
    };
  }

  private groupByAttribute(
    data: Record<string, unknown>[],
    attribute: ProtectedAttribute,
  ): Record<string, Record<string, unknown>[]> {
    const groups: Record<string, Record<string, unknown>[]> = {};
    for (const record of data) {
      const value = String(record[attribute] ?? 'unknown');
      if (!groups[value]) groups[value] = [];
      groups[value].push(record);
    }
    return groups;
  }

  private groupPredictionsByAttribute(
    predictions: { input: Record<string, unknown>; prediction: unknown }[],
    attribute: ProtectedAttribute,
  ): Record<string, { input: Record<string, unknown>; prediction: unknown }[]> {
    const groups: Record<string, { input: Record<string, unknown>; prediction: unknown }[]> =
      {};
    for (const pred of predictions) {
      const value = String(pred.input[attribute] ?? 'unknown');
      if (!groups[value]) groups[value] = [];
      groups[value].push(pred);
    }
    return groups;
  }

  private computeOverallScore(results: BiasResult[]): number {
    if (results.length === 0) return 0;
    const weightedSum = results.reduce(
      (sum, r) => sum + r.score * this.severityWeight(r.severity),
      0,
    );
    const totalWeight = results.reduce(
      (sum, r) => sum + this.severityWeight(r.severity),
      0,
    );
    return totalWeight > 0 ? weightedSum / totalWeight : 0;
  }

  private severityWeight(severity: BiasResult['severity']): number {
    switch (severity) {
      case 'critical':
        return 4;
      case 'high':
        return 3;
      case 'medium':
        return 2;
      case 'low':
        return 1;
    }
  }

  private computeSignificance(
    groups: { name: string; count: number }[],
  ): number {
    const total = groups.reduce((s, g) => s + g.count, 0);
    const expected = total / groups.length;
    const chiSq = groups.reduce(
      (s, g) => s + Math.pow(g.count - expected, 2) / expected,
      0,
    );
    return Math.min(1 - 1 / (1 + chiSq / groups.length), 0.999);
  }

  private getDefaultMitigations(attribute: ProtectedAttribute): string[] {
    return [
      'Ensure balanced representation across all groups in training data',
      'Apply fairness-aware machine learning techniques',
      'Conduct regular bias audits on model predictions',
      'Implement disparate impact testing in CI/CD pipeline',
      'Establish human review for decisions affecting underrepresented groups',
    ];
  }
}
