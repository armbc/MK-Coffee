import {
  mysqlTable,
  mysqlEnum,
  serial,
  varchar,
  text,
  timestamp,
  // bigint,
} from "drizzle-orm/mysql-core";

// 合作咨询留资
export const leads = mysqlTable("leads", {
  id: serial("id").primaryKey(),
  name: varchar("name", { length: 64 }).notNull(),
  company: varchar("company", { length: 128 }),
  phone: varchar("phone", { length: 32 }).notNull(),
  intent: mysqlEnum("intent", [
    "soe",
    "commercial",
    "beans",
    "gift",
    "other",
  ]).notNull(),
  message: text("message"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export type Lead = typeof leads.$inferSelect;
