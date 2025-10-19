# ScanPro Database Tables

Generated on: 2025-10-19 08:53:00
Database: scanpro_db
Host: localhost:5432

## document

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| filename | character varying(500) | No | - | |
| file_content | bytea | No | - | |
| file_size | integer | No | - | |
| mime_type | character varying(100) | No | - | |
| status | USER-DEFINED | No | - | |
| created_at | timestamp without time zone | No | - | |
| updated_at | timestamp without time zone | No | - | |
| id | character varying(64) | No | - | |
| user_id | integer | Yes | - | |

## documentclassification

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| category | character varying(100) | No | - | |
| confidence | double precision | No | - | |
| model_version | character varying(50) | No | - | |
| created_at | timestamp without time zone | No | - | |
| id | integer | No | nextval('documentclassification_id_seq'::regclass) | |
| document_id | character varying | No | - | |
| user_id | integer | Yes | - | |

## documentfeedback

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| feedback_type | character varying(50) | No | - | |
| suggested_category | character varying(100) | Yes | - | |
| comment | character varying(1000) | Yes | - | |
| created_at | timestamp without time zone | No | - | |
| id | integer | No | nextval('documentfeedback_id_seq'::regclass) | |
| document_id | character varying | No | - | |
| user_id | integer | Yes | - | |

## pdfcache

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| max_pages | integer | No | - | |
| total_pages | integer | No | - | |
| pages_data | character varying | No | - | |
| created_at | timestamp without time zone | No | - | |
| expires_at | timestamp without time zone | No | - | |
| id | integer | No | nextval('pdfcache_id_seq'::regclass) | |
| document_id | character varying | No | - | |

## session

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| user_id | integer | No | - | |
| session_token | character varying(255) | No | - | |
| is_revoked | boolean | No | - | |
| expires_at | timestamp without time zone | No | - | |
| created_at | timestamp without time zone | No | - | |
| last_activity | timestamp without time zone | No | - | |
| id | integer | No | nextval('session_id_seq'::regclass) | |

## uploadsession

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| client_id | character varying(100) | No | - | |
| status | USER-DEFINED | No | - | |
| total_files | integer | No | - | |
| processed_files | integer | No | - | |
| current_file | character varying(500) | Yes | - | |
| progress_percent | double precision | No | - | |
| error_message | character varying(1000) | Yes | - | |
| created_at | timestamp without time zone | No | - | |
| updated_at | timestamp without time zone | No | - | |
| expires_at | timestamp without time zone | No | - | |
| id | integer | No | nextval('uploadsession_id_seq'::regclass) | |
| user_id | integer | Yes | - | |

## uploadsessionfile

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| filename | character varying(500) | No | - | |
| file_size | integer | No | - | |
| mime_type | character varying(100) | No | - | |
| status | USER-DEFINED | No | - | |
| error_message | character varying(1000) | Yes | - | |
| created_at | timestamp without time zone | No | - | |
| id | integer | No | nextval('uploadsessionfile_id_seq'::regclass) | |
| session_id | integer | No | - | |
| file_hash | character varying(64) | Yes | - | |
| document_id | character varying | Yes | - | |

## user

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| username | character varying(50) | No | - | |
| email | character varying(255) | No | - | |
| full_name | character varying(255) | No | - | |
| user_role | USER-DEFINED | No | - | |
| is_active | boolean | No | - | |
| created_at | timestamp without time zone | No | - | |
| updated_at | timestamp without time zone | No | - | |
| id | integer | No | nextval('user_id_seq'::regclass) | |
| password_hash | character varying(255) | No | - | |

