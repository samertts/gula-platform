
/*
==========================================================
NHOP MEDICAL GLOBAL STORE
Clinical Operating Memory Layer
==========================================================
*/

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { v4 as uuid } from "uuid";

/* ======================================================
   DOMAIN TYPES
====================================================== */

export type Patient = {
  id: string;
  name: string;
  age?: number;
  gender?: string;
};

export type LabResult = {
  id: string;
  patientId: string;
  test: string;
  value: string;
  status: "pending" | "verified";
  timestamp: number;
};

export type ConnectionState =
  | "offline"
  | "connecting"
  | "online";

/* ======================================================
   STORE CONTRACT
====================================================== */

type MedicalStore = {

  /* SYSTEM SESSION */
  sessionId: string;

  /* CONNECTION */
  connection: ConnectionState;

  /* ACTIVE CONTEXT */
  currentPatient?: Patient;

  /* DATA */
  patients: Patient[];
  results: LabResult[];

  /* FLAGS */
  aiThinking: boolean;

  /* ACTIONS */

  setConnection(state: ConnectionState): void;

  setCurrentPatient(patient: Patient): void;
  clearPatient(): void;

  addPatient(patient: Patient): void;

  addResult(result: LabResult): void;
  updateResult(resultId: string, patch: Partial<LabResult>): void;

  setAIThinking(v: boolean): void;
};

/* ======================================================
   STORE IMPLEMENTATION
====================================================== */

export const useMedicalStore = create<MedicalStore>()(
  devtools((set, get) => ({

    sessionId: uuid(),

    connection: "offline",

    patients: [],
    results: [],

    aiThinking: false,

    /* ---------------- CONNECTION ---------------- */

    setConnection: (state) =>
      set({ connection: state }),

    /* ---------------- PATIENT ---------------- */

    setCurrentPatient: (patient) =>
      set({ currentPatient: patient }),

    clearPatient: () =>
      set({ currentPatient: undefined }),

    addPatient: (patient) =>
      set((s) => ({
        patients: [...s.patients, patient]
      })),

    /* ---------------- RESULTS ---------------- */

    addResult: (result) =>
      set((s) => ({
        results: [...s.results, result]
      })),

    updateResult: (resultId, patch) =>
      set((s) => ({
        results: s.results.map(r =>
          r.id === resultId
            ? { ...r, ...patch }
            : r
        )
      })),

    /* ---------------- AI ---------------- */

    setAIThinking: (v) =>
      set({ aiThinking: v })

  }), {
    name: "NHOP_MEDICAL_STORE"
  })
);

