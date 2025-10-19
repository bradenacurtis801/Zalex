#!/usr/bin/env python3
"""
Export PostgreSQL schema for ScanPro database
Generates SQL schema file and table descriptions
"""

import psycopg2
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

try:
    import config
except ImportError:
    print("❌ Could not import config. Make sure you're running from the project root.")
    sys.exit(1)

def generate_mermaid_erd(cursor, tables, output_file):
    """Generate a Mermaid ERD diagram"""
    
    mermaid_content = ["erDiagram"]
    
    # Get all foreign key relationships
    cursor.execute("""
        SELECT 
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name, kcu.column_name;
    """)
    
    relationships = cursor.fetchall()
    
    # Generate table definitions
    for table in tables:
        # Get table columns
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s
            ORDER BY ordinal_position;
        """, (table,))
        
        columns = cursor.fetchall()
        
        # Start table definition
        mermaid_content.append(f"    {table} {{")
        
        # Add columns
        for col_name, data_type, nullable, default_val, max_length in columns:
            # Format data type
            if max_length:
                type_str = f"{data_type}({max_length})"
            else:
                type_str = data_type
            
            # Add primary key indicator (simple heuristic)
            pk_indicator = " PK" if "id" in col_name.lower() and col_name.lower().endswith("id") else ""
            
            # Add foreign key indicator
            fk_indicator = ""
            for rel_table, rel_col, ref_table, ref_col in relationships:
                if rel_table == table and rel_col == col_name:
                    fk_indicator = " FK"
                    break
            
            # Add NOT NULL indicator
            null_indicator = "" if nullable == "YES" else " NOT NULL"
            
            mermaid_content.append(f"        {data_type} {col_name}{pk_indicator}{fk_indicator}{null_indicator}")
        
        mermaid_content.append("    }")
        mermaid_content.append("")  # Empty line between tables
    
    # Add relationships
    for rel_table, rel_col, ref_table, ref_col in relationships:
        mermaid_content.append(f"    {rel_table} ||--o{{ {ref_table} : \"{rel_col}\"")
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(mermaid_content))

def export_schema():
    """Export the complete database schema"""
    
    try:
        # Connect to database using config settings
        conn = psycopg2.connect(
            host=config.settings.postgres_host,
            port=int(config.settings.postgres_port),
            database=config.settings.postgres_db_name,
            user=config.settings.postgres_username,
            password=config.settings.postgres_password
        )
        
        cursor = conn.cursor()
        
        print("📊 Exporting ScanPro database schema...")
        print(f"   Host: {config.settings.postgres_host}")
        print(f"   Port: {config.settings.postgres_port}")
        print(f"   Database: {config.settings.postgres_db_name}")
        print(f"   User: {config.settings.postgres_username}")
        print()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Export schema to SQL file
        output_dir = Path(__file__).parent
        schema_file = output_dir / 'schema.sql'
        with open(schema_file, 'w') as f:
            f.write(f"-- ScanPro Database Schema\n")
            f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Database: {config.settings.postgres_db_name}\n")
            f.write(f"-- Host: {config.settings.postgres_host}:{config.settings.postgres_port}\n")
            f.write(f"-- User: {config.settings.postgres_username}\n\n")
            
            # Get table structures
            for table in tables:
                f.write(f"-- Table: {table}\n")
                f.write(f"-- {'='*50}\n")
                
                # Get column information
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))
                
                columns = cursor.fetchall()
                
                f.write(f"CREATE TABLE {table} (\n")
                for i, (col_name, data_type, nullable, default_val, max_length) in enumerate(columns):
                    # Format data type
                    if max_length:
                        type_str = f"{data_type}({max_length})"
                    else:
                        type_str = data_type
                    
                    # Add NOT NULL constraint
                    null_constraint = "" if nullable == "YES" else " NOT NULL"
                    
                    # Add default value
                    default_str = f" DEFAULT {default_val}" if default_val else ""
                    
                    # Add comma except for last column
                    comma = "," if i < len(columns) - 1 else ""
                    
                    f.write(f"    {col_name} {type_str}{null_constraint}{default_str}{comma}\n")
                
                f.write(");\n\n")
                
                # Get foreign key constraints
                cursor.execute("""
                    SELECT 
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_name = %s;
                """, (table,))
                
                fks = cursor.fetchall()
                if fks:
                    f.write(f"-- Foreign Keys for {table}\n")
                    for fk_name, col_name, ref_table, ref_col in fks:
                        f.write(f"ALTER TABLE {table} ADD CONSTRAINT {fk_name} ")
                        f.write(f"FOREIGN KEY ({col_name}) REFERENCES {ref_table}({ref_col});\n")
                    f.write("\n")
        
        print(f"✅ Schema exported to {schema_file}")
        
        # Generate table descriptions
        tables_file = output_dir / 'tables.md'
        with open(tables_file, 'w') as f:
            f.write("# ScanPro Database Tables\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database: {config.settings.postgres_db_name}\n")
            f.write(f"Host: {config.settings.postgres_host}:{config.settings.postgres_port}\n\n")
            
            for table in tables:
                f.write(f"## {table}\n\n")
                
                # Get column details
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))
                
                columns = cursor.fetchall()
                
                f.write("| Column | Type | Nullable | Default | Description |\n")
                f.write("|--------|------|----------|---------|-------------|\n")
                
                for col_name, data_type, nullable, default_val, max_length in columns:
                    type_str = f"{data_type}({max_length})" if max_length else data_type
                    null_str = "Yes" if nullable == "YES" else "No"
                    default_str = str(default_val) if default_val else "-"
                    
                    f.write(f"| {col_name} | {type_str} | {null_str} | {default_str} | |\n")
                
                f.write("\n")
        
        print(f"✅ Table descriptions exported to {tables_file}")
        
        # Generate Mermaid ERD
        mermaid_file = output_dir / 'erd.mmd'
        generate_mermaid_erd(cursor, tables, mermaid_file)
        print(f"✅ Mermaid ERD exported to {mermaid_file}")
        
        cursor.close()
        conn.close()
        
        print("\n🎯 Next steps:")
        print("1. View the Mermaid ERD at: https://mermaid.live/")
        print("2. Or open erd.mmd in VS Code with Mermaid Preview extension")
        print("3. GitHub will automatically render the diagram in the README")
        print("4. For pgAdmin ERD: Generate in pgAdmin and save as 'erd.png' and 'erd.svg'")
        
    except Exception as e:
        print(f"❌ Error exporting schema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    export_schema()
