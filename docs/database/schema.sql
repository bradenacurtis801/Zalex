-- ScanPro Database Schema
-- Generated on: 2025-10-23 12:32:43
-- Database: scanpro_db
-- Host: localhost:5432
-- User: postgres

-- Table: document
-- ==================================================
CREATE TABLE document (
    filename character varying(500) NOT NULL,
    file_content bytea NOT NULL,
    file_size integer NOT NULL,
    mime_type character varying(100) NOT NULL,
    status USER-DEFINED NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    id character varying(64) NOT NULL,
    user_id integer
);

-- Foreign Keys for document
ALTER TABLE document ADD CONSTRAINT document_user_id_fkey FOREIGN KEY (user_id) REFERENCES user(id);

-- Table: documentclassification
-- ==================================================
CREATE TABLE documentclassification (
    category character varying(100) NOT NULL,
    confidence double precision NOT NULL,
    model_version character varying(50) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    id integer NOT NULL DEFAULT nextval('documentclassification_id_seq'::regclass),
    document_id character varying NOT NULL,
    user_id integer
);

-- Foreign Keys for documentclassification
ALTER TABLE documentclassification ADD CONSTRAINT documentclassification_document_id_fkey FOREIGN KEY (document_id) REFERENCES document(id);
ALTER TABLE documentclassification ADD CONSTRAINT documentclassification_user_id_fkey FOREIGN KEY (user_id) REFERENCES user(id);

-- Table: documentfeedback
-- ==================================================
CREATE TABLE documentfeedback (
    feedback_type character varying(50) NOT NULL,
    suggested_category character varying(100),
    comment character varying(1000),
    created_at timestamp without time zone NOT NULL,
    id integer NOT NULL DEFAULT nextval('documentfeedback_id_seq'::regclass),
    document_id character varying NOT NULL,
    user_id integer
);

-- Foreign Keys for documentfeedback
ALTER TABLE documentfeedback ADD CONSTRAINT documentfeedback_document_id_fkey FOREIGN KEY (document_id) REFERENCES document(id);
ALTER TABLE documentfeedback ADD CONSTRAINT documentfeedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES user(id);

-- Table: ocrdata
-- ==================================================
CREATE TABLE ocrdata (
    page_number integer NOT NULL,
    full_text character varying NOT NULL,
    words_data character varying NOT NULL,
    lines_data character varying NOT NULL,
    confidence_score double precision NOT NULL,
    total_words integer NOT NULL,
    total_lines integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    id integer NOT NULL DEFAULT nextval('ocrdata_id_seq'::regclass),
    document_id character varying NOT NULL,
    original_image_width integer,
    original_image_height integer
);

-- Foreign Keys for ocrdata
ALTER TABLE ocrdata ADD CONSTRAINT ocrdata_document_id_fkey FOREIGN KEY (document_id) REFERENCES document(id);

-- Table: pdfcache
-- ==================================================
CREATE TABLE pdfcache (
    max_pages integer NOT NULL,
    total_pages integer NOT NULL,
    pages_data character varying NOT NULL,
    created_at timestamp without time zone NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    id integer NOT NULL DEFAULT nextval('pdfcache_id_seq'::regclass),
    document_id character varying NOT NULL
);

-- Foreign Keys for pdfcache
ALTER TABLE pdfcache ADD CONSTRAINT pdfcache_document_id_fkey FOREIGN KEY (document_id) REFERENCES document(id);

-- Table: session
-- ==================================================
CREATE TABLE session (
    user_id integer NOT NULL,
    session_token character varying(255) NOT NULL,
    is_revoked boolean NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone NOT NULL,
    last_activity timestamp without time zone NOT NULL,
    id integer NOT NULL DEFAULT nextval('session_id_seq'::regclass)
);

-- Foreign Keys for session
ALTER TABLE session ADD CONSTRAINT session_user_id_fkey FOREIGN KEY (user_id) REFERENCES user(id);

-- Table: uploadsession
-- ==================================================
CREATE TABLE uploadsession (
    client_id character varying(100) NOT NULL,
    status USER-DEFINED NOT NULL,
    total_files integer NOT NULL,
    processed_files integer NOT NULL,
    current_file character varying(500),
    progress_percent double precision NOT NULL,
    error_message character varying(1000),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    id integer NOT NULL DEFAULT nextval('uploadsession_id_seq'::regclass),
    user_id integer
);

-- Foreign Keys for uploadsession
ALTER TABLE uploadsession ADD CONSTRAINT uploadsession_user_id_fkey FOREIGN KEY (user_id) REFERENCES user(id);

-- Table: uploadsessionfile
-- ==================================================
CREATE TABLE uploadsessionfile (
    filename character varying(500) NOT NULL,
    file_size integer NOT NULL,
    mime_type character varying(100) NOT NULL,
    status USER-DEFINED NOT NULL,
    error_message character varying(1000),
    created_at timestamp without time zone NOT NULL,
    id integer NOT NULL DEFAULT nextval('uploadsessionfile_id_seq'::regclass),
    session_id integer NOT NULL,
    file_hash character varying(64),
    document_id character varying
);

-- Foreign Keys for uploadsessionfile
ALTER TABLE uploadsessionfile ADD CONSTRAINT uploadsessionfile_session_id_fkey FOREIGN KEY (session_id) REFERENCES uploadsession(id);
ALTER TABLE uploadsessionfile ADD CONSTRAINT uploadsessionfile_document_id_fkey FOREIGN KEY (document_id) REFERENCES document(id);

-- Table: user
-- ==================================================
CREATE TABLE user (
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    user_role USER-DEFINED NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    id integer NOT NULL DEFAULT nextval('user_id_seq'::regclass),
    password_hash character varying(255) NOT NULL
);

