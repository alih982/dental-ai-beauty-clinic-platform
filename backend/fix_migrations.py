import sqlite3
import os
from datetime import datetime

db_path = '/Users/alihatami/Documents/django for big projects/new pro/Hospital_Application-main/backend/db.sqlite3'

sql = """
DROP TABLE IF EXISTS doctor_working_hours;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS specialties;
DELETE FROM django_migrations WHERE app='doctors';

CREATE TABLE "specialties" (
    "id" char(32) NOT NULL PRIMARY KEY, 
    "created_at" datetime NOT NULL, 
    "updated_at" datetime NOT NULL, 
    "is_deleted" bool NOT NULL, 
    "deleted_at" datetime NULL, 
    "name_fa" varchar(200) NOT NULL UNIQUE, 
    "name_en" varchar(200) NOT NULL, 
    "description_fa" text NOT NULL, 
    "description_en" text NOT NULL, 
    "icon" varchar(100) NOT NULL
);

CREATE TABLE "doctors" (
    "id" char(32) NOT NULL PRIMARY KEY, 
    "created_at" datetime NOT NULL, 
    "updated_at" datetime NOT NULL, 
    "is_deleted" bool NOT NULL, 
    "deleted_at" datetime NULL, 
    "first_name_fa" varchar(100) NOT NULL, 
    "first_name_en" varchar(100) NOT NULL, 
    "last_name_fa" varchar(100) NOT NULL, 
    "last_name_en" varchar(100) NOT NULL, 
    "national_code" varchar(10) NOT NULL UNIQUE, 
    "phone" varchar(15) NOT NULL UNIQUE, 
    "email" varchar(254) NOT NULL, 
    "medical_council_number" varchar(20) NOT NULL UNIQUE, 
    "sub_specialty_fa" varchar(200) NOT NULL, 
    "sub_specialty_en" varchar(200) NOT NULL, 
    "years_of_experience" integer unsigned NOT NULL, 
    "education_fa" text NOT NULL, 
    "education_en" text NOT NULL, 
    "clinic_name_fa" varchar(255) NOT NULL, 
    "clinic_name_en" varchar(255) NOT NULL, 
    "clinic_address_fa" text NOT NULL, 
    "clinic_address_en" text NOT NULL, 
    "city_fa" varchar(100) NOT NULL, 
    "city_en" varchar(100) NOT NULL, 
    "fee" decimal NOT NULL, 
    "accepts_insurance" bool NOT NULL, 
    "bio_fa" text NOT NULL, 
    "bio_en" text NOT NULL, 
    "profile_image" varchar(100) NULL, 
    "is_active" bool NOT NULL, 
    "is_verified" bool NOT NULL, 
    "rating" decimal NOT NULL, 
    "review_count" integer unsigned NOT NULL, 
    "patient_count" integer unsigned NOT NULL, 
    "specialty_id" char(32) NOT NULL REFERENCES "specialties" ("id")
);

CREATE TABLE "doctor_working_hours" (
    "id" char(32) NOT NULL PRIMARY KEY, 
    "created_at" datetime NOT NULL, 
    "updated_at" datetime NOT NULL, 
    "is_deleted" bool NOT NULL, 
    "deleted_at" datetime NULL, 
    "day_of_week" integer NOT NULL, 
    "start_time" time NOT NULL, 
    "end_time" time NOT NULL, 
    "is_active" bool NOT NULL, 
    "doctor_id" char(32) NOT NULL REFERENCES "doctors" ("id")
);

CREATE INDEX "doctors_special_602ff7_idx" ON "doctors" ("specialty_id", "city_fa");
CREATE INDEX "doctors_special_b4eb53_idx" ON "doctors" ("specialty_id", "city_en");
CREATE INDEX "doctors_is_acti_d2e13d_idx" ON "doctors" ("is_active", "is_verified");
CREATE INDEX "specialties_created_at" ON "specialties" ("created_at");
CREATE INDEX "doctors_created_at" ON "doctors" ("created_at");

INSERT INTO django_migrations (app, name, applied) VALUES ('doctors', '0001_initial', datetime('now'));
"""

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
try:
    conn.executescript(sql)
    conn.commit()
    print("Doctor tables created successfully and history updated.")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
