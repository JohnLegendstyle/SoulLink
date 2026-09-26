// Intentionally empty by default.
// Add Drizzle tables here when the site actually needs a database.
// See examples/d1/db/schema.ts for an opt-in example.
import {sqliteTable,text,integer} from 'drizzle-orm/sqlite-core';
export const rooms=sqliteTable('rooms', {id:text('id').primaryKey(),readHash:text('read_hash').notNull(),johnHash:text('john_hash').notNull(),eddieHash:text('eddie_hash').notNull(),state:text('state').notNull(),revision:integer('revision').notNull().default(0),createdAt:integer('created_at').notNull()});
