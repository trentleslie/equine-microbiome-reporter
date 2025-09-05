#!/usr/bin/env python3
"""
Real-time Kraken2 database build monitor
Tracks progress through all phases of the build process
"""

import time
import os
import subprocess
from pathlib import Path
from datetime import datetime

class Kraken2BuildMonitor:
    def __init__(self):
        self.db_path = Path("/home/trentleslie/kraken2_databases/standard")
        self.project_root = Path.home() / "Insync/projects/equine-microbiome-reporter"
        self.start_time = time.time()
    
    def check_process_status(self, process_name):
        """Check if a specific process is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                return True, pids
            return False, []
        except:
            return False, []
    
    def get_file_age(self, filepath):
        """Get age of a file in minutes"""
        if not filepath.exists():
            return None
        age_seconds = time.time() - filepath.stat().st_mtime
        return age_seconds / 60
    
    def check_database_files(self):
        """Check for database build files"""
        files_to_check = {
            "taxonomy/nodes.dmp": "Taxonomy nodes",
            "taxonomy/names.dmp": "Taxonomy names", 
            "library/bacteria": "Bacteria library",
            "seqid2taxid.map": "Sequence ID mapping",
            "hash.k2d": "Hash table (final)",
            "opts.k2d": "Database options (final)",
            "taxo.k2d": "Taxonomy data (final)",
            "taxo.k2d.tmp": "Taxonomy temp file"
        }
        
        status = {}
        for file, desc in files_to_check.items():
            file_path = self.db_path / file
            if file_path.exists():
                size = file_path.stat().st_size if file_path.is_file() else "directory"
                age = self.get_file_age(file_path)
                status[file] = {
                    "exists": True,
                    "description": desc,
                    "size": size,
                    "age_minutes": age
                }
            else:
                status[file] = {"exists": False, "description": desc}
        
        return status
    
    def get_directory_size(self):
        """Get database directory size"""
        try:
            result = subprocess.run(
                ["du", "-sh", str(self.db_path)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.split()[0]
        except:
            pass
        return "Unknown"
    
    def check_log_files(self):
        """Check progress from log files"""
        log_files = [
            (self.project_root / "taxonomy_download.log", "Taxonomy download"),
            (self.project_root / "kraken2_build.log", "Database build")
        ]
        
        logs = {}
        for log_path, desc in log_files:
            if log_path.exists():
                # Read last few lines
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                        last_lines = lines[-5:] if len(lines) >= 5 else lines
                        logs[desc] = {
                            "exists": True,
                            "last_lines": [line.strip() for line in last_lines],
                            "age_minutes": self.get_file_age(log_path)
                        }
                except:
                    logs[desc] = {"exists": True, "error": "Could not read"}
            else:
                logs[desc] = {"exists": False}
        
        return logs
    
    def print_status(self):
        """Print comprehensive status"""
        elapsed = (time.time() - self.start_time) / 60
        print(f"\n{'='*70}")
        print(f"🔍 Kraken2 Database Build Monitor - {datetime.now().strftime('%H:%M:%S')}")
        print(f"Elapsed time: {elapsed:.1f} minutes")
        print(f"{'='*70}")
        
        # Check processes
        print("\n📋 Process Status:")
        taxonomy_running, tax_pids = self.check_process_status("kraken2-build.*download-taxonomy")
        build_running, build_pids = self.check_process_status("kraken2-build.*--build")
        
        print(f"  Taxonomy download: {'✅ Running' if taxonomy_running else '❌ Not running'}")
        if taxonomy_running:
            print(f"    PIDs: {', '.join(tax_pids)}")
        
        print(f"  Database build: {'✅ Running' if build_running else '❌ Not running'}")
        if build_running:
            print(f"    PIDs: {', '.join(build_pids)}")
        
        # Database size
        db_size = self.get_directory_size()
        print(f"\n💾 Database size: {db_size}")
        
        # File status
        print(f"\n📁 File Status:")
        files = self.check_database_files()
        for file, info in files.items():
            if info["exists"]:
                size_info = f" ({info['size']} bytes)" if isinstance(info['size'], int) else f" ({info['size']})"
                age_info = f" - {info['age_minutes']:.1f}min ago" if info.get('age_minutes') else ""
                print(f"  ✅ {file}{size_info}{age_info}")
            else:
                print(f"  ❌ {file} - {info['description']}")
        
        # Log status
        print(f"\n📜 Log Files:")
        logs = self.check_log_files()
        for log_name, info in logs.items():
            if info["exists"] and "last_lines" in info:
                print(f"  📄 {log_name} (updated {info['age_minutes']:.1f}min ago):")
                for line in info["last_lines"]:
                    if line:
                        print(f"    {line}")
            elif info["exists"]:
                print(f"  📄 {log_name}: {info.get('error', 'Present but unreadable')}")
            else:
                print(f"  ❌ {log_name}: Not found")
        
        # Build phase detection
        print(f"\n🔄 Current Phase:")
        if files["taxonomy/nodes.dmp"]["exists"] and files["taxonomy/names.dmp"]["exists"]:
            if files["library/bacteria"]["exists"]:
                if files["hash.k2d"]["exists"] and files["opts.k2d"]["exists"] and files["taxo.k2d"]["exists"]:
                    print("  🎉 BUILD COMPLETE!")
                elif files["taxo.k2d.tmp"]["exists"]:
                    print("  🔨 Database compilation in progress...")
                else:
                    print("  📦 Ready to build database")
            else:
                print("  📥 Downloading bacteria library...")
        else:
            print("  📥 Downloading taxonomy data...")

def main():
    """Run monitoring with periodic updates"""
    monitor = Kraken2BuildMonitor()
    
    try:
        print("🚀 Starting Kraken2 build monitoring...")
        print("Press Ctrl+C to stop monitoring")
        
        check_count = 0
        while True:
            check_count += 1
            monitor.print_status()
            
            # Check if build is complete
            files = monitor.check_database_files()
            if (files["hash.k2d"]["exists"] and 
                files["opts.k2d"]["exists"] and 
                files["taxo.k2d"]["exists"]):
                print(f"\n🎉 DATABASE BUILD COMPLETE! 🎉")
                print(f"Total time: {(time.time() - monitor.start_time) / 3600:.1f} hours")
                break
            
            # Wait between checks (shorter intervals for active monitoring)
            print(f"\n⏱️  Waiting 30 seconds for next check... (Check #{check_count})")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n\nMonitoring stopped by user after {check_count} checks")
        monitor.print_status()

if __name__ == "__main__":
    main()