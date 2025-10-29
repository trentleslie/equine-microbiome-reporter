# Environment Troubleshooting Guide

This guide helps resolve common conda environment issues with the Equine Microbiome Reporter.

## Common Issues

### Issue 1: cffi/libffi Symbol Error

**Error Message:**
```
ImportError: undefined symbol: ffi_type_uint32, version LIBFFI_BASE_7.0
```

**Cause:** Version mismatch between cffi binary and system libffi library.

**Solution - Quick Fix:**
```bash
conda activate equine-microbiome
pip install --force-reinstall cffi
```

**Solution - Update Environment:**
```bash
conda activate equine-microbiome
conda env update -f environment.yml --prune
```

**Solution - Nuclear Option (rebuild from scratch):**
```bash
conda deactivate
conda env remove -n equine-microbiome
conda env create -f environment.yml
conda activate equine-microbiome
```

**Verification:**
```bash
python -c "from weasyprint import HTML; print('✓ WeasyPrint working')"
```

### Issue 2: Translation Dependencies Missing

**Error Message:**
```
Translation dependencies not found
```

**Cause:** Translation packages not installed in conda environment.

**Solution:**
```bash
conda activate equine-microbiome
pip install deep-translator==1.11.4 googletrans==4.0.0rc1 translatepy==2.3
```

**Verification:**
```bash
python -c "import deep_translator, googletrans, translatepy; print('✓ Translation ready')"
```

### Issue 3: WeasyPrint Missing System Dependencies

**Error Message:**
```
OSError: cannot load library 'gobject-2.0-0'
```

**Cause:** Missing system-level libraries (GTK, Pango, Cairo).

**Solution for Ubuntu/Debian/WSL:**
```bash
sudo apt-get update
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info libcairo2 libpangoft2-1.0-0
```

**Solution for conda-only approach:**
```bash
conda activate equine-microbiome
conda install -c conda-forge cairo pango gdk-pixbuf2
```

### Issue 4: Matplotlib Backend Errors

**Error Message:**
```
ImportError: Cannot load backend 'TkAgg'
```

**Cause:** Qt/Tk display backend not configured for headless operation.

**Solution:** Already handled by `QT_QPA_PLATFORM=offscreen` in demo.sh, but if running scripts manually:
```bash
export QT_QPA_PLATFORM=offscreen
python scripts/generate_clean_report.py
```

### Issue 5: Permission Errors with Conda

**Error Message:**
```
PermissionError: [Errno 13] Permission denied
```

**Cause:** Conda installed in system location without proper permissions.

**Solution:**
```bash
# Option 1: Fix ownership
sudo chown -R $USER:$USER ~/miniconda3

# Option 2: Use user-level conda install
conda config --set channel_priority flexible
```

## Complete Environment Reset

If all else fails, completely rebuild the environment:

### Step 1: Remove Old Environment
```bash
conda deactivate
conda env remove -n equine-microbiome
```

### Step 2: Clean Conda Cache
```bash
conda clean --all -y
```

### Step 3: Recreate Environment
```bash
conda env create -f environment.yml
```

### Step 4: Activate and Verify
```bash
conda activate equine-microbiome

# Test core dependencies
python -c "import pandas, numpy, matplotlib, seaborn; print('✓ Data science libraries OK')"
python -c "from weasyprint import HTML; print('✓ PDF generation OK')"
python -c "import deep_translator; print('✓ Translation OK')"

# Test report generation
python -c "
from scripts.generate_clean_report import generate_clean_report
from src.data_models import PatientInfo
print('✓ All imports successful')
"
```

## Debugging Tips

### Check Python Version
```bash
conda activate equine-microbiome
python --version  # Should be 3.9.x
```

### List Installed Packages
```bash
conda list | grep -E "cffi|weasyprint|deep-translator"
```

### Verify cffi Compatibility
```bash
python << EOF
import cffi
print(f"cffi version: {cffi.__version__}")

ffi = cffi.FFI()
print("✓ cffi FFI works")
EOF
```

