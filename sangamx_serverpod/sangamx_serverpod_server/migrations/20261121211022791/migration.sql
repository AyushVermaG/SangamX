BEGIN;

--
-- ACTION CREATE TABLE
--
CREATE TABLE "room" (
    "id" bigserial PRIMARY KEY,
    "name" text NOT NULL,
    "roomCode" text NOT NULL,
    "createdAt" timestamp without time zone NOT NULL,
    "isActive" boolean NOT NULL
);

-- Indexes
CREATE UNIQUE INDEX "room_code_unique_idx" ON "room" USING btree ("roomCode");

--
-- ACTION CREATE TABLE
--
CREATE TABLE "room_participant" (
    "id" bigserial PRIMARY KEY,
    "roomId" bigint NOT NULL,
    "participantName" text NOT NULL,
    "joinedAt" timestamp without time zone NOT NULL,
    "isOnline" boolean NOT NULL
);

-- Indexes
CREATE INDEX "room_participant_idx" ON "room_participant" USING btree ("roomId", "participantName");

--
-- ACTION CREATE FOREIGN KEY
--
ALTER TABLE ONLY "room_participant"
    ADD CONSTRAINT "room_participant_fk_0"
    FOREIGN KEY("roomId")
    REFERENCES "room"("id")
    ON DELETE CASCADE
    ON UPDATE NO ACTION;


--
-- MIGRATION VERSION FOR sangamx_serverpod
--
INSERT INTO "serverpod_migrations" ("module", "version", "timestamp")
    VALUES ('sangamx_serverpod', '20261121211022791', now())
    ON CONFLICT ("module")
    DO UPDATE SET "version" = '20261121211022791', "timestamp" = now();

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
