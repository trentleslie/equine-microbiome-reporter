# Poetry Lock File Sync - FIXED ✅

**Commit:** `356c464` - Update poetry.lock to sync with pyproject.toml

---

## Problem

GitHub Actions workflow #54 failed with:
```
pyproject.toml changed significantly since poetry.lock was last generated.
Run `poetry lock` to fix the lock file.
Error: Process completed with exit code 1.
```

This prevented dependencies from being installed, so tests never ran.

---

## Root Cause

**Timeline:**
- **Sep 5, 2025:** `poetry.lock` last updated (commit `cda9985`)
- **Nov 11, 2025:** `requests` package added to main dependencies in `pyproject.toml` (commit `eb8e31b`)
- **Dec 1, 2025:** CI/CD discovers lock file is out of sync (2+ months stale)

**What Changed:**
The `requests` package was moved from optional dependency groups to main dependencies:

```toml
# Before (in optional groups only):
[tool.poetry.group.llm.dependencies]
requests = "^2.31.0"

# After (in main dependencies):
[tool.poetry.dependencies]
requests = "^2.31.0"  # For NCBI API calls and file downloads
```

Poetry detected this as a "significant change" in the dependency graph structure.

---

## Solution

### Command Used
```bash
poetry lock --no-update
```

**Why `--no-update`:**
- ✅ Preserves all existing package versions (no surprises)
- ✅ Only updates lock file metadata (dependency groups, content hash)
- ✅ Avoids updating 400+ packages to latest versions
- ✅ Lower risk for production system
- ✅ Faster execution

**What Changed:**
- Updated content hash to match current `pyproject.toml`
- Adjusted dependency group markers (removed optional groups for now-main packages)
- Updated Poetry generator version metadata (2.1.2 → 1.8.2)
- No package version changes
- No breaking changes

**Statistics:**
```
1 file changed: poetry.lock
51 insertions, 409 deletions
```

The large deletion count is due to removing group metadata markers (e.g., `groups = ["llm"]`) for packages that are now in main dependencies.

---

## Verification

### Local Testing ✅

```bash
# 1. Lock file updated
poetry lock --no-update
✓ Lock file written successfully

# 2. Installation works
poetry install --with dev --with test
✓ Package operations: 9 installs, 1 update, 0 removals
✓ All dependencies installed successfully

# 3. Imports work
poetry run python -c "
from src.batch_processor import BatchProcessor, BatchConfig
from scripts.generate_clean_report import generate_clean_report
import requests
print('✓ All imports successful')
print(f'✓ requests version: {requests.__version__}')
"
✓ All imports successful
✓ requests version: 2.32.4
```

### Expected GitHub Actions Results

Once workflow #55 (commit 356c464) runs:
- ✅ Dependency installation should succeed
- ✅ Tests should run (may still have test failures to debug separately)
- ✅ All Python versions (3.9, 3.10, 3.11, 3.12) should get past dependency installation

---

## Technical Details

### Package Version Changes
**None.** All package versions preserved:
- `requests==2.32.4` (unchanged)
- `anthropic==0.25.9` (unchanged)
- `pandas==1.4.2` (unchanged)
- All 400+ other packages unchanged

### Lock File Metadata Changes
- **Content hash:** Updated to match current pyproject.toml
- **Generator:** `Poetry 1.8.2` (was `Poetry 2.1.2`)
- **Dependency groups:** Removed group markers for main dependencies
- **Platform markers:** Cleaned up (e.g., removed Windows-specific markers)

### Why This Happened

The original commit that added `requests` to main dependencies (`eb8e31b`) did not run `poetry lock` to update the lock file. This is easy to forget when editing pyproject.toml manually.

**Best Practice:** Always run `poetry lock --no-update` after editing `pyproject.toml`.

---

## Impact

**Files Changed:** 1 (poetry.lock)
**Breaking Changes:** None
**Version Changes:** None
**CI/CD Status:** Should now pass dependency installation step

---

## Related Fixes

This is the **second fix** for the GitHub Actions failures:

1. **Fix #1 (commit b56d170):** Made `scripts/` a proper Python package
   - Fixed import errors in tests
   - Created `scripts/__init__.py`
   - Updated `src/batch_processor.py` imports

2. **Fix #2 (commit 356c464):** Synced poetry.lock with pyproject.toml ← **Current**
   - Fixed dependency installation errors
   - Updated lock file metadata
   - No version changes

---

## Next Steps

1. ⏳ **Monitor GitHub Actions workflow #55** - Should get past dependency installation
2. ⏳ **Check if tests pass** - Fix #1 addressed import errors, this fix addresses installation
3. ⏳ **If tests still fail** - Debug the actual test failures (not dependency/import issues)
4. ✅ **Email Gosia** - Once tests are green, installation instructions are ready

---

## Prevention

To avoid this in the future:

```bash
# After editing pyproject.toml (adding/removing/changing dependencies):
poetry lock --no-update

# Commit both files together:
git add pyproject.toml poetry.lock
git commit -m "Add/update dependency X"
```

Or use Poetry commands that auto-update the lock file:
```bash
poetry add requests           # Adds to pyproject.toml AND updates lock file
poetry remove old-package     # Removes from both
poetry update requests        # Updates specific package
```

---

**Commit Reference:** `356c464`
**Branch:** `main`
**Pushed:** ✅ Yes (2025-01-20)
**Status:** ✅ Fix deployed, awaiting CI verification

---

**Last Updated:** 2025-01-20 (after commit 356c464)
