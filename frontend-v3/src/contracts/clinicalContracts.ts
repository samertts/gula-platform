export type ContractState = string;

export type TransitionTable = Readonly<Record<string, readonly string[]>>;

export interface ContractDefinition {
  readonly id: string;
  readonly domain: string;
  readonly states: readonly ContractState[];
  readonly transitions: TransitionTable;
  readonly writeSafety: {
    readonly requiresAuthorization: boolean;
    readonly requiresAudit: boolean;
    readonly requiresIdempotency: boolean;
    readonly requiresConcurrency: boolean;
  };
}

const writeSafe = { requiresAuthorization: true, requiresAudit: true, requiresIdempotency: true, requiresConcurrency: true } as const;
const readOrManageSafe = { requiresAuthorization: true, requiresAudit: true, requiresIdempotency: false, requiresConcurrency: true } as const;

export const CLINICAL_CONTRACTS = {
  appointment: {
    id: "CONTRACT-001",
    domain: "appointment",
    states: ["REQUESTED", "CONFIRMED", "CHECKED_IN", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW", "RESCHEDULED", "EXPIRED"],
    transitions: {
      REQUESTED: ["CONFIRMED", "CANCELLED", "EXPIRED"],
      CONFIRMED: ["CHECKED_IN", "CANCELLED", "RESCHEDULED", "NO_SHOW", "EXPIRED"],
      CHECKED_IN: ["IN_PROGRESS", "NO_SHOW"],
      IN_PROGRESS: ["COMPLETED"],
      COMPLETED: [], CANCELLED: [], NO_SHOW: [], RESCHEDULED: ["REQUESTED"], EXPIRED: [],
    },
    writeSafety: writeSafe,
  },
  session: {
    id: "CONTRACT-002",
    domain: "session",
    states: ["ACTIVE", "EXPIRED", "TERMINATED", "REVOKED"],
    transitions: { ACTIVE: ["EXPIRED", "TERMINATED", "REVOKED"], EXPIRED: [], TERMINATED: [], REVOKED: [] },
    writeSafety: readOrManageSafe,
  },
  device: {
    id: "CONTRACT-003",
    domain: "device",
    states: ["PENDING", "ACTIVE", "EXPIRED", "REVOKED"],
    transitions: { PENDING: ["ACTIVE", "REVOKED"], ACTIVE: ["EXPIRED", "REVOKED"], EXPIRED: ["REVOKED"], REVOKED: [] },
    writeSafety: readOrManageSafe,
  },
  patientAccess: {
    id: "CONTRACT-004",
    domain: "patient-access",
    states: ["REQUESTED", "AUTHORIZED", "DENIED", "EXPIRED", "REVOKED"],
    transitions: { REQUESTED: ["AUTHORIZED", "DENIED", "EXPIRED"], AUTHORIZED: ["EXPIRED", "REVOKED"], DENIED: [], EXPIRED: [], REVOKED: [] },
    writeSafety: readOrManageSafe,
  },
  consent: {
    id: "CONTRACT-005",
    domain: "consent-sharing",
    states: ["ACTIVE", "EXPIRED", "REVOKED"],
    transitions: { ACTIVE: ["EXPIRED", "REVOKED"], EXPIRED: [], REVOKED: [] },
    writeSafety: writeSafe,
  },
  accessHistory: {
    id: "CONTRACT-006",
    domain: "access-history",
    states: ["RECORDED"],
    transitions: { RECORDED: [] },
    writeSafety: readOrManageSafe,
  },
  delegation: {
    id: "CONTRACT-007",
    domain: "delegation",
    states: ["REQUESTED", "ACTIVE", "EXPIRED", "REVOKED", "REJECTED"],
    transitions: { REQUESTED: ["ACTIVE", "REJECTED", "REVOKED"], ACTIVE: ["EXPIRED", "REVOKED"], EXPIRED: [], REVOKED: [], REJECTED: [] },
    writeSafety: writeSafe,
  },
  task: {
    id: "CONTRACT-008",
    domain: "task",
    states: ["PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED", "CANCELLED", "EXPIRED"],
    transitions: { PENDING: ["IN_PROGRESS", "SKIPPED", "CANCELLED", "EXPIRED"], IN_PROGRESS: ["COMPLETED", "SKIPPED", "CANCELLED", "EXPIRED"], COMPLETED: [], SKIPPED: [], CANCELLED: [], EXPIRED: [] },
    writeSafety: writeSafe,
  },
  encounter: {
    id: "CONTRACT-009",
    domain: "encounter",
    states: ["DRAFT", "IN_PROGRESS", "COMPLETED", "SIGNED", "AMENDMENT", "CANCELLED"],
    transitions: { DRAFT: ["IN_PROGRESS", "CANCELLED"], IN_PROGRESS: ["COMPLETED"], COMPLETED: ["SIGNED"], SIGNED: ["AMENDMENT"], AMENDMENT: ["SIGNED"], CANCELLED: [] },
    writeSafety: writeSafe,
  },
  clinicalNote: {
    id: "CONTRACT-010",
    domain: "clinical-note",
    states: ["DRAFT", "SIGNED", "AMENDMENT"],
    transitions: { DRAFT: ["SIGNED"], SIGNED: ["AMENDMENT"], AMENDMENT: ["SIGNED"] },
    writeSafety: writeSafe,
  },
  labOrder: {
    id: "CONTRACT-011",
    domain: "lab-order",
    states: ["DRAFT", "PLACED", "ACCEPTED", "IN_PROGRESS", "COMPLETED", "REJECTED", "CANCELLED"],
    transitions: { DRAFT: ["PLACED", "CANCELLED"], PLACED: ["ACCEPTED", "REJECTED", "CANCELLED"], ACCEPTED: ["IN_PROGRESS", "REJECTED", "CANCELLED"], IN_PROGRESS: ["COMPLETED", "REJECTED"], COMPLETED: [], REJECTED: [], CANCELLED: [] },
    writeSafety: writeSafe,
  },
  specimen: {
    id: "CONTRACT-012",
    domain: "specimen",
    states: ["ORDERED", "COLLECTED", "RECEIVED", "PROCESSING", "ANALYZING", "VALIDATED", "REJECTED"],
    transitions: { ORDERED: ["COLLECTED", "REJECTED"], COLLECTED: ["RECEIVED", "REJECTED"], RECEIVED: ["PROCESSING", "REJECTED"], PROCESSING: ["ANALYZING", "REJECTED"], ANALYZING: ["VALIDATED", "REJECTED"], VALIDATED: [], REJECTED: [] },
    writeSafety: writeSafe,
  },
  result: {
    id: "CONTRACT-013",
    domain: "result",
    states: ["DRAFT", "TECHNICALLY_VALIDATED", "CLINICALLY_VALIDATED", "RELEASED", "CORRECTED", "AMENDED"],
    transitions: { DRAFT: ["TECHNICALLY_VALIDATED"], TECHNICALLY_VALIDATED: ["CLINICALLY_VALIDATED"], CLINICALLY_VALIDATED: ["RELEASED"], RELEASED: ["CORRECTED", "AMENDED"], CORRECTED: ["RELEASED"], AMENDED: ["RELEASED"] },
    writeSafety: writeSafe,
  },
  criticalResult: {
    id: "CONTRACT-014",
    domain: "critical-result",
    states: ["DETECTED", "NOTIFIED", "ACKNOWLEDGED", "ACTIONED", "ESCALATED", "CLOSED"],
    transitions: { DETECTED: ["NOTIFIED", "ESCALATED"], NOTIFIED: ["ACKNOWLEDGED", "ESCALATED"], ACKNOWLEDGED: ["ACTIONED", "ESCALATED"], ACTIONED: ["CLOSED"], ESCALATED: ["ACKNOWLEDGED", "ACTIONED", "CLOSED"], CLOSED: [] },
    writeSafety: writeSafe,
  },
  notification: {
    id: "CONTRACT-015",
    domain: "notification",
    states: ["PENDING", "DELIVERED", "FAILED", "ACKNOWLEDGED", "ESCALATED"],
    transitions: { PENDING: ["DELIVERED", "FAILED", "ESCALATED"], DELIVERED: ["ACKNOWLEDGED", "ESCALATED"], FAILED: ["PENDING", "ESCALATED"], ACKNOWLEDGED: [], ESCALATED: ["DELIVERED", "ACKNOWLEDGED"] },
    writeSafety: readOrManageSafe,
  },
} as const satisfies Record<string, ContractDefinition>;

export type ClinicalContractId = keyof typeof CLINICAL_CONTRACTS;

export function isAllowedTransition(contractId: ClinicalContractId, from: string, to: string): boolean {
  const transitions = CLINICAL_CONTRACTS[contractId].transitions as TransitionTable;
  return transitions[from]?.includes(to) ?? false;
}

export function requireAllowedTransition(contractId: ClinicalContractId, from: string, to: string): void {
  if (!isAllowedTransition(contractId, from, to)) {
    throw new Error(`INVALID_STATE_TRANSITION:${CLINICAL_CONTRACTS[contractId].id}:${from}->${to}`);
  }
}

export function requiresClinicalWriteControls(contractId: ClinicalContractId) {
  return CLINICAL_CONTRACTS[contractId].writeSafety;
}
