"""
NCBI FASTQ Downloader Module

Downloads FASTQ files from NCBI SRA using either:
1. SRA Toolkit (prefetch + fasterq-dump) - recommended
2. Direct FASTQ URL download - fallback

Designed for testing and demonstration purposes.
"""

import subprocess
import requests
import logging
import shutil
import gzip
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time
import json

logger = logging.getLogger(__name__)


@dataclass
class SRAMetadata:
    """Metadata extracted from SRA accession"""
    accession: str
    organism: str = "Unknown"
    sample_name: str = "Unknown"
    library_strategy: str = "Unknown"
    platform: str = "Unknown"
    total_spots: int = 0
    total_bases: int = 0


class NCBIDownloader:
    """
    Downloads FASTQ files from NCBI SRA database.

    Features:
    - SRA Toolkit integration (prefetch + fasterq-dump)
    - Direct ENA/NCBI FASTQ URL download as fallback
    - Metadata extraction via NCBI E-utilities
    - Progress tracking and logging
    - Automatic directory organization
    """

    def __init__(self, output_dir: Path = Path("ncbi_downloads")):
        """
        Initialize NCBI downloader.

        Args:
            output_dir: Base directory for downloaded files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check SRA toolkit availability
        self.sra_tools_available = self._check_sra_tools()

    def _check_sra_tools(self) -> bool:
        """Check if SRA toolkit is installed and accessible"""
        try:
            result = subprocess.run(
                ['prefetch', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"SRA Toolkit found: {result.stdout.strip()}")
                return True
            else:
                logger.warning("prefetch command found but returned error")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError, OSError) as e:
            logger.warning(f"SRA Toolkit not found ({e.__class__.__name__}). Will use direct URL download as fallback.")
            return False

    def get_metadata(self, accession: str) -> SRAMetadata:
        """
        Fetch metadata for an SRA accession via NCBI E-utilities.

        Args:
            accession: SRA accession (e.g., SRR12345678)

        Returns:
            SRAMetadata object with extracted information
        """
        logger.info(f"Fetching metadata for {accession}")

        try:
            # Use E-utilities to get metadata
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                'db': 'sra',
                'id': accession,
                'rettype': 'runinfo',
                'retmode': 'text'
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Parse CSV response (first line is header)
            lines = response.text.strip().split('\n')
            if len(lines) < 2:
                logger.warning(f"No metadata found for {accession}")
                return SRAMetadata(accession=accession)

            # Parse header and data
            header = lines[0].split(',')
            data = lines[1].split(',')

            # Create dict for easier access
            metadata_dict = dict(zip(header, data))

            # Extract relevant fields
            metadata = SRAMetadata(
                accession=accession,
                organism=metadata_dict.get('Organism', 'Unknown'),
                sample_name=metadata_dict.get('SampleName', accession),
                library_strategy=metadata_dict.get('LibraryStrategy', 'Unknown'),
                platform=metadata_dict.get('Platform', 'Unknown'),
                total_spots=int(metadata_dict.get('spots', 0) or 0),
                total_bases=int(metadata_dict.get('bases', 0) or 0)
            )

            logger.info(f"Metadata: {metadata.organism} - {metadata.sample_name}")
            return metadata

        except Exception as e:
            logger.error(f"Failed to fetch metadata for {accession}: {e}")
            return SRAMetadata(accession=accession)

    def download_with_sra_toolkit(self, accession: str, output_path: Path) -> bool:
        """
        Download FASTQ using SRA Toolkit (prefetch + fasterq-dump).

        Args:
            accession: SRA accession (e.g., SRR12345678)
            output_path: Directory to save FASTQ files

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Downloading {accession} with SRA Toolkit...")

        try:
            # Step 1: Prefetch the SRA file
            logger.info(f"Step 1/2: Prefetching {accession}...")
            prefetch_result = subprocess.run(
                ['prefetch', accession, '--output-directory', str(output_path)],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if prefetch_result.returncode != 0:
                logger.error(f"Prefetch failed: {prefetch_result.stderr}")
                return False

            logger.info(f"Prefetch complete for {accession}")

            # Step 2: Convert to FASTQ
            logger.info(f"Step 2/2: Converting {accession} to FASTQ...")

            # fasterq-dump output directory
            fastq_output = output_path / accession
            fastq_output.mkdir(parents=True, exist_ok=True)

            fasterq_result = subprocess.run(
                [
                    'fasterq-dump',
                    accession,
                    '--outdir', str(fastq_output),
                    '--split-files',  # Split paired-end reads
                    '--threads', '4',
                    '--progress'
                ],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if fasterq_result.returncode != 0:
                logger.error(f"fasterq-dump failed: {fasterq_result.stderr}")
                return False

            logger.info(f"Successfully downloaded {accession}")

            # Compress FASTQ files with gzip
            self._compress_fastq_files(fastq_output)

            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Download timeout for {accession}")
            return False
        except Exception as e:
            logger.error(f"SRA Toolkit download failed: {e}")
            return False

    def download_from_ena_url(self, accession: str, output_path: Path) -> bool:
        """
        Download FASTQ directly from ENA (European Nucleotide Archive) FTP.
        Fallback method when SRA Toolkit is not available.

        Args:
            accession: SRA accession (e.g., SRR12345678)
            output_path: Directory to save FASTQ files

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Downloading {accession} from ENA FTP...")

        try:
            # ENA FTP URL pattern
            # Example: ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR123/045/SRR12345678/SRR12345678.fastq.gz

            # Extract accession parts for URL construction
            prefix = accession[:6]
            last_digits = accession[-6:] if len(accession) >= 9 else ""

            # Try multiple URL patterns
            url_patterns = [
                f"ftp://ftp.sra.ebi.ac.uk/vol1/fastq/{prefix}/{accession}/{accession}.fastq.gz",
                f"ftp://ftp.sra.ebi.ac.uk/vol1/fastq/{prefix}/{last_digits}/{accession}/{accession}.fastq.gz",
                f"ftp://ftp.sra.ebi.ac.uk/vol1/fastq/{prefix}/{accession}/{accession}_1.fastq.gz",
                f"ftp://ftp.sra.ebi.ac.uk/vol1/fastq/{prefix}/{last_digits}/{accession}/{accession}_1.fastq.gz",
            ]

            fastq_output = output_path / accession
            fastq_output.mkdir(parents=True, exist_ok=True)

            success = False
            for url in url_patterns:
                logger.info(f"Trying URL: {url}")

                try:
                    # Use wget for FTP download (more reliable than requests for FTP)
                    wget_result = subprocess.run(
                        ['wget', '-P', str(fastq_output), url],
                        capture_output=True,
                        text=True,
                        timeout=3600
                    )

                    if wget_result.returncode == 0:
                        logger.info(f"Successfully downloaded from {url}")
                        success = True

                        # Check for paired-end file
                        if "_1.fastq.gz" in url:
                            url_2 = url.replace("_1.fastq.gz", "_2.fastq.gz")
                            logger.info(f"Downloading paired-end file: {url_2}")
                            subprocess.run(
                                ['wget', '-P', str(fastq_output), url_2],
                                capture_output=True,
                                timeout=3600
                            )
                        break

                except Exception as e:
                    logger.debug(f"Failed with URL {url}: {e}")
                    continue

            if success:
                logger.info(f"Successfully downloaded {accession} from ENA")
                return True
            else:
                logger.error(f"All URL patterns failed for {accession}")
                return False

        except Exception as e:
            logger.error(f"ENA download failed: {e}")
            return False

    def _compress_fastq_files(self, directory: Path):
        """Compress all .fastq files in directory with gzip"""
        for fastq_file in directory.glob("*.fastq"):
            logger.info(f"Compressing {fastq_file.name}...")

            gz_file = fastq_file.with_suffix('.fastq.gz')

            with open(fastq_file, 'rb') as f_in:
                with gzip.open(gz_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove original uncompressed file
            fastq_file.unlink()
            logger.info(f"Compressed to {gz_file.name}")

    def download_accession(self, accession: str, barcode: Optional[str] = None) -> Tuple[bool, Path]:
        """
        Download a single SRA accession.

        Args:
            accession: SRA accession (e.g., SRR12345678)
            barcode: Optional barcode name (e.g., barcode01) for organization

        Returns:
            Tuple of (success: bool, output_path: Path)
        """
        logger.info(f"=" * 60)
        logger.info(f"Starting download: {accession}")
        logger.info(f"=" * 60)

        # Create output directory (use barcode if provided)
        if barcode:
            output_path = self.output_dir / barcode
        else:
            output_path = self.output_dir / accession

        output_path.mkdir(parents=True, exist_ok=True)

        # Get metadata first
        metadata = self.get_metadata(accession)

        # Save metadata to JSON
        metadata_file = output_path / f"{accession}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata.__dict__, f, indent=2)

        # Attempt download
        success = False

        if self.sra_tools_available:
            success = self.download_with_sra_toolkit(accession, output_path)

        # Fallback to ENA if SRA Toolkit failed or not available
        if not success:
            logger.info("Trying ENA FTP download as fallback...")
            success = self.download_from_ena_url(accession, output_path)

        if success:
            logger.info(f"✅ Successfully downloaded {accession}")
            logger.info(f"Output directory: {output_path}")
        else:
            logger.error(f"❌ Failed to download {accession}")

        return success, output_path

    def download_batch(self, accessions: List[str], barcodes: Optional[List[str]] = None) -> Dict[str, Path]:
        """
        Download multiple SRA accessions.

        Args:
            accessions: List of SRA accessions
            barcodes: Optional list of barcode names (must match length of accessions)

        Returns:
            Dictionary mapping accession -> output_path for successful downloads
        """
        if barcodes and len(barcodes) != len(accessions):
            raise ValueError("Number of barcodes must match number of accessions")

        results = {}

        logger.info(f"Batch download: {len(accessions)} accessions")

        for idx, accession in enumerate(accessions):
            barcode = barcodes[idx] if barcodes else None

            success, output_path = self.download_accession(accession, barcode)

            if success:
                results[accession] = output_path

            # Brief pause between downloads to be nice to NCBI
            if idx < len(accessions) - 1:
                time.sleep(2)

        logger.info(f"Batch download complete: {len(results)}/{len(accessions)} successful")

        return results

    def validate_sra_tools(self) -> bool:
        """
        Validate SRA toolkit installation.

        Returns:
            True if properly installed, False otherwise
        """
        commands = ['prefetch', 'fasterq-dump']

        for cmd in commands:
            try:
                result = subprocess.run(
                    [cmd, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    logger.error(f"{cmd} command failed")
                    return False
                logger.info(f"{cmd}: OK")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.error(f"{cmd} not found")
                return False

        logger.info("✅ SRA Toolkit validation passed")
        return True


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    downloader = NCBIDownloader(output_dir=Path("test_downloads"))

    # Test single download
    test_accession = "SRR12345678"  # Replace with actual accession
    success, output_path = downloader.download_accession(test_accession)

    if success:
        print(f"✅ Download successful: {output_path}")
    else:
        print(f"❌ Download failed")
