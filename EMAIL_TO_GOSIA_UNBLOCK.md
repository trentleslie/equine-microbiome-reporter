# Email to Gosia - Installation Fix

---

**Subject:** Quick Fix for Installation Issues

---

Hi Gosia,

Thanks for testing! I've fixed the installation issues you encountered. Here's how to get it working:

## Quick Fix (3 Steps)

```bash
# 1. Remove translation cache and pull updates
cd equine-microbiome-reporter
rm -rf translation_cache/
git pull

# 2. Create the conda environment using new Linux-compatible file
conda env create -f environment_linux.yml

# 3. Activate and test
conda activate equine-microbiome
python scripts/test_installation.py
```

## What Was Fixed

**Issue 1 - Git merge conflict:** The `.gitignore` was missing `translation_cache/` at root level. Fixed.

**Issue 2 & 3 - Conda environment errors:** The original `environment.yml` had platform-specific packages from Windows/macOS. I created `environment_linux.yml` with Linux-compatible dependencies only.

## Verification

After the 3 steps above, verify it's working:

```bash
# Test PDF generation
python -c "
from scripts.generate_clean_report import generate_clean_report
from src.data_models import PatientInfo

patient = PatientInfo(name='TestHorse', sample_number='001')
success = generate_clean_report('data/sample_1.csv', patient, 'test.pdf')
print('✅ Success!' if success else '❌ Failed')
"

# Test multi-language batch processing
python scripts/batch_multilanguage.py \
  --data-dir data/ \
  --output-dir reports/ \
  --languages en pl ja
```

## Workflow Questions (No Rush)

Once you're unblocked, I have a few quick questions about your EPI2ME workflow:

1. Does EPI2ME give you `.kreport` files or CSV files directly?
2. How are files organized for ~15 horses? (one folder per horse, or all in one folder?)
3. For the CSV with 30 barcode columns - is that ONE horse (30 replicates) or 30 different horses?
4. Expected output: 15 horses × 3 languages = 45 PDFs total?

Let me know if you hit any issues!

Best,
Trent

---

**Note:** If you prefer Poetry over Conda (faster, more reliable), see `docs/LINUX_INSTALLATION.md` for instructions.
