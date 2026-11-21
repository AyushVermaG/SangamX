BEGIN;

--
-- ACTION CREATE TABLE
--
CREATE TABLE "shared_task" (
    "id" bigserial PRIMARY KEY,
    "roomId" bigint NOT NULL,
    "query" text NOT NULL,
    "status" text NOT NULL,
    "fastapiTaskId" text,
    "finalAnswer" text,
    "error" text,
    "createdAt" timestamp without time zone NOT NULL,
    "completedAt" timestamp without time zone
);

-- Indexes
CREATE INDEX "shared_task_room_idx" ON "shared_task" USING btree ("roomId");
CREATE INDEX "shared_task_fastapi_idx" ON "shared_task" USING btree ("fastapiTaskId");

--
-- ACTION CREATE FOREIGN KEY
--
ALTER TABLE ONLY "shared_task"
    ADD CONSTRAINT "shared_task_fk_0"
    FOREIGN KEY("roomId")
    REFERENCES "room"("id")
    ON DELETE CASCADE
    ON UPDATE NO ACTION;


--
-- MIGRATION VERSION FOR sangamx_serverpod
--
INSERT INTO "serverpod_migrations" ("module", "version", "timestamp")
    VALUES ('sangamx_serverpod', '20261121212443648', now())
    ON CONFLICT ("module")
    DO UPDATE SET "version" = '20261121212443648', "timestamp" = now();

--
-- MIGRATION VERSION FOR serverpod
--
INSERT INTO "serverpod_migrations" ("module", "version", "timestamp")
    VALUES ('serverpod', '20260824182259319', now())
    ON CONFLICT ("module")
    DO UPDATE SET "version" = '20260824182259319', "timestamp" = now();

--
-- MIGRATION VERSION FOR serverpod_auth_idp
--
INSERT INTO "serverpod_migrations" ("module", "version", "timestamp")
    VALUES ('serverpod_auth_idp', '20261015164015382', now())
    ON CONFLICT ("module")
    DO UPDATE SET "version" = '20261015164015382', "timestamp" = now();

--
-- MIGRATION VERSION FOR serverpod_auth_core
--
INSERT INTO "serverpod_migrations" ("module", "version", "timestamp")
    VALUES ('serverpod_auth_core', '20260924105232991', now())
    ON CONFLICT ("module")
    DO UPDATE SET "version" = '20260924105232991', "timestamp" = now();


COMMIT;
