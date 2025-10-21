#!/usr/bin/env python3
"""
Development Database Runner
Runs a PostgreSQL container using configuration from backend/config.py
"""

import subprocess
import sys
from pathlib import Path

# Add backend to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import config

def run_postgres_container():
    """Run PostgreSQL container with configuration from config.py"""
    
    # Get configuration values
    postgres_user = config.settings.postgres_username
    postgres_password = config.settings.postgres_password
    postgres_db = config.settings.postgres_db_name
    postgres_host = config.settings.postgres_host
    postgres_port = config.settings.postgres_port
    
    # Get paths
    db_dir = str(config.DB_DIR.resolve())
    script_dir = Path(__file__).parent
    dev_config_dir = script_dir / "dev_db_config"
    
    print(f"🐘 Starting PostgreSQL container...")
    print(f"   Database: {postgres_db}")
    print(f"   User: {postgres_user}")
    print(f"   Host: {postgres_host}:{postgres_port}")
    print(f"   Data Directory: {db_dir}")
    print(f"   Config Directory: {dev_config_dir}")
    print()
    
    # Docker run command with config file mounts (interactive mode)
    docker_cmd = [
        "docker", "run", "-it", "--rm",
        "--name", "scanpro-postgres",
        "-p", f"{postgres_port}:5432",
        "-v", f"{db_dir}:/var/lib/postgresql/data",
        "-v", f"{dev_config_dir}/postgresql.conf:/etc/postgresql/postgresql.conf",
        "-v", f"{dev_config_dir}/pg_hba.conf:/etc/postgresql/pg_hba.conf",
        "-e", f"POSTGRES_USER={postgres_user}",
        "-e", f"POSTGRES_PASSWORD={postgres_password}",
        "-e", f"POSTGRES_DB={postgres_db}",
        "postgres:17",
        "-c", "config_file=/etc/postgresql/postgresql.conf",
        "-c", "hba_file=/etc/postgresql/pg_hba.conf"
    ]
    
    try:
        print(f"✅ PostgreSQL container starting...")
        print(f"   Connection string: postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}")
        print("   Using configuration from dev_db_config/")
        print()
        print("🛑 Press Ctrl+C to stop the container")
        print()
        
        subprocess.run(docker_cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start PostgreSQL container: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Stopping PostgreSQL container...")
        return True
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker and try again.")
        return False
    
    return True

def main():
    """Main function"""
    run_postgres_container()

if __name__ == "__main__":
    main()
