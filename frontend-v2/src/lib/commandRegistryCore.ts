/**
 * Pure (no-React, no-icon) helpers used by the command-palette registry.
 *
 * Kept in a separate module so they can be unit-tested with plain Node — the
 * full registry imports `lucide-react` icons which require a bundler.
 */
import type { Translation } from '../translations';
import type { UserProfile, UserWing } from '../types/domain';

/** Mirror of the role→wing mapping that the Sidebar uses. */
export const ROLE_WING_MAP: Readonly<Record<string, readonly UserWing[]>> = {
  master_admin: ['admin', 'ministry', 'doctor', 'lab', 'citizen', 'researcher', 'regulator', 'system'],
  admin: ['admin', 'ministry', 'doctor', 'lab', 'citizen', 'researcher', 'regulator'],
  ministry_admin: ['ministry', 'citizen'],
  ministry_analyst: ['ministry', 'citizen', 'researcher'],
  ministry_inspector: ['ministry', 'citizen', 'regulator'],
  physician: ['doctor', 'citizen'],
  technician: ['lab', 'citizen'],
  pathologist: ['lab', 'citizen'],
  lab_admin: ['lab', 'citizen'],
  researcher: ['researcher', 'citizen'],
  regulator: ['regulator', 'citizen'],
  auditor: ['regulator', 'citizen'],
  integration_service: ['admin', 'system'],
  citizen: ['citizen'],
};

export function wingsForProfile(profile: UserProfile | null): readonly UserWing[] {
  if (!profile) return ['citizen'];
  return ROLE_WING_MAP[profile.role] ?? ['citizen'];
}

/**
 * Generic shape — matches the parts of `CommandDefinition` the search
 * helpers need without forcing tests to construct icons or run callbacks.
 */
export interface SearchableCommand {
  id: string;
  category: string;
  label: (t: Translation) => string;
  hint?: (t: Translation) => string;
  keywords?: readonly string[];
  shortcut?: readonly string[];
  wings?: readonly UserWing[];
}

export function filterByWings<C extends SearchableCommand>(
  commands: readonly C[],
  wings: readonly UserWing[],
): C[] {
  return commands.filter((cmd) => {
    if (!cmd.wings || cmd.wings.length === 0) return true;
    return cmd.wings.some((w) => wings.includes(w));
  });
}

/**
 * Score a command against a query. Higher is better; 0 means no match.
 *   100 — exact substring match
 *    25 — subsequence match (each query char appears in order)
 *     1 — empty query (everything passes)
 */
export function scoreCommand<C extends SearchableCommand>(
  cmd: C,
  t: Translation,
  query: string,
): number {
  const q = query.trim().toLowerCase();
  if (!q) return 1;

  const haystack = [
    cmd.label(t),
    cmd.hint?.(t) ?? '',
    cmd.category,
    ...(cmd.keywords ?? []),
    ...(cmd.shortcut ?? []),
  ]
    .join(' ')
    .toLowerCase();

  if (haystack.includes(q)) return 100;

  let qi = 0;
  for (let i = 0; i < haystack.length && qi < q.length; i++) {
    if (haystack[i] === q[qi]) qi++;
  }
  return qi === q.length ? 25 : 0;
}

export function searchCommands<C extends SearchableCommand>(
  commands: readonly C[],
  t: Translation,
  query: string,
): C[] {
  const scored = commands
    .map((cmd) => ({ cmd, score: scoreCommand(cmd, t, query) }))
    .filter((x) => x.score > 0);
  scored.sort((a, b) => b.score - a.score);
  return scored.map((x) => x.cmd);
}

/* ─── Sequence machine (mirror of useShortcut.stepSequence) ───────────── */

export interface SequenceState {
  buffer: string[];
  expiresAt: number;
}

/**
 * Pure step. Returns the new buffer and the matched binding key, if any.
 * Note: does NOT invoke handlers — test-only convenience. The runtime hook
 * fires handlers in place; here we only assert which key matched.
 */
export function stepSequence(
  state: SequenceState,
  key: string,
  bindings: readonly string[],
  now: number,
  windowMs: number,
): { state: SequenceState; fired: string | null } {
  const buf =
    now > state.expiresAt
      ? [key.toLowerCase()]
      : [...state.buffer, key.toLowerCase()];
  const joined = buf.join(' ');

  if (bindings.includes(joined)) {
    return { state: { buffer: [], expiresAt: 0 }, fired: joined };
  }
  const isPrefix = bindings.some(
    (k) => k.startsWith(joined + ' ') || k === joined,
  );
  if (isPrefix) {
    return {
      state: { buffer: buf, expiresAt: now + windowMs },
      fired: null,
    };
  }
  return { state: { buffer: [], expiresAt: 0 }, fired: null };
}
