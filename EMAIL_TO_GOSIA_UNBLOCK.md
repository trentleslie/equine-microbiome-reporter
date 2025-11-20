# Email to Gosia - Unblocking Installation Issues

---

**Subject:** Quick Fixes for Installation Issues (3 Simple Steps)

---

Hi Gosia,

Thanks for testing the installation! I've identified and fixed all three issues you encountered. Here's how to get unblocked:

## Issue 1: Git Merge Conflict - FIXED ✅

**Error you saw:**
```
error: The following untracked working tree files would be overwritten by merge:
translation_cache/translation_cache.json
```

**Quick fix:**
```bash
cd equine-microbiome-reporter

# Remove the translation cache (it's safe - will regenerate automatically)
rm -rf translation_cache/

# Now pull the latest changes
git pull
```

**What was the problem?** The `.gitignore` file was missing the root-level `translation_cache/` directory. I've fixed this in the latest commit, so this won't happen again.

---

## Issue 2 & 3: Conda Environment - FIXED ✅

**Errors you saw:**
```
CondaEnvironmentNotFoundError: Could not find conda environment: equine-microbiome
PackagesNotFoundError: The following packages are not available from current channels
```

**Root cause:** The `environment.yml` file was created on a different system and has platform-specific packages that don't work on Linux.

**Solution - Choose ONE of these options:**

### OPTION A: Use Poetry (RECOMMENDED) 🌟

Poetry is platform-independent and will work reliably:

```bash
cd equine-microbiome-reporter

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Install all dependencies
poetry install

# Activate the environment
poetry shell

# Test that it works
python scripts/test_installation.py
```

### OPTION B: Use New Linux Environment File

I've created a Linux-specific conda environment file:

```bash
cd equine-microbiome-reporter

# Create environment using the new Linux file
conda env create -f environment_linux.yml

# Activate environment
conda activate equine-microbiome

# Test that it works
python scripts/test_installation.py
```

---

## Complete Fresh Start (If Needed)

If you want to start completely fresh:

```bash
# 1. Remove any existing conda environment
conda env remove -n equine-microbiome

# 2. Go to your project directory
cd equine-microbiome-reporter

# 3. Remove translation cache
rm -rf translation_cache/

# 4. Pull latest changes
git pull

# 5. Choose either Poetry (Option A) or Conda (Option B) from above
```

---

## Verification Steps

After installation, verify everything works:

```bash
# Check you're in the right environment
# For Poetry:
poetry shell

# For Conda:
conda activate equine-microbiome

# Test imports
python -c "import src.data_models; print('✅ Imports working!')"

# Test PDF generation
python -c "
from scripts.generate_clean_report import generate_clean_report
from src.data_models import PatientInfo

patient = PatientInfo(name='TestHorse', sample_number='001')
success = generate_clean_report('data/sample_1.csv', patient, 'test.pdf')
print('✅ PDF generation working!' if success else '❌ Failed')
"
```

---

## Which Option Should You Choose?

**Use Poetry if:**
- You want the most reliable, platform-independent setup
- You're open to learning a modern Python tool
- You want faster dependency resolution

**Use Conda if:**
- You're already familiar with conda
- You have other conda environments you use
- You prefer to stick with what you know

Both will work perfectly - Poetry is just slightly more modern and portable.

---

## Detailed Documentation

For complete step-by-step instructions with screenshots and troubleshooting, see:

📖 **[docs/LINUX_INSTALLATION.md](docs/LINUX_INSTALLATION.md)**

This guide includes:
- Complete installation steps for both Poetry and Conda
- System dependency installation (for WeasyPrint PDF generation)
- Troubleshooting for common issues
- Verification checklist
- Next steps after installation

---

## Testing the Multi-Language Batch Processing

Once installation is complete, test the new multi-language feature:

```bash
# Generate reports in English, Polish, and Japanese
poetry run python scripts/batch_multilanguage.py \
  --data-dir data/ \
  --output-dir reports/ \
  --languages en pl ja

# Or with conda:
python scripts/batch_multilanguage.py \
  --data-dir data/ \
  --output-dir reports/ \
  --languages en pl ja
```

This will generate 3 PDFs per sample (one in each language).

---

## Questions About Your Workflow

Once you're unblocked, I have a few questions about the EPI2ME workflow to ensure the batch processing matches your needs:

1. **EPI2ME Starting Point**: Does EPI2ME produce `.kreport` files (Kraken2 reports) or does it give you CSV files directly?

2. **File Organization**: For a batch of ~15 horses, how are the files organized?
   - One folder per horse?
   - All `.kreport` files in one folder?
   - Something else?

3. **Barcode Mapping**: In the CSV file with 30 barcode columns:
   - Is this ONE horse with 30 technical replicates?
   - Or is this 30 different horses, each in a barcode column?

4. **Expected Output**: You want:
   - 15 individual PDF reports (one per horse)?
   - Each report in 3 languages (en, pl, ja)?
   - Total of 45 PDFs?

No rush on these - let's get you unblocked first!

---

## Summary

**To get started immediately:**

1. `rm -rf translation_cache/`
2. `git pull`
3. Choose Poetry (recommended) or Conda with `environment_linux.yml`
4. Test with `python scripts/test_installation.py`

Let me know how it goes! If you hit any issues, send me the exact error message and I'll help troubleshoot.

Best regards,
Trent

---

**Files Changed in This Update:**
- ✅ Fixed `.gitignore` to include `translation_cache/` at root level
- ✅ Created `environment_linux.yml` with platform-independent dependencies
- ✅ Added complete Linux installation guide in `docs/LINUX_INSTALLATION.md`
- ✅ Updated `README.md` with Linux quick start
- ✅ Updated `CLAUDE.md` with troubleshooting section
