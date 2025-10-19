# ScanPro Database Schema

This directory contains the database schema documentation and diagrams for the ScanPro application.

## 📊 Database Diagram

### Mermaid ERD (Text-based)

```mermaid
erDiagram
    user {
        int id PK
        varchar username
        varchar email
        varchar full_name
        varchar user_role
        boolean is_active
        varchar password_hash
        timestamp created_at
        timestamp updated_at
    }
    
    session {
        int id PK
        int user_id FK
        varchar session_token
        boolean is_revoked
        timestamp expires_at
        timestamp created_at
        timestamp last_activity
    }
    
    document {
        varchar id PK
        int user_id FK
        varchar filename
        bytea file_content
        int file_size
        varchar mime_type
        varchar status
        timestamp created_at
        timestamp updated_at
    }
    
    documentclassification {
        int id PK
        varchar document_id FK
        int user_id FK
        varchar category
        float confidence
        varchar model_version
        timestamp created_at
    }
    
    documentfeedback {
        int id PK
        varchar document_id FK
        int user_id FK
        varchar feedback_type
        varchar suggested_category
        text comment
        timestamp created_at
    }
    
    pdfcache {
        int id PK
        varchar document_id FK
        int max_pages
        int total_pages
        text pages_data
        timestamp created_at
        timestamp expires_at
    }
    
    user ||--o{ session : "user_id"
    user ||--o{ document : "user_id"
    user ||--o{ documentfeedback : "user_id"
    document ||--o{ documentclassification : "document_id"
    document ||--|| documentfeedback : "document_id"
    document ||--|| pdfcache : "document_id"
```


## 🗂️ Files

- **`erd.png`** - Main database ERD diagram (PNG format)
- **`erd.svg`** - Scalable vector version of the ERD
- **`schema.sql`** - Complete database schema as SQL
- **`tables.md`** - Detailed table descriptions

## 🏗️ Database Structure

### Core Tables

#### **Authentication & Users**
- **`user`** - User accounts and authentication
- **`session`** - User session management

#### **Document Management**
- **`document`** - Uploaded document metadata
- **`documentclassification`** - AI classification results
- **`documentfeedback`** - User corrections and feedback

#### **Document Processing**
- **`pdfcache`** - PDF processing cache

## 🔗 Relationships

- **User** → **Session** (1:many)
- **User** → **Document** (1:many)
- **User** → **DocumentFeedback** (1:many)
- **Document** → **DocumentClassification** (1:many)
- **Document** → **DocumentFeedback** (1:1)
- **Document** → **PdfCache** (1:1)

## 🛠️ Generating Diagrams

To regenerate the ERD diagram:

1. **Using pgAdmin:**
   - Connect to your PostgreSQL database
   - Right-click on "public" schema → "Generate ERD"
   - Export as PNG/SVG

2. **Using DBeaver:**
   - Connect to database
   - Right-click database → "Generate ERD"
   - Export in desired format

3. **Using command line:**
   ```bash
   # Export schema
   pg_dump --schema-only --no-owner --no-privileges -h localhost -U postgres scanpro_db > schema.sql
   ```

## 📝 Schema Updates

When making database changes:

1. Update the ERD diagram
2. Update `schema.sql` with new structure
3. Update this README if new tables are added
4. Document any breaking changes

## 🔒 Security Notes

- All user passwords are hashed using bcrypt
- Session tokens are securely generated
- Foreign key constraints ensure data integrity
- Indexes are optimized for common queries
