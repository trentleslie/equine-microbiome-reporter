# Linux Installation Guide

**Complete installation instructions for Ubuntu/Debian-based Linux systems**

## Quick Start (Recommended: Poetry)

Poetry is the recommended installation method as it's platform-independent and handles dependencies more reliably.

### Prerequisites

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+ and pip
sudo apt install python3.9 python3.9-venv python3-pip -y

# Install system dependencies for WeasyPrint
sudo apt install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info
```

### Install Poetry

```bash
# Install Poetry using the official installer
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH (add this to ~/.bashrc for persistence)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/trentleslie/equine-microbiome-reporter.git
cd equine-microbiome-reporter

# Install dependencies using Poetry
poetry install

# Optional: Install additional features
poetry install --with dev         # Development tools (Jupyter)
poetry install --with llm          # LLM support (OpenAI, Anthropic, etc.)
poetry install --with translation-free  # Free translation services

# Activate the virtual environment
poetry shell
```

### Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your paths (use nano, vim, or your preferred editor)
nano .env
```

**Key settings to configure in `.env`:**

```bash
# If you have Kraken2 database (optional)
KRAKEN2_DB_PATH=/path/to/k2_pluspfp_16gb

# Output directories
DEFAULT_OUTPUT_DIR=/path/to/results
PDF_OUTPUT_DIR=/path/to/pdf_reports
```

### Test Installation

```bash
# Run installation test
poetry run python scripts/test_installation.py

# Generate a test report
poetry run python -c "
from scripts.generate_clean_report import generate_clean_report
from src.data_models import PatientInfo

patient = PatientInfo(name='Montana', sample_number='506')
success = generate_clean_report('data/sample_1.csv', patient, 'test_report.pdf')
print('✅ Success!' if success else '❌ Failed!')
"
```

---

## Alternative: Conda Installation

If you prefer Conda or already have it installed:

### Install Conda (if not already installed)

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Run installer
bash Miniconda3-latest-Linux-x86_64.sh

# Follow prompts, then restart terminal or run:
source ~/.bashrc
```

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/trentleslie/equine-microbiome-reporter.git
cd equine-microbiome-reporter

# Create environment using Linux-specific file
conda env create -f environment_linux.yml

# Activate environment
conda activate equine-microbiome
```

### Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your paths
nano .env
```

### Test Installation

```bash
# Run installation test
python scripts/test_installation.py

# Generate a test report
python -c "
from scripts.generate_clean_report import generate_clean_report
from src.data_models import PatientInfo

patient = PatientInfo(name='Montana', sample_number='506')
success = generate_clean_report('data/sample_1.csv', patient, 'test_report.pdf')
print('✅ Success!' if success else '❌ Failed!')
"
```

---

## Troubleshooting

### Git Merge Conflict with `translation_cache`

If you see this error when pulling:

```
error: The following untracked working tree files would be overwritten by merge:
translation_cache/translation_cache.json
```

**Solution:**

```bash
# Option 1: Remove the cache (safe - will regenerate)
rm -rf translation_cache/

# Option 2: Stash the cache temporarily
git stash --include-untracked
git pull
git stash pop
```

The `.gitignore` has been updated to prevent this in the future.

### Conda Environment Creation Failures

If you see errors like:

```
Package libfoo-1.2.3 is excluded by strict repo priority
nothing provides __win needed by package
```

**Cause:** The original `environment.yml` was exported from a different platform (Windows/macOS) with exact version pins.

**Solutions:**

1. **Use `environment_linux.yml` instead** (Linux-specific, version ranges):
   ```bash
   conda env create -f environment_linux.yml
   ```

2. **Switch to Poetry** (recommended, platform-independent):
   ```bash
   # Remove conda environment if created
   conda env remove -n equine-microbiome

   # Use Poetry instead
   poetry install
   poetry shell
   ```

3. **If you must use the original `environment.yml`**, relax constraints:
   ```bash
   conda config --set channel_priority flexible
   conda env create -f environment.yml --force
   ```

### WeasyPrint Installation Failures

If WeasyPrint fails to install or PDF generation errors occur:

```bash
# Install system dependencies
sudo apt install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info

# If using Poetry, reinstall
poetry install --sync

# If using Conda, reinstall via pip
pip install --force-reinstall weasyprint
```

### Missing Modules or Import Errors

```bash
# Poetry: Ensure you're in the virtual environment
poetry shell

# Conda: Ensure environment is activated
conda activate equine-microbiome

# Verify Python can find modules
python -c "import src.data_models; print('✅ Imports working')"
```

### Permission Errors

If you encounter permission errors when creating files/directories:

```bash
# Ensure output directories are writable
mkdir -p results reports temp_charts
chmod 755 results reports temp_charts

# If using sudo, don't - use user permissions instead
# BAD:  sudo python script.py
# GOOD: python script.py
```

---

## Verification Checklist

After installation, verify everything works:

- [ ] Python 3.9+ installed: `python --version`
- [ ] Poetry or Conda environment activated
- [ ] Can import modules: `python -c "import src.data_models"`
- [ ] WeasyPrint works: `python -c "import weasyprint"`
- [ ] Translation services: `python -c "from deep_translator import GoogleTranslator"`
- [ ] Test report generates: `python scripts/test_installation.py`
- [ ] Sample PDF created: Check for `test_report.pdf`

---

## Next Steps

Once installation is complete:

1. **Generate your first report:**
   ```bash
   poetry run python -c "
   from scripts.generate_clean_report import generate_clean_report
   from src.data_models import PatientInfo

   patient = PatientInfo(name='YourHorse', sample_number='001')
   generate_clean_report('data/your_data.csv', patient, 'report.pdf')
   "
   ```

2. **Process multiple samples:**
   ```bash
   poetry run python scripts/batch_multilanguage.py \
     --data-dir data/ \
     --output-dir reports/ \
     --languages en pl ja
   ```

3. **Explore interactive notebooks:**
   ```bash
   poetry run jupyter notebook notebooks/batch_processing.ipynb
   ```

---

## Getting Help

- **Documentation:** See `CLAUDE.md` for commands and architecture
- **Issues:** Check existing troubleshooting in this guide
- **Examples:** Review `notebooks/` for interactive tutorials
- **Test data:** Sample CSV files in `data/` directory

---

## Platform Differences

### Poetry vs Conda

| Feature | Poetry (Recommended) | Conda |
|---------|---------------------|-------|
| Platform independence | ✅ Excellent | ⚠️ Can have issues |
| Dependency resolution | ✅ Modern solver | ⚠️ Can be slow |
| Virtual environments | ✅ Automatic | ⚠️ Manual activation |
| Lock files | ✅ Yes (`poetry.lock`) | ❌ No |
| Development workflow | ✅ Great (`poetry add`) | ⚠️ Manual |
| Scientific packages | ✅ Via PyPI | ✅ Via conda-forge |

### Why `environment_linux.yml` instead of `environment.yml`?

The original `environment.yml` was exported with:
- **Exact version pins** (e.g., `python=3.9.23` instead of `python=3.9.*`)
- **Platform-specific packages** (Windows `__win`, macOS `__osx` virtual packages)
- **Build-specific dependencies** (tied to specific conda builds)

The new `environment_linux.yml` uses:
- **Version ranges** (e.g., `python=3.9.*`, `numpy>=1.21,<2.0`)
- **No platform markers** (works on any Linux distribution)
- **Minimal dependencies** (only what's needed for core functionality)

This makes it portable across different Linux systems and conda versions.

---

**Last Updated:** 2025-01-20
