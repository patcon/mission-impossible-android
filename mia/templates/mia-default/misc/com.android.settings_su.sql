PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS android_metadata;
CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT);
INSERT INTO "android_metadata" VALUES('en_US');
DROP TABLE IF EXISTS uid_policy;
CREATE TABLE IF NOT EXISTS uid_policy (logging integer, desired_name text, username text, policy text, until integer, command text not null, uid integer, desired_uid integer, package_name text, name text, primary key(uid, command, desired_uid));
INSERT INTO "uid_policy" VALUES(1,NULL,NULL,'allow',0,'',REPLACE_WITH_ORWALL_UID,0,'org.ethack.orwall','orWall');
COMMIT;
