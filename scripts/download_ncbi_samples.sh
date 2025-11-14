#!/bin/bash
#
# Download NCBI FASTQ files for pipeline testing
# Downloads 3 racehorse gut microbiome samples from ENA
#
# Total download size: ~7 GB (6 files, paired-end)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OUTPUT_DIR="data/ncbi_samples"
BASE_URL="http://ftp.sra.ebi.ac.uk/vol1/fastq/SRR211"

# Sample information
declare -A SAMPLES=(
    ["SRR21151045"]="045 2.80"  # directory_suffix total_size_GB
    ["SRR21150809"]="009 2.08"
    ["SRR21150880"]="080 2.10"
)

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}NCBI FASTQ Download Script${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "Downloading 3 racehorse gut microbiome samples"
echo -e "Total size: ~7 GB (6 files, paired-end)"
echo -e "Output directory: ${OUTPUT_DIR}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Function to download a single file
download_file() {
    local url="$1"
    local output_file="$2"
    local accession="$3"

    if [ -f "${output_file}" ]; then
        echo -e "${YELLOW}  File exists, checking size...${NC}"
        local actual_size=$(stat -c%s "${output_file}" 2>/dev/null || echo "0")
        if [ "${actual_size}" -gt 1000000 ]; then
            echo -e "${GREEN}  ✓ File already downloaded ($(numfmt --to=iec-i --suffix=B ${actual_size}))${NC}"
            return 0
        else
            echo -e "${YELLOW}  File incomplete, re-downloading...${NC}"
            rm -f "${output_file}"
        fi
    fi

    echo -e "${BLUE}  Downloading: $(basename ${output_file})${NC}"
    if curl -# -C - -L -o "${output_file}" "${url}"; then
        local size=$(stat -c%s "${output_file}" 2>/dev/null || echo "0")
        echo -e "${GREEN}  ✓ Downloaded successfully ($(numfmt --to=iec-i --suffix=B ${size}))${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Download failed${NC}"
        return 1
    fi
}

# Function to validate FASTQ file
validate_fastq() {
    local file="$1"

    if [ ! -f "${file}" ]; then
        echo -e "${RED}  ✗ File not found: ${file}${NC}"
        return 1
    fi

    # Check if it's a valid gzip file
    if ! gzip -t "${file}" 2>/dev/null; then
        echo -e "${RED}  ✗ Invalid gzip file: ${file}${NC}"
        return 1
    fi

    # Check if it contains FASTQ data (look for @ at start of lines)
    if ! zcat "${file}" 2>/dev/null | head -n 4 | grep -q "^@"; then
        echo -e "${RED}  ✗ Not a valid FASTQ file: ${file}${NC}"
        return 1
    fi

    echo -e "${GREEN}  ✓ Valid FASTQ file: $(basename ${file})${NC}"
    return 0
}

# Track statistics
total_files=0
downloaded_files=0
failed_files=0
start_time=$(date +%s)

# Download each sample
for accession in "${!SAMPLES[@]}"; do
    info=(${SAMPLES[$accession]})
    dir_suffix="${info[0]}"
    size_gb="${info[1]}"

    echo ""
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BLUE}Sample: ${accession}${NC}"
    echo -e "${BLUE}Expected size: ~${size_gb} GB (paired-end)${NC}"
    echo -e "${BLUE}======================================================================${NC}"

    # Create sample directory
    sample_dir="${OUTPUT_DIR}/${accession}"
    mkdir -p "${sample_dir}"

    # Download both paired-end files
    for read_num in 1 2; do
        total_files=$((total_files + 1))

        filename="${accession}_${read_num}.fastq.gz"
        output_file="${sample_dir}/${filename}"
        url="${BASE_URL}/${dir_suffix}/${accession}/${filename}"

        echo ""
        echo -e "${YELLOW}File ${total_files}/6: ${filename}${NC}"

        if download_file "${url}" "${output_file}" "${accession}"; then
            downloaded_files=$((downloaded_files + 1))
        else
            failed_files=$((failed_files + 1))
            echo -e "${RED}Failed to download ${filename}${NC}"
            echo -e "${YELLOW}You can try manually downloading from:${NC}"
            echo -e "${YELLOW}  ${url}${NC}"
        fi
    done
done

# Validation phase
echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}Validating Downloaded Files${NC}"
echo -e "${BLUE}======================================================================${NC}"

valid_files=0
invalid_files=0

for accession in "${!SAMPLES[@]}"; do
    sample_dir="${OUTPUT_DIR}/${accession}"
    echo ""
    echo -e "${YELLOW}Validating: ${accession}${NC}"

    for read_num in 1 2; do
        filename="${accession}_${read_num}.fastq.gz"
        filepath="${sample_dir}/${filename}"

        if validate_fastq "${filepath}"; then
            valid_files=$((valid_files + 1))
        else
            invalid_files=$((invalid_files + 1))
        fi
    done
done

# Calculate statistics
end_time=$(date +%s)
duration=$((end_time - start_time))
minutes=$((duration / 60))
seconds=$((duration % 60))

# Calculate total downloaded size
total_size=$(du -sb "${OUTPUT_DIR}" 2>/dev/null | cut -f1 || echo "0")
total_size_human=$(numfmt --to=iec-i --suffix=B ${total_size})

# Final summary
echo ""
echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}DOWNLOAD COMPLETE${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "Total files: ${total_files}"
echo -e "${GREEN}Downloaded: ${downloaded_files}${NC}"
echo -e "${RED}Failed: ${failed_files}${NC}"
echo -e ""
echo -e "${GREEN}Valid FASTQ files: ${valid_files}${NC}"
echo -e "${RED}Invalid files: ${invalid_files}${NC}"
echo -e ""
echo -e "Total size: ${total_size_human}"
echo -e "Time elapsed: ${minutes}m ${seconds}s"
echo -e ""
echo -e "Files saved to: ${OUTPUT_DIR}/"
echo -e "${BLUE}======================================================================${NC}"

# Exit status
if [ ${failed_files} -gt 0 ] || [ ${invalid_files} -gt 0 ]; then
    echo -e "${RED}⚠️  Some downloads failed or files are invalid${NC}"
    echo -e "${YELLOW}Please check the output above for details${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All files downloaded and validated successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next step: Run the complete pipeline test${NC}"
    echo -e "${YELLOW}poetry run python scripts/full_pipeline.py \\${NC}"
    echo -e "${YELLOW}  --input-dir ${OUTPUT_DIR} \\${NC}"
    echo -e "${YELLOW}  --output-dir results/ncbi_test \\${NC}"
    echo -e "${YELLOW}  --languages en,pl,ja${NC}"
    exit 0
fi
