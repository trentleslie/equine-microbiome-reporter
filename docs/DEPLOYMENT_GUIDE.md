# HippoVet+ Clinical Filtering System - Deployment Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [Integration with Epi2Me](#integration-with-epi2me)
5. [Troubleshooting](#troubleshooting)
6. [Performance Optimization](#performance-optimization)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11 with WSL (Windows Subsystem for Linux)
- **WSL Version**: WSL1 or WSL2 (WSL1 tested with client setup)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 10GB free space
- **Python**: 3.9 or higher
- **Epi2Me**: Already installed and configured

### Recommended Setup
- Windows 11 with WSL2 for better performance
- 16GB RAM for processing large FASTQ files
- SSD storage for faster I/O operations
- Conda/Miniconda for package management

## Installation Steps

### Step 1: Enable WSL (if not already enabled)

Open PowerShell as Administrator and run:

```powershell
# Enable WSL
wsl --install

# For WSL1 (if compatibility issues with WSL2):
wsl --set-default-version 1

# Install Ubuntu
wsl --install -d Ubuntu-22.04
```

### Step 2: Access WSL Environment

Open Windows Terminal or Command Prompt:

```bash
wsl
```

### Step 3: Download Installation Package

In WSL terminal:

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/trentleslie/equine-microbiome-reporter.git
cd equine-microbiome-reporter

# Or download the deployment package
wget https://github.com/trentleslie/equine-microbiome-reporter/releases/download/v1.0/clinical-filter-deployment.zip
unzip clinical-filter-deployment.zip
```

### Step 4: Run Automated Installer

```bash
# Make installer executable
chmod +x deployment/windows_installer.py

# Run installer (for WSL1)
python3 deployment/windows_installer.py --wsl-version 1

# Or for WSL2
python3 deployment/windows_installer.py --wsl-version 2
```

The installer will:
- ✅ Check system prerequisites
- ✅ Install Miniconda if needed
- ✅ Create conda environment with all dependencies
- ✅ Install Kraken2 and Bracken
- ✅ Configure for Windows/WSL paths
- ✅ Create convenient shortcuts
- ✅ Validate the installation

### Step 5: Verify Installation

```bash
# Run validation script
./clinical-filter validate

# Expected output:
# ✅ All modules imported successfully
# ✅ Core components initialized
# ✅ PlusPFP-16 configuration loaded
# ✅ EuPathDB configuration loaded
# ✅ Viral configuration loaded
# ✅ Installation validation PASSED
```

## Configuration

### Database Paths Configuration

Edit `config/wsl_config.json`:

```json
{
  "windows_paths": {
    "databases": "/mnt/c/Users/hippovet/Desktop/databases",
    "sequencing_data": "/mnt/c/Users/hippovet/Desktop/sequencing_data",
    "epi2me_output": "/mnt/c/Users/hippovet/epi2melabs/instances"
  },
  "databases": {
    "PlusPFP-16": {
      "path": "/mnt/c/Users/hippovet/Desktop/databases/PlusPFP-16",
      "min_abundance": 0.1,
      "auto_exclude_kingdoms": ["Archaea", "Plantae"]
    },
    "EuPathDB": {
      "path": "/mnt/c/Users/hippovet/Desktop/databases/EuPathDB",
      "min_abundance": 0.5,
      "require_manual_review": true
    },
    "Viral": {
      "path": "/mnt/c/Users/hippovet/Desktop/databases/Viral",
      "min_abundance": 0.1,
      "include_patterns": ["equine", "mammalian"]
    }
  }
}
```

### Clinical Filter Rules

Customize filtering rules in `config/clinical_filters.json`:

```json
{
  "exclude_genera": [
    "Phytophthora", "Pythium", "Fusarium",
    "Chlorella", "Paramecium", "Tetrahymena"
  ],
  "high_priority_pathogens": [
    "Streptococcus equi",
    "Rhodococcus equi",
    "Clostridium difficile"
  ],
  "abundance_thresholds": {
    "high_relevance": 10.0,
    "moderate_relevance": 1.0,
    "low_relevance": 0.1
  }
}
```

## Integration with Epi2Me

### Automatic Processing After Epi2Me

Create a batch file on Windows Desktop (`ProcessKraken2.bat`):

```batch
@echo off
echo Processing Kraken2 results with clinical filter...

REM Get the latest Epi2Me output directory
for /f "tokens=*" %%a in ('wsl ls -t /mnt/c/Users/hippovet/epi2melabs/instances ^| head -1') do set LATEST=%%a

REM Process with clinical filter
wsl ~/equine-clinical-filter/clinical-filter filter ^
  --input /mnt/c/Users/hippovet/epi2melabs/instances/%LATEST%/output ^
  --database PlusPFP-16 ^
  --output /mnt/c/Users/hippovet/Desktop/filtered_results

echo Processing complete! Check filtered_results folder on Desktop.
pause
```

### Manual Processing

After Epi2Me completes analysis:

```bash
# In WSL terminal
cd ~/equine-clinical-filter

# Process the latest Epi2Me run
./clinical-filter filter \
  --input /mnt/c/Users/hippovet/epi2melabs/instances/wf-metagenomics_[ID]/output \
  --database PlusPFP-16

# Review Excel file will be created in:
# /mnt/c/Users/hippovet/Desktop/curation_results/
```

### Batch Processing Multiple Databases

```bash
# Process all three databases
for db in PlusPFP-16 EuPathDB Viral; do
  ./clinical-filter filter \
    --input /mnt/c/Users/hippovet/epi2melabs/instances/[ID]/output \
    --database $db
done
```

## Excel Review Workflow

### Opening Review Files

1. Navigate to `C:\Users\hippovet\Desktop\curation_results\`
2. Open the Excel file: `[Database]_review_[timestamp].xlsx`
3. Review the color-coded species list:
   - 🔴 **Red (High)**: Known pathogens - usually include
   - 🟡 **Orange (Moderate)**: Review based on abundance
   - 🔵 **Blue (Low)**: Commensal organisms
   - ⚪ **Gray (Excluded)**: Already filtered out

### Making Decisions

1. In the `include_in_report` column, enter:
   - `YES` to include the species
   - `NO` to exclude the species
2. Add notes in `reviewer_notes` column if needed
3. Save the file when complete

### Importing Decisions

```bash
# Import reviewed Excel file
python3 -c "
from src.curation_interface import CurationInterface
curator = CurationInterface()
df = curator.import_excel_decisions('/mnt/c/Users/hippovet/Desktop/curation_results/PlusPFP-16_review_*.xlsx')
print(f'Imported {len(df)} species for report')
"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. WSL Cannot Access Windows Files

**Error**: `/mnt/c/` not accessible

**Solution**:
```bash
# Check WSL mount
mount | grep mnt

# If not mounted, manually mount
sudo mkdir /mnt/c
sudo mount -t drvfs C: /mnt/c
```

#### 2. Permission Denied Errors

**Error**: Permission denied when accessing database files

**Solution**:
```bash
# In WSL, add to ~/.bashrc
umask 022

# Or change Windows folder permissions
# Right-click folder → Properties → Security → Edit
# Give "Everyone" read permissions
```

#### 3. Memory Issues with Large Files

**Error**: Out of memory processing 3GB+ files

**Solution for WSL1**:
```bash
# Create .wslconfig in Windows user directory
# C:\Users\hippovet\.wslconfig

[wsl2]
memory=8GB
swap=2GB
```

**Solution for WSL1**: Process in chunks
```bash
./clinical-filter filter --input [path] --chunk-size 100
```

#### 4. Conda Environment Not Activating

**Error**: Module not found errors

**Solution**:
```bash
# Manually activate environment
source ~/miniconda3/bin/activate equine-clinical

# Verify environment
conda info --envs
```

#### 5. Kraken2 Database Not Found

**Error**: Database validation failed

**Solution**:
```bash
# Check database files exist
ls -la /mnt/c/Users/hippovet/Desktop/databases/PlusPFP-16/

# Should see: hash.k2d, opts.k2d, taxo.k2d
# If missing, re-download or copy from backup
```

## Performance Optimization

### For WSL1 (Limited Resources)

```python
# Edit config/performance.json
{
  "wsl1_optimizations": {
    "max_threads": 4,
    "chunk_size_mb": 100,
    "use_memory_mapping": false,
    "cache_size_mb": 500
  }
}
```

### For WSL2 (Better Performance)

```python
# Edit config/performance.json  
{
  "wsl2_optimizations": {
    "max_threads": 8,
    "chunk_size_mb": 500,
    "use_memory_mapping": true,
    "cache_size_mb": 2000
  }
}
```

### Processing Time Estimates

| File Size | WSL1 Time | WSL2 Time |
|-----------|-----------|-----------|
| 1 GB      | 10-15 min | 5-8 min   |
| 3 GB      | 30-40 min | 15-20 min |
| 5 GB      | 50-60 min | 25-30 min |

### Monitoring Performance

```bash
# Monitor resource usage during processing
./clinical-filter filter --input [path] --monitor

# View performance report
cat performance_report.txt
```

## Updating the System

### Check for Updates

```bash
# In WSL terminal
cd ~/equine-microbiome-reporter
git pull origin main

# Re-run installer to update
python3 deployment/windows_installer.py --update
```

### Backup Configuration

Before updating, backup your configurations:

```bash
cp -r config config_backup_$(date +%Y%m%d)
```

## Support

### Getting Help

- **Documentation**: See `docs/` folder
- **Issues**: Report at https://github.com/trentleslie/equine-microbiome-reporter/issues
- **Email**: trentleslie@gmail.com

### Diagnostic Information

If you encounter issues, run:

```bash
./clinical-filter diagnose > diagnostic_report.txt
```

Include this report when requesting support.

## Quick Reference Card

### Essential Commands

```bash
# Process Epi2Me output
./clinical-filter filter --input [epi2me_output] --database [DB_NAME]

# Export for Excel review  
./clinical-filter review [input_file] [database_name]

# Validate installation
./clinical-filter validate

# Run diagnostics
./clinical-filter diagnose

# Show help
./clinical-filter --help
```

### File Locations

- **Installation**: `~/equine-clinical-filter/`
- **Configurations**: `~/equine-clinical-filter/config/`
- **Excel Reviews**: `/mnt/c/Users/hippovet/Desktop/curation_results/`
- **Epi2Me Output**: `/mnt/c/Users/hippovet/epi2melabs/instances/`
- **Databases**: `/mnt/c/Users/hippovet/Desktop/databases/`

### Workflow Summary

1. **Run Epi2Me** → Generates Kraken2 output
2. **Run Clinical Filter** → Applies automated filtering
3. **Review Excel** → Manual curation of moderate relevance species
4. **Import Decisions** → Generate final filtered dataset
5. **Create Report** → Generate PDF report for clients

---

*Last Updated: September 2024*
*Version: 1.0.0*