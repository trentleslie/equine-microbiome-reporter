#!/usr/bin/env python3
"""
Monitor Kraken2 database build progress
"""

import time
import os
from pathlib import Path
import subprocess

def check_database_files():
    """Check for Kraken2 database files"""
    db_path = Path("/home/trentleslie/kraken2_databases/standard")
    
    # Core database files created during build
    db_files = {
        "hash.k2d": "Main hash table",
        "opts.k2d": "Database options", 
        "taxo.k2d": "Taxonomy data"
    }
    
    found_files = {}
    for file, desc in db_files.items():
        file_path = db_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            found_files[file] = (desc, size)
    
    return found_files, len(found_files) == len(db_files)

def check_build_process():
    """Check if kraken2-build process is still running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "kraken2-build.*--build"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def get_database_size():
    """Get total database directory size"""
    db_path = Path("/home/trentleslie/kraken2_databases/standard")
    try:
        result = subprocess.run(
            ["du", "-sh", str(db_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.split()[0]
    except:
        pass
    return "Unknown"

def monitor_build():
    """Monitor database build progress"""
    print("🔍 Kraken2 Database Build Monitor")
    print("=" * 50)
    
    start_time = time.time()
    check_count = 0
    
    while True:
        check_count += 1
        current_time = time.time()
        elapsed = current_time - start_time
        
        print(f"\n--- Check #{check_count} (Elapsed: {elapsed/60:.1f} minutes) ---")
        
        # Check if build process is running
        process_running = check_build_process()
        print(f"Build process running: {'✅ Yes' if process_running else '❌ No'}")
        
        # Check database size
        db_size = get_database_size()
        print(f"Database directory size: {db_size}")
        
        # Check for database files
        found_files, build_complete = check_database_files()
        
        if found_files:
            print("Found database files:")
            for file, (desc, size) in found_files.items():
                print(f"  ✅ {file}: {desc} ({size:,} bytes)")
        else:
            print("No database files found yet (build still in progress)")
        
        if build_complete:
            print("\n🎉 Database build appears complete!")
            print("All required database files found.")
            break
        
        if not process_running:
            print("\n⚠️  Build process not found - may have completed or failed")
            break
        
        # Wait 5 minutes between checks
        print("Waiting 5 minutes before next check...")
        time.sleep(300)
    
    total_time = (time.time() - start_time) / 60
    print(f"\nTotal monitoring time: {total_time:.1f} minutes")
    
    return build_complete

if __name__ == "__main__":
    try:
        completed = monitor_build()
        if completed:
            print("\n✅ Ready to test Kraken2 functionality!")
        else:
            print("\n⚠️  Monitor ended - check build status manually")
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")