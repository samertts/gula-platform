/**
 * Showcase data boundary.
 *
 * Showcase UI depends on DemoDataProvider (synthetic data only) — never on
 * production repositories (patients, laboratory, results, clinical, users).
 * A future ProductionDataProvider would live on the production side of the
 * boundary and must NEVER be reachable from Showcase code.
 */

import type { DemoProfileId } from "./profiles";
import { DEMO_VIEWS, type DemoProfileView } from "./mockData";

export interface DemoDataProvider {
  readonly kind: "demo";
  getView(profile: DemoProfileId): DemoProfileView | null;
}

/** The single synthetic-data provider used by the Showcase. */
export const demoDataProvider: DemoDataProvider = {
  kind: "demo",
  getView(profile) {
    return DEMO_VIEWS[profile] ?? null;
  },
};
