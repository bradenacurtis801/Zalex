#!/usr/bin/env python3
"""
Interactive database console for making database queries.
Supports both raw SQL queries and SQLModel operations.
"""

import sys
import logging
from pathlib import Path
from sqlalchemy import text

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, create_engine, select
import config
from src.core.constants import get_database_config
from src.models.database import (
    Document,
    DocumentClassification,
    DocumentFeedback,
    OCRData,
    PDFCache,
    ProcessingTask,
    EmbeddingMetadata,
    Entity,
    User,
    ProcessingTaskStatus,
    DocumentStatus,
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_help():
    """Print help information."""
    print("\n" + "=" * 70)
    print("Database Console Help")
    print("=" * 70)
    print("\nAvailable commands:")
    print("  help              - Show this help message")
    print("  exit / quit      - Exit the console")
    print("  models            - List available SQLModel classes")
    print("  tables            - List all database tables")
    print("  count <model>     - Count records in a model (e.g., 'count Document')")
    print("\nSQL Queries:")
    print("  Enter any SQL query directly (e.g., 'SELECT * FROM document LIMIT 10')")
    print("  Use ';' to end a multi-line query")
    print("\nSQLModel Examples:")
    print("  session.exec(select(Document)).all()")
    print("  session.exec(select(Document).where(Document.id == 'abc123')).first()")
    print("  session.get(Document, 'document_id_here')")
    print("\nAvailable Models:")
    print("  - Document")
    print("  - DocumentClassification")
    print("  - DocumentFeedback")
    print("  - OCRData")
    print("  - PDFCache")
    print("  - ProcessingTask")
    print("  - EmbeddingMetadata")
    print("  - Entity")
    print("  - User")
    print("\nEnums:")
    print("  - ProcessingTaskStatus (PENDING, PROCESSING, COMPLETED, FAILED)")
    print("  - DocumentStatus (PENDING, PROCESSING, COMPLETED, FAILED)")
    print("=" * 70 + "\n")


def list_tables(session: Session):
    """List all tables in the database."""
    from sqlalchemy import inspect
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    print(f"\nDatabase tables ({len(tables)}):")
    for table in sorted(tables):
        print(f"  - {table}")
    print()


def count_records(session: Session, model_name: str, filter_clause: str = None):
    """Count records in a model, optionally with a WHERE filter or JOIN."""
    model_map = {
        'document': Document,
        'documentclassification': DocumentClassification,
        'documentfeedback': DocumentFeedback,
        'ocrdata': OCRData,
        'pdfcache': PDFCache,
        'processingtask': ProcessingTask,
        'embeddingmetadata': EmbeddingMetadata,
        'entity': Entity,
        'user': User,
    }
    
    model_name_lower = model_name.lower().strip()
    if model_name_lower not in model_map:
        print(f"Unknown model: {model_name}")
        print("Available models:", ", ".join(model_map.keys()))
        return
    
    model = model_map[model_name_lower]
    
    if filter_clause:
        # Check if filter contains a JOIN pattern (e.g., "DocumentClassification.category")
        import re
        
        # Handle JOIN queries (e.g., "DocumentClassification.category = 'mercantil'")
        if 'documentclassification' in filter_clause.lower() or 'classification' in filter_clause.lower():
            # Build JOIN query for Document -> DocumentClassification
            if model_name_lower == 'document':
                # Auto-fix == to = in filter clause
                fixed_filter = re.sub(r'(?<!=)=(?!=)', '=', filter_clause)
                # Extract the condition after the JOIN
                # Handle patterns like "DocumentClassification.category = 'mercantil'"
                condition = fixed_filter
                if 'documentclassification.' in condition.lower():
                    # Replace model name with table alias
                    condition = condition.replace('DocumentClassification.', 'dc.').replace('documentclassification.', 'dc.')
                elif 'classification.' in condition.lower():
                    condition = condition.replace('Classification.', 'dc.').replace('classification.', 'dc.')
                
                query = f"""
                    SELECT COUNT(*) 
                    FROM document d
                    INNER JOIN documentclassification dc ON d.id = dc.document_id
                    WHERE {condition}
                """
                try:
                    result = session.execute(text(query))
                    count = result.scalar()
                    print(f"\n{model_name} (with classification filter): {count} records\n")
                    return
                except Exception as e:
                    print(f"\nError executing count query: {e}")
                    print(f"\nTry using SQL directly:")
                    print(f"SELECT COUNT(*) FROM document d")
                    print(f"INNER JOIN documentclassification dc ON d.id = dc.document_id")
                    print(f"WHERE {condition}\n")
                    return
        
        # Execute SQL COUNT query with filter (simple case)
        try:
            # Auto-fix == to = in filter clause
            fixed_filter = re.sub(r'(?<!=)=(?!=)', '=', filter_clause)
            query = f"SELECT COUNT(*) FROM {model_name_lower} WHERE {fixed_filter}"
            result = session.execute(text(query))
            count = result.scalar()
            print(f"\n{model_name} (filtered): {count} records\n")
            return
        except Exception as e:
            print(f"\nError executing count query: {e}")
            print(f"Try using SQL directly: SELECT COUNT(*) FROM {model_name_lower} WHERE {filter_clause}\n")
            return
    
    count = len(session.exec(select(model)).all())
    print(f"\n{model_name}: {count} records\n")


def execute_sql(session: Session, query: str):
    """Execute a raw SQL query."""
    try:
        # Auto-fix common Python-to-SQL syntax issues
        # Replace == with = (but not ===)
        import re
        fixed_query = re.sub(r'(?<!=)=(?!=)', '=', query)
        
        result = session.execute(text(fixed_query))
        
        # Check if it's a SELECT query (has rows)
        if result.returns_rows:
            rows = result.fetchall()
            if rows:
                # Get column names
                columns = result.keys()
                print(f"\n{len(rows)} row(s) returned:")
                print("-" * 70)
                
                # Print header
                print(" | ".join(str(col) for col in columns))
                print("-" * 70)
                
                # Print rows (limit to first 100 for readability)
                for i, row in enumerate(rows[:100]):
                    print(" | ".join(str(val) if val is not None else "NULL" for val in row))
                    if i >= 99 and len(rows) > 100:
                        print(f"\n... ({len(rows) - 100} more rows)")
                        break
                print("-" * 70)
            else:
                print("\nNo rows returned.")
        else:
            # DDL/DML query
            session.commit()
            print("\nQuery executed successfully.")
            
    except Exception as e:
        print(f"\nError executing query: {e}")
        # Provide helpful hints for common errors
        error_str = str(e).lower()
        if 'syntax error' in error_str or 'invalid' in error_str:
            print("\nTip: SQL uses '=' for equality, not '=='. Use: WHERE column = 'value'")
            print("     Table names are case-insensitive in PostgreSQL (documentclassification = DocumentClassification)")
        session.rollback()


def main():
    """Main interactive console loop."""
    print("=" * 70)
    print("ScanPro Database Console")
    print("=" * 70)
    print(f"Database: {config.settings.database_url}")
    print(f"Environment: {config.settings.node_env_value}")
    print("=" * 70)
    print("\nType 'help' for available commands, 'exit' to quit.")
    print("You can execute SQL queries or use SQLModel operations via 'session'.\n")
    
    # Create database engine
    engine = create_engine(
        config.settings.database_url,
        echo=config.LOG_LEVEL == "DEBUG",
        **get_database_config()
    )
    
    # Create session
    session = Session(engine)
    
    # Make models and session available in the console namespace
    console_globals = {
        'session': session,
        'select': select,
        'Document': Document,
        'DocumentClassification': DocumentClassification,
        'DocumentFeedback': DocumentFeedback,
        'OCRData': OCRData,
        'PDFCache': PDFCache,
        'ProcessingTask': ProcessingTask,
        'EmbeddingMetadata': EmbeddingMetadata,
        'Entity': Entity,
        'User': User,
        'ProcessingTaskStatus': ProcessingTaskStatus,
        'DocumentStatus': DocumentStatus,
    }
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("db> ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nExiting database console. Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    print_help()
                    continue
                
                if user_input.lower() == 'models':
                    print("\nAvailable SQLModel classes:")
                    for name in sorted(console_globals.keys()):
                        if name not in ['session', 'select']:
                            print(f"  - {name}")
                    print()
                    continue
                
                if user_input.lower() == 'tables':
                    list_tables(session)
                    continue
                
                if user_input.lower().startswith('count '):
                    # Case-insensitive split on WHERE
                    import re
                    parts = re.split(r'\s+where\s+', user_input[6:].strip(), flags=re.IGNORECASE, maxsplit=1)
                    model_name = parts[0].strip()
                    filter_clause = parts[1] if len(parts) > 1 else None
                    count_records(session, model_name, filter_clause)
                    continue
                
                # Handle SQL COUNT queries
                if user_input.strip().upper().startswith('SELECT COUNT'):
                    execute_sql(session, user_input)
                    continue
                
                # Try to execute as Python code first (SQLModel operations)
                if user_input.startswith('session.') or user_input.startswith('select('):
                    try:
                        result = eval(user_input, console_globals)
                        if result is not None:
                            # Handle SQLModel results
                            if hasattr(result, '__iter__') and not isinstance(result, str):
                                result_list = list(result) if not isinstance(result, list) else result
                                print(f"\n{len(result_list)} result(s):")
                                for i, item in enumerate(result_list[:20]):
                                    print(f"  [{i}] {item}")
                                if len(result_list) > 20:
                                    print(f"  ... ({len(result_list) - 20} more)")
                            else:
                                print(f"\n{result}")
                            print()
                    except SyntaxError:
                        # Not Python code, try as SQL
                        execute_sql(session, user_input)
                    except Exception as e:
                        print(f"\nError: {e}\n")
                else:
                    # Execute as SQL query
                    execute_sql(session, user_input)
                    
            except KeyboardInterrupt:
                print("\n\nExiting database console. Goodbye!")
                break
            except EOFError:
                print("\n\nExiting database console. Goodbye!")
                break
                
    finally:
        session.close()
        print("Database session closed.")


if __name__ == "__main__":
    main()

