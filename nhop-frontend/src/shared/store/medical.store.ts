
/*
==========================================================
NHOP MEDICAL GLOBAL STORE
Sovereign Clinical State Engine
==========================================================
*/

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { v4 as uuid } from "uuid";

/* ======================================================
   TYPES
====================================================== */

export type Patient = {
  id: string;
  name: string;
  age?: number;
  gender?: string;
};

export type Sample = {
  id: string;
  patientId: string;
  type: string;
  status: "pending" | "processing" | "completed";
};

type ConnectionState = "offline" | "connecting" | "online";

/* ======================================================
   STORE STATE
====================================================== */

type MedicalState = {

  /* session */
  sessionId: string;

  /* connection */
  connection: ConnectionState;

  /* active entities */
  activePatient?: Patient;
  activeSample?: Sample;

  /* collections */
  patients: Patient[];
  samples: Sample[];

  /* actions */
  setConnection: (state: ConnectionState) => void;

  setActivePatient: (patient: Patient) => void;
  clearActivePatient: () => void;

  addPatient: (patient: Patient) => void;

  addSample: (sample: Sample) => void;
  setActiveSample: (sample: Sample) => void;
};

/* ======================================================
   STORE
====================================================== */

export const useMedicalStore = create<MedicalState>()(
  devtools((set) => ({

    sessionId: uuid(),

    connection: "offline",

    patients: [],
    samples: [],

    /* ---------------- connection ---------------- */

    setConnection: (connection) =>
      set({ connection }),

    /* ---------------- patient ---------------- */

    setActivePatient: (patient) =>
      set({ activePatient: patient }),

    clearActivePatient: () =>
      set({ activePatient: undefined }),

    addPatient: (patient) =>
      set((state) => ({
        patients: [...state.patients, patient]
      })),

    /* ---------------- samples ---------------- */

    addSample: (sample) =>
      set((state) => ({
        samples: [...state.samples, sample]
      })),

    setActiveSample: (sample) =>
      set({ activeSample: sample })

  }))
);