### Check libffi System Library
```bash
# Find libffi
ldconfig -p | grep libffi

# Check conda's libffi
find ~/miniconda3/envs/equine-microbiome -name "libffi*"
```

### Test WeasyPrint Step-by-Step
```bash
python << EOF
print("Testing WeasyPrint imports...")

try:
    import cffi
    print("✓ cffi imported")
except Exception as e:
    print(f"✗ cffi failed: {e}")
    exit(1)

try:
    from weasyprint import CSS
    print("✓ WeasyPrint CSS imported")
except Exception as e:
    print(f"✗ WeasyPrint CSS failed: {e}")
    exit(1)

try:
    from weasyprint import HTML
    print("✓ WeasyPrint HTML imported")
except Exception as e:
    print(f"✗ WeasyPrint HTML failed: {e}")
    exit(1)

print("\\n✓ All WeasyPrint components working")
EOF
```

## Environment Variables

Key environment variables for the project:

```bash
# For headless chart generation
export QT_QPA_PLATFORM=offscreen

# For WeasyPrint debugging
export WEASYPRINT_DPI=96
export WEASYPRINT_DEFAULT_FONT_SIZE=10

# For translation service selection
export TRANSLATION_SERVICE=free  # or "google_cloud"

# For conda environment
export CONDA_DEFAULT_ENV=equine-microbiome
```

## Version Compatibility Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.9.23 | Fixed in environment.yml |
| cffi | 1.17.1 | Updated for libffi compatibility |
| weasyprint | 66.0 | Installed via pip |
| deep-translator | 1.11.4 | For free translation |
| googletrans | 4.0.0rc1 | Fallback translator |
| translatepy | 2.3 | Backup translator |
| pandas | 1.4.2 | Data processing |
| matplotlib | 3.9.2 | Charting |
| seaborn | 0.13.2 | Statistical plots |

## Getting Help

1. **Check demo.sh output**: The script now validates dependencies and provides specific error messages
2. **Review error logs**: Full tracebacks are displayed for debugging
3. **Test imports manually**: Use the debugging commands above
4. **Check conda environment**: `conda list` to see all installed packages
5. **Verify system libraries**: `ldconfig -p | grep -E "cairo|pango|gdk"` for system deps

## Common Workflows

### After Pulling New Code
```bash
cd /path/to/equine-microbiome-reporter
conda activate equine-microbiome
conda env update -f environment.yml --prune
./demo.sh
```

### Before Running Production Reports
```bash
conda activate equine-microbiome

# Verify all systems
python -c "from weasyprint import HTML"
python -c "import deep_translator"
python -c "from scripts.generate_clean_report import generate_clean_report"

# Run demo to test
./demo.sh
```

### Installing on New Machine
```bash
# Install conda if needed
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Clone repository
cd ~
git clone <repository-url>
cd equine-microbiome-reporter

# Create environment
conda env create -f environment.yml

# Activate and test
conda activate equine-microbiome
./demo.sh
```

## Known Limitations

1. **cffi/libffi sensitivity**: Binary compatibility between conda cffi and system libffi can be fragile
2. **WeasyPrint font handling**: Some fonts may not render correctly on first run
3. **Translation rate limits**: Free services may throttle requests if used too frequently
4. **Memory usage**: Large reports with many species can use 500MB+ RAM during generation
5. **WSL2 specifics**: File permissions can be tricky between Windows and Linux filesystems

## Support Contact

For persistent issues:
1. Check `docs/TRANSLATION_INSTALL.md` for translation-specific issues
2. Review `docs/TRANSLATION_SETUP.md` for general setup
3. Run `./demo.sh` to see automatic dependency validation
4. Collect error output from:
   - `conda list > conda_packages.txt`
   - `python -c "from weasyprint import HTML"` error output
   - Full traceback from failed report generation

Last updated: 2025-10-28
