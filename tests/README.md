# Testing Infrastructure

This directory contains the complete testing infrastructure for the Equine Microbiome Reporter project.

## Setup

1. Install testing dependencies:
```bash
poetry install --with test
```

2. Run all tests:
```bash
poetry run pytest
```

3. Run tests with coverage:
```bash
poetry run pytest --cov=src --cov-report=html
```

## Directory Structure

- `conftest.py` - Shared fixtures and test configuration
- `pytest.ini` - pytest configuration settings
- `fixtures/` - Test data and fixtures
  - `csv_files/` - Sample CSV files for testing
  - `patient_data.py` - Patient information fixtures
  - `microbiome_data.py` - Microbiome data fixtures
  - `config_data.py` - Configuration fixtures
- `utils/` - Testing utilities and helpers
  - `helpers.py` - Common test helper functions
  - `assertions.py` - Custom assertion functions
  - `pdf_validation.py` - PDF validation utilities
- `integration/` - Integration and end-to-end tests
- `test_*.py` - Unit test modules (placeholders for specialized testing agents)

## Test Markers

- `@pytest.mark.unit` - Unit tests (fast)
- `@pytest.mark.integration` - Integration tests (slower)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.pdf` - Tests that generate PDF files
- `@pytest.mark.fastq` - Tests that process FASTQ files

## Running Specific Tests

```bash
# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration

# Skip slow tests
poetry run pytest -m "not slow"

# Run specific test file
poetry run pytest tests/test_data_models.py

# Run with verbose output
poetry run pytest -v
```

## Test Data

The fixtures directory contains realistic test data:

- `sample_normal.csv` - Normal microbiome composition
- `sample_dysbiotic.csv` - Dysbiotic microbiome composition
- `sample_minimal.csv` - Minimal test data
- `test_manifest.csv` - Batch processing manifest

## CI/CD Integration

GitHub Actions workflow is configured in `.github/workflows/tests.yml` to run tests on:
- Multiple Python versions (3.9, 3.10, 3.11, 3.12)
- Push to main/develop branches
- Pull requests

## Coverage Reporting

Coverage reports are generated in:
- `htmlcov/` - HTML coverage report
- `coverage.xml` - XML coverage report (for CI)
- Terminal output with missing lines

Target coverage: 80% minimum (configurable in pytest.ini)

## Future Development

Placeholder test files are ready for implementation by specialized testing agents:
- `test_data_models.py` - Data models testing
- `test_csv_processor.py` - CSV processing testing  
- `test_report_generator.py` - Report generation testing
- `test_batch_processor.py` - Batch processing testing
- `integration/test_end_to_end.py` - End-to-end testing