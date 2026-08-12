import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * A server-only, audited binding between a Manus user and a verified GULA
 * workspace identity. No row is seeded: operations requiring lab scope remain
 * unavailable until an administrator records evidence from GULA authz/me and
 * an active assignment.
 */
export const gulaWorkspaceBindings = mysqlTable("gula_workspace_bindings", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().unique(),
  gulaSubjectId: int("gulaSubjectId").notNull(),
  labId: int("labId").notNull(),
  organizationId: int("organizationId"),
  facilityId: int("facilityId"),
  assignmentRoleId: varchar("assignmentRoleId", { length: 128 }),
  verifiedAt: timestamp("verifiedAt").notNull(),
  verifiedByUserId: int("verifiedByUserId").notNull(),
  status: mysqlEnum("status", ["active", "revoked"]).default("active").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type GulaWorkspaceBinding = typeof gulaWorkspaceBindings.$inferSelect;
export type InsertGulaWorkspaceBinding = typeof gulaWorkspaceBindings.$inferInsert;
