# FASTQ Pipeline Upgrade Guide

> **Comprehensive Guide for Upgrading from K-mer Based Classification to Production-Grade Taxonomic Classification Tools**

## Table of Contents
1. [Current Pipeline Analysis](#current-pipeline-analysis)
2. [Production-Grade Alternatives](#production-grade-alternatives)
3. [Upgrade Implementation Paths](#upgrade-implementation-paths)
4. [Database Management](#database-management)
5. [Performance Optimization](#performance-optimization)
6. [Migration Strategy](#migration-strategy)
7. [Implementation Examples](#implementation-examples)
8. [Quality Control](#quality-control)
9. [Troubleshooting](#troubleshooting)

---

## Current Pipeline Analysis

### Overview
The existing FASTQ processing pipeline in `src/real_fastq_processor.py` implements a **k-mer based taxonomic classification system** designed for proof-of-concept and development purposes.

### Current Architecture

#### **MinimalTaxonomicClassifier**
```python
# Current Implementation Characteristics:
• Algorithm: 9-mer k-mer matching
• Database: 12 hardcoded reference species
• Classification: Simple consensus voting
• Confidence: Fraction of matching k-mers
```

#### **Key Components**
- **Quality Filtering**: Min read length (100bp), Min quality score (7.0)
- **Batch Processing**: 10 files at a time for memory management
- **Format Support**: `.fastq` and `.fastq.gz` files
- **Output**: CSV abundance table compatible with report generator

#### **Built-in Database Coverage**
```yaml
Current Species (12 total):
  Actinomycetota: 3 species
    - Streptomyces albidoflavus
    - Arthrobacter citreus  
    - Cellulomonas chengniuliangii
  
  Bacillota: 4 species
    - Lactobacillus acidophilus
    - Clostridium perfringens
    - Enterococcus faecalis
    - Bacillus subtilis
  
  Bacteroidota: 2 species
    - Bacteroides fragilis
    - Prevotella copri
  
  Pseudomonadota: 2 species
    - Escherichia coli
    - Salmonella enterica
  
  Fibrobacterota: 1 species
    - Fibrobacter succinogenes
```

### Limitations of Current System

#### **Scientific Limitations**
- ⚠️ **Limited Database**: Only 12 species vs. thousands in equine gut microbiome
- ⚠️ **Oversimplified Algorithm**: K-mer matching without phylogenetic context
- ⚠️ **No Quality Scores**: Classifications lack confidence intervals
- ⚠️ **Poor Sensitivity**: Misses closely related species and novel variants

#### **Technical Limitations**
- ⚠️ **Memory Inefficient**: Stores entire sequences in memory
- ⚠️ **Slow Processing**: Sequential k-mer matching without indexing
- ⚠️ **No Multithreading**: Single-threaded processing limits throughput
- ⚠️ **Hardcoded Database**: Difficult to update or customize

#### **Production Limitations**
- ⚠️ **Not Validated**: No benchmarking against known standards
- ⚠️ **No Error Handling**: Limited resilience to corrupted data
- ⚠️ **No Monitoring**: No performance metrics or logging
- ⚠️ **Single Format**: Limited to FASTQ input only

---

## Production-Grade Alternatives

### 1. **Kraken2** ⭐ **RECOMMENDED**

#### **Overview**
Kraken2 is the gold standard for metagenomic taxonomic classification, offering ultra-fast exact k-mer matching with comprehensive databases.

#### **Key Advantages**
```yaml
Performance:
  - Speed: ~4.2 million reads/minute
  - Memory: 8-50GB depending on database
  - Accuracy: 95%+ for species-level classification
  
Features:
  - Exact k-mer matching with minimizers
  - Comprehensive NCBI taxonomy integration
  - Confidence scoring with statistical validation
  - Multi-threading support (up to 64 cores)
  - Multiple output formats (TSV, JSON, etc.)
```

#### **Database Options**
```bash
# Standard Databases
kraken2-build --standard --db standard_db     # ~50GB, comprehensive
kraken2-build --db minikraken2_v1_8GB        # 8GB, faster
kraken2-build --db pluspf --threads 16       # Includes fungi/protozoa

# Custom Databases
kraken2-build --add-to-library sequences.fa --db custom_db
kraken2-build --build --db custom_db --threads 16
```

### 2. **Centrifuge** 

#### **Overview**
Memory-efficient metagenomic classifier using FM-index and Burrows-Wheeler Transform for rapid alignment-based classification.

#### **Key Advantages**
```yaml
Performance:
  - Speed: ~1 million reads/minute  
  - Memory: 4-6GB for comprehensive databases
  - Accuracy: 90%+ for genus-level classification
  
Features:
  - Space-efficient FM-index
  - Multiple alignment scoring
  - Integration with NCBI taxonomy
  - Handles long reads well (ONT/PacBio)
  - Real-time classification capability
```

### 3. **Diamond + MEGAN** 

#### **Overview**
Protein-based taxonomic classification using translated DNA sequences against comprehensive protein databases.

#### **Key Advantages**
```yaml
Performance:
  - Speed: ~500k reads/minute
  - Memory: 12-16GB for nr database
  - Accuracy: 85%+ for functional classification
  
Features:
  - Protein-level classification
  - Functional annotation (KEGG, COG)
  - Handles divergent sequences well
  - Long-term phylogenetic accuracy
```

### 4. **MetaPhlAn4**

#### **Overview**
Species-level profiling using clade-specific marker genes with quantitative abundance estimation.

#### **Key Advantages**
```yaml
Performance:
  - Speed: ~100k reads/minute
  - Memory: 2-4GB
  - Accuracy: 98%+ for known species
  
Features:
  - Quantitative abundance profiling
  - Strain-level resolution
  - Marker gene based (no false positives)
  - Integration with pathway analysis
```

### **Comparison Matrix**

| Tool | Speed | Memory | Accuracy | Database Size | Best For |
|------|-------|--------|----------|---------------|----------|
| **Kraken2** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | 50GB | General purpose, high throughput |
| **Centrifuge** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 6GB | Memory-limited environments |
| **Diamond+MEGAN** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | 16GB | Functional analysis, proteins |
| **MetaPhlAn4** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 2GB | Quantitative profiling |

---

## Upgrade Implementation Paths

### **Path 1: Drop-in Kraken2 Integration** ⭐ **RECOMMENDED**

#### **Implementation Strategy**
Replace `MinimalTaxonomicClassifier` with `Kraken2Classifier` while maintaining the same interface.

#### **Code Template**
```python
class Kraken2Classifier:
    """Production-grade taxonomic classifier using Kraken2"""
    
    def __init__(self, db_path: str, confidence: float = 0.1, threads: int = 4):
        self.db_path = db_path
        self.confidence = confidence
        self.threads = threads
        self.temp_dir = Path("temp_kraken2")
        self.temp_dir.mkdir(exist_ok=True)
    
    def classify_sequences(self, fastq_path: str) -> List[TaxonomicHit]:
        """Classify sequences using Kraken2"""
        output_file = self.temp_dir / f"kraken2_output_{time.time()}.txt"
        report_file = self.temp_dir / f"kraken2_report_{time.time()}.txt"
        
        # Run Kraken2
        cmd = [
            "kraken2",
            "--db", self.db_path,
            "--threads", str(self.threads),
            "--confidence", str(self.confidence),
            "--output", str(output_file),
            "--report", str(report_file),
            str(fastq_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Kraken2 failed: {result.stderr}")
        
        # Parse results
        return self._parse_kraken2_output(output_file)
    
    def _parse_kraken2_output(self, output_file: Path) -> List[TaxonomicHit]:
        """Parse Kraken2 classification output"""
        hits = []
        with open(output_file) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    classified = parts[0] == 'C'
                    if classified:
                        read_id = parts[1]
                        taxid = parts[2]
                        length = int(parts[3])
                        
                        # Get taxonomic lineage from NCBI taxonomy
                        taxonomy = self._get_taxonomy_from_taxid(taxid)
                        if taxonomy:
                            hits.append(TaxonomicHit(
                                read_id=read_id,
                                species=taxonomy.get('species', 'Unknown'),
                                genus=taxonomy.get('genus', 'Unknown'),
                                family=taxonomy.get('family', 'Unknown'),
                                order=taxonomy.get('order', 'Unknown'),
                                class_name=taxonomy.get('class', 'Unknown'),
                                phylum=taxonomy.get('phylum', 'Unknown'),
                                confidence=1.0,  # Kraken2 confidence handled internally
                                length=length
                            ))
        
        return hits
```

#### **Integration Steps**
1. **Install Kraken2**: `conda install -c bioconda kraken2`
2. **Download Database**: `kraken2-build --standard --db /path/to/kraken2_db`
3. **Replace Classifier**: Modify `RealFASTQProcessor.__init__()`
4. **Update Config**: Add database path to `report_config.yaml`
5. **Test Pipeline**: Validate with existing test data

### **Path 2: Hybrid Multi-Tool Approach**

#### **Implementation Strategy**
Combine multiple tools for comprehensive analysis with cross-validation.

```python
class HybridClassifier:
    """Multi-tool classifier with consensus scoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.kraken2 = Kraken2Classifier(config['kraken2_db'])
        self.centrifuge = CentrifugeClassifier(config['centrifuge_db'])
        self.consensus_threshold = config.get('consensus_threshold', 0.6)
    
    def classify_sequences(self, fastq_path: str) -> List[TaxonomicHit]:
        """Multi-tool classification with consensus"""
        
        # Run all classifiers
        kraken2_results = self.kraken2.classify_sequences(fastq_path)
        centrifuge_results = self.centrifuge.classify_sequences(fastq_path)
        
        # Generate consensus classifications
        return self._generate_consensus(kraken2_results, centrifuge_results)
```

### **Path 3: Gradual Migration Strategy**

#### **Phase 1: Parallel Running**
- Run both old and new systems in parallel
- Compare results for validation
- Build confidence in new system

#### **Phase 2: A/B Testing**
- Route percentage of samples to new system
- Monitor performance and accuracy
- Gradual increase in new system usage

#### **Phase 3: Full Migration**
- Switch to new system completely
- Keep old system as fallback
- Remove old system after validation period

---

## Database Management

### **Standard Databases**

#### **Kraken2 Standard Databases**
```bash
# Full NCBI RefSeq database (~50GB)
kraken2-build --standard --db standard_db --threads 16

# Compact database for faster processing (~8GB)  
wget https://genome-idx.s3.amazonaws.com/kraken/k2_standard_8gb_20210517.tar.gz
tar -xzf k2_standard_8gb_20210517.tar.gz

# PlusPF database with fungi and protozoa (~75GB)
kraken2-build --db pluspf --threads 16
```

#### **Centrifuge Databases**
```bash
# NCBI RefSeq bacteria/archaea (~6GB)
wget https://genome-idx.s3.amazonaws.com/centrifuge/p_compressed_2018_4_15.tar.gz

# NCBI nucleotide database (~9GB)
wget https://genome-idx.s3.amazonaws.com/centrifuge/nt_2018_3_3.tar.gz
```

### **Custom Database Creation**

#### **Equine-Specific Database**
```yaml
Target Organisms:
  Bacteria:
    - All major equine gut microbiome species (200+ species)
    - Pathogenic bacteria (Salmonella, E. coli, Clostridium)
    - Antibiotic resistance genes
  
  Parasites:
    - Giardia duodenalis
    - Cryptosporidium parvum
    - Eimeria leuckarti
    - Parascaris equorum
    - Strongyle species
  
  Viruses:
    - Equine herpesvirus (EHV-1, EHV-4)
    - Equine influenza virus
    - Equine rotavirus
    - Equine coronavirus
  
  Fungi:
    - Candida albicans
    - Aspergillus fumigatus
    - Malassezia species
```

#### **Custom Database Build Script**
```bash
#!/bin/bash
# build_equine_database.sh

DB_NAME="equine_microbiome"
THREADS=16

# Initialize database
kraken2-build --download-taxonomy --db $DB_NAME

# Add equine-specific sequences
kraken2-build --download-library bacteria --db $DB_NAME
kraken2-build --download-library viral --db $DB_NAME
kraken2-build --download-library fungi --db $DB_NAME

# Add custom sequences
find custom_sequences/ -name "*.fa" -exec kraken2-build --add-to-library {} --db $DB_NAME \;

# Build database
kraken2-build --build --db $DB_NAME --threads $THREADS

# Clean intermediate files
kraken2-build --clean --db $DB_NAME

echo "Equine microbiome database built successfully"
```

### **Database Maintenance**

#### **Automated Updates**
```python
class DatabaseManager:
    """Automated database update and validation"""
    
    def __init__(self, db_path: str, update_interval: int = 30):
        self.db_path = Path(db_path)
        self.update_interval = update_interval  # days
    
    def check_for_updates(self) -> bool:
        """Check if database needs updating"""
        if not self.db_path.exists():
            return True
        
        db_age = time.time() - self.db_path.stat().st_mtime
        return db_age > (self.update_interval * 24 * 3600)
    
    def update_database(self):
        """Download and rebuild database"""
        backup_path = self.db_path.with_suffix('.backup')
        
        try:
            # Backup existing database
            if self.db_path.exists():
                shutil.move(self.db_path, backup_path)
            
            # Download new database
            self._download_latest_database()
            
            # Validate new database
            if self._validate_database():
                logger.info("Database update successful")
                if backup_path.exists():
                    shutil.rmtree(backup_path)
            else:
                # Restore backup on failure
                if backup_path.exists():
                    shutil.move(backup_path, self.db_path)
                raise RuntimeError("Database validation failed")
                
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            raise
```

---

## Performance Optimization

### **Hardware Requirements**

#### **Minimum Requirements**
```yaml
CPU: 4 cores, 2.5GHz
RAM: 16GB
Storage: 100GB SSD
Network: 10Mbps (for database downloads)
```

#### **Recommended Requirements**
```yaml
CPU: 16+ cores, 3.0GHz+
RAM: 64GB
Storage: 500GB NVMe SSD
Network: 100Mbps+
```

#### **High-Throughput Requirements**
```yaml
CPU: 32+ cores, 3.5GHz+
RAM: 128GB
Storage: 1TB+ NVMe SSD in RAID
Network: 1Gbps+
```

### **Optimization Strategies**

#### **Multi-threading Configuration**
```python
class OptimizedProcessor:
    """Optimized FASTQ processor with performance tuning"""
    
    def __init__(self, threads: int = None):
        if threads is None:
            threads = min(16, os.cpu_count())
        
        self.threads = threads
        self.batch_size = max(1000, threads * 100)  # Scale with thread count
        
    def process_with_threading(self, fastq_files: List[Path]):
        """Process files with optimal threading"""
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Submit batches to thread pool
            futures = []
            for batch in self._batch_files(fastq_files, self.batch_size):
                future = executor.submit(self._process_batch, batch)
                futures.append(future)
            
            # Collect results
            all_results = []
            for future in as_completed(futures):
                batch_results = future.result()
                all_results.extend(batch_results)
        
        return all_results
```

#### **Memory Optimization**
```python
class MemoryEfficientProcessor:
    """Memory-optimized processing for large datasets"""
    
    def __init__(self, max_memory_gb: int = 8):
        self.max_memory_gb = max_memory_gb
        self.chunk_size = self._calculate_optimal_chunk_size()
    
    def _calculate_optimal_chunk_size(self) -> int:
        """Calculate optimal chunk size based on available memory"""
        available_memory = self.max_memory_gb * 1024 * 1024 * 1024  # bytes
        avg_read_size = 500  # average read length
        safety_factor = 0.7  # use 70% of available memory
        
        return int((available_memory * safety_factor) / avg_read_size)
    
    def process_large_file(self, fastq_path: Path):
        """Process large FASTQ files in chunks"""
        
        with self._open_fastq(fastq_path) as f:
            chunk = []
            chunk_count = 0
            
            for record in SeqIO.parse(f, "fastq"):
                chunk.append(record)
                
                if len(chunk) >= self.chunk_size:
                    # Process chunk
                    results = self._process_chunk(chunk)
                    yield results
                    
                    # Clear chunk
                    chunk = []
                    chunk_count += 1
                    
                    # Garbage collection
                    if chunk_count % 10 == 0:
                        gc.collect()
            
            # Process final chunk
            if chunk:
                yield self._process_chunk(chunk)
```

### **Caching Strategies**

#### **Database Result Caching**
```python
class ResultCache:
    """Cache taxonomic classification results"""
    
    def __init__(self, cache_dir: str = "classification_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def get_cache_key(self, fastq_path: Path) -> str:
        """Generate cache key from file content hash"""
        hasher = hashlib.md5()
        
        with open(fastq_path, 'rb') as f:
            # Hash first and last 1MB for speed
            hasher.update(f.read(1024*1024))
            f.seek(-1024*1024, 2)
            hasher.update(f.read(1024*1024))
        
        return hasher.hexdigest()
    
    def get_cached_result(self, cache_key: str) -> Optional[List[TaxonomicHit]]:
        """Retrieve cached classification result"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                return [TaxonomicHit(**hit) for hit in data]
        
        return None
```

---

## Migration Strategy

### **Pre-Migration Checklist**

#### **System Preparation**
- [ ] Hardware requirements met
- [ ] Software dependencies installed  
- [ ] Database downloaded and validated
- [ ] Backup of current system created
- [ ] Testing environment prepared

#### **Validation Preparation**
- [ ] Reference datasets prepared
- [ ] Performance benchmarks established
- [ ] Accuracy metrics defined
- [ ] Rollback procedures documented

### **Migration Timeline**

#### **Week 1: Setup and Validation**
```yaml
Days 1-2: Infrastructure Setup
  - Install Kraken2/Centrifuge
  - Download standard databases
  - Configure hardware

Days 3-5: Initial Testing
  - Run test datasets
  - Compare with existing results
  - Identify discrepancies

Days 6-7: Optimization
  - Tune performance parameters
  - Optimize memory usage
  - Test batch processing
```

#### **Week 2: Integration and Testing**
```yaml
Days 8-10: Code Integration
  - Implement new classifier classes
  - Update pipeline interfaces
  - Add configuration management

Days 11-12: Comprehensive Testing
  - Process full sample sets
  - Validate output formats
  - Test error handling

Days 13-14: Performance Testing
  - Load testing with large datasets
  - Memory profiling
  - Throughput benchmarking
```

#### **Week 3-4: Deployment and Monitoring**
```yaml
Week 3: Staged Deployment
  - Deploy to staging environment
  - Run parallel processing
  - Monitor for issues

Week 4: Production Deployment
  - Switch to new system
  - Monitor performance metrics
  - Address any issues
```

### **Rollback Plan**

#### **Immediate Rollback (< 1 hour)**
```python
def emergency_rollback():
    """Emergency rollback to previous system"""
    # Stop current processing
    stop_all_processes()
    
    # Switch configuration back
    config['classifier_type'] = 'minimal'
    save_config(config)
    
    # Restart with old system
    restart_processing_service()
    
    logger.critical("Emergency rollback completed")
```

#### **Planned Rollback (< 24 hours)**
```python
def planned_rollback():
    """Planned rollback with data preservation"""
    # Complete current processing jobs
    wait_for_job_completion(timeout=3600)
    
    # Backup new system results
    backup_new_results()
    
    # Switch back to old system
    switch_to_previous_version()
    
    # Validate rollback success
    validate_system_health()
```

---

## Implementation Examples

### **Complete Kraken2 Integration**

```python
# src/production_fastq_processor.py
"""
Production FASTQ processor with Kraken2 integration
Replaces real_fastq_processor.py with production-grade classification
"""

import subprocess
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Kraken2Config:
    """Configuration for Kraken2 classifier"""
    database_path: str
    confidence_threshold: float = 0.1
    threads: int = 4
    memory_mapping: bool = True
    quick_mode: bool = False


class ProductionTaxonomicClassifier:
    """Production taxonomic classifier using Kraken2"""
    
    def __init__(self, config: Kraken2Config):
        self.config = config
        self.taxonomy_db = self._load_taxonomy_database()
        
        # Validate Kraken2 installation
        self._validate_kraken2_installation()
        
        logger.info(f"Initialized Kraken2 classifier with database: {config.database_path}")
    
    def _validate_kraken2_installation(self):
        """Check if Kraken2 is installed and accessible"""
        try:
            result = subprocess.run(['kraken2', '--version'], 
                                 capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("Kraken2 not found in PATH")
            
            version = result.stdout.strip()
            logger.info(f"Kraken2 version: {version}")
            
        except FileNotFoundError:
            raise RuntimeError("Kraken2 not installed. Install with: conda install -c bioconda kraken2")
    
    def _load_taxonomy_database(self) -> Dict[str, Dict[str, str]]:
        """Load NCBI taxonomy database for taxid -> lineage mapping"""
        # Implementation would load NCBI taxonomy files
        # For now, return empty dict - can be populated from nodes.dmp/names.dmp
        return {}
    
    def classify_fastq_file(self, fastq_path: Path) -> List[TaxonomicHit]:
        """Classify all sequences in a FASTQ file using Kraken2"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "kraken2_output.txt"
            report_file = Path(temp_dir) / "kraken2_report.txt"
            
            # Build Kraken2 command
            cmd = [
                'kraken2',
                '--db', self.config.database_path,
                '--threads', str(self.config.threads),
                '--confidence', str(self.config.confidence_threshold),
                '--output', str(output_file),
                '--report', str(report_file)
            ]
            
            if self.config.memory_mapping:
                cmd.append('--memory-mapping')
            
            if self.config.quick_mode:
                cmd.append('--quick')
            
            cmd.append(str(fastq_path))
            
            # Run Kraken2
            logger.info(f"Running Kraken2 on {fastq_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Kraken2 error: {result.stderr}")
                raise RuntimeError(f"Kraken2 classification failed: {result.stderr}")
            
            # Parse results
            classifications = self._parse_kraken2_output(output_file)
            
            # Log statistics
            report_stats = self._parse_kraken2_report(report_file)
            logger.info(f"Kraken2 completed: {len(classifications)} sequences classified")
            logger.info(f"Classification rate: {report_stats.get('classified_rate', 'N/A')}%")
            
            return classifications
    
    def _parse_kraken2_output(self, output_file: Path) -> List[TaxonomicHit]:
        """Parse Kraken2 classification output"""
        classifications = []
        
        with open(output_file) as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    classified = parts[0] == 'C'
                    read_id = parts[1]
                    taxid = parts[2]
                    length = int(parts[3])
                    
                    if classified:
                        # Get taxonomic lineage
                        lineage = self._get_lineage_from_taxid(taxid)
                        
                        if lineage:
                            classifications.append(TaxonomicHit(
                                read_id=read_id,
                                species=lineage.get('species', 'Unknown species'),
                                genus=lineage.get('genus', 'Unknown genus'),
                                family=lineage.get('family', 'Unknown family'),
                                order=lineage.get('order', 'Unknown order'),
                                class_name=lineage.get('class', 'Unknown class'),
                                phylum=lineage.get('phylum', 'Unknown phylum'),
                                confidence=1.0,  # Kraken2 handles confidence internally
                                length=length
                            ))
        
        return classifications
    
    def _parse_kraken2_report(self, report_file: Path) -> Dict[str, float]:
        """Parse Kraken2 report for statistics"""
        stats = {}
        
        try:
            with open(report_file) as f:
                lines = f.readlines()
                if lines:
                    # First line contains unclassified percentage
                    unclassified_line = lines[0]
                    unclassified_pct = float(unclassified_line.split()[0])
                    stats['classified_rate'] = 100 - unclassified_pct
        except Exception as e:
            logger.warning(f"Could not parse Kraken2 report: {e}")
        
        return stats
    
    def _get_lineage_from_taxid(self, taxid: str) -> Optional[Dict[str, str]]:
        """Get taxonomic lineage from NCBI taxonomy ID"""
        # This would query the loaded taxonomy database
        # For now, return None - implement based on nodes.dmp/names.dmp
        return None


class ProductionFASTQProcessor:
    """Production FASTQ processor with Kraken2 backend"""
    
    def __init__(self, kraken2_config: Kraken2Config, 
                 min_read_length: int = 100, min_quality: float = 7.0):
        self.min_read_length = min_read_length
        self.min_quality = min_quality
        self.classifier = ProductionTaxonomicClassifier(kraken2_config)
    
    def process_barcode_directories(self, data_dir: str, barcode_dirs: List[str]) -> pd.DataFrame:
        """Process barcode directories with production classifier"""
        logger.info(f"Processing {len(barcode_dirs)} barcode directories with Kraken2")
        
        # Use same logic as RealFASTQProcessor but with production classifier
        barcode_results = {}
        all_species = set()
        
        for barcode_dir in barcode_dirs:
            barcode_path = Path(data_dir) / barcode_dir
            if not barcode_path.exists():
                logger.warning(f"Barcode directory not found: {barcode_path}")
                continue
            
            logger.info(f"Processing {barcode_dir} with Kraken2...")
            classifications, stats = self._process_barcode_directory(barcode_path)
            
            # Count species abundances
            species_counts = Counter()
            for hit in classifications:
                species_counts[hit.species] += 1
                all_species.add(hit.species)
            
            barcode_results[barcode_dir] = {
                'counts': species_counts,
                'stats': stats,
                'total_classified': len(classifications)
            }
            
            logger.info(f"  {barcode_dir}: {stats.total_reads} reads, "
                       f"{len(classifications)} classified, {len(species_counts)} species")
        
        # Generate abundance table (same as original)
        return self._create_abundance_dataframe(barcode_results, all_species)
    
    def _process_barcode_directory(self, barcode_path: Path) -> Tuple[List[TaxonomicHit], SequenceStats]:
        """Process barcode directory with production classifier"""
        fastq_files = list(barcode_path.glob('*.fastq.gz')) + list(barcode_path.glob('*.fastq'))
        
        if not fastq_files:
            logger.warning(f"No FASTQ files found in {barcode_path}")
            return [], SequenceStats()
        
        all_classifications = []
        stats = SequenceStats()
        
        # Process each file with Kraken2
        for fastq_file in fastq_files:
            try:
                # Quality filtering happens within Kraken2
                file_classifications = self.classifier.classify_fastq_file(fastq_file)
                all_classifications.extend(file_classifications)
                
                # Update statistics (simplified - Kraken2 handles quality)
                with self._open_fastq(fastq_file) as f:
                    read_count = sum(1 for _ in SeqIO.parse(f, "fastq"))
                    stats.total_reads += read_count
                    stats.classified_reads += len(file_classifications)
                
            except Exception as e:
                logger.error(f"Error processing {fastq_file}: {e}")
                continue
        
        return all_classifications, stats


# Configuration and usage example
def create_production_processor() -> ProductionFASTQProcessor:
    """Create production processor with Kraken2 configuration"""
    
    kraken2_config = Kraken2Config(
        database_path="/path/to/kraken2_standard_db",
        confidence_threshold=0.1,
        threads=8,
        memory_mapping=True,
        quick_mode=False
    )
    
    return ProductionFASTQProcessor(
        kraken2_config=kraken2_config,
        min_read_length=100,
        min_quality=7.0
    )


# Main function for production use
def process_fastq_directories_production(data_dir: str, barcode_dirs: List[str], 
                                       output_csv: str, config_path: str = None) -> bool:
    """Production FASTQ processing with Kraken2"""
    try:
        # Load configuration
        if config_path:
            with open(config_path) as f:
                config_data = json.load(f)
                kraken2_config = Kraken2Config(**config_data['kraken2'])
        else:
            kraken2_config = Kraken2Config(
                database_path=os.environ.get('KRAKEN2_DB_PATH', '/opt/kraken2_db')
            )
        
        # Create processor
        processor = ProductionFASTQProcessor(kraken2_config)
        
        # Process directories
        abundance_df = processor.process_barcode_directories(data_dir, barcode_dirs)
        
        # Save results
        abundance_df.to_csv(output_csv, index=False)
        
        logger.info(f"Production processing completed: {output_csv}")
        return True
        
    except Exception as e:
        logger.error(f"Production processing failed: {e}")
        return False
```

### **Configuration Management**

```python
# config/production_config.yaml
production_classification:
  enabled: true
  classifier_type: "kraken2"  # kraken2, centrifuge, hybrid
  
  kraken2:
    database_path: "/opt/databases/kraken2_standard"
    confidence_threshold: 0.1
    threads: 8
    memory_mapping: true
    quick_mode: false
    
  centrifuge:
    database_path: "/opt/databases/centrifuge_nt"
    min_hitlen: 22
    threads: 8
    
  quality_control:
    min_read_length: 100
    min_quality_score: 7.0
    max_ambiguous_bases: 5
    
  performance:
    batch_size: 1000
    max_memory_gb: 32
    cache_results: true
    cache_dir: "/tmp/classification_cache"
    
  output:
    include_confidence_scores: true
    include_read_assignments: false
    detailed_taxonomy: true
```

### **Docker Containerization**

```dockerfile
# Dockerfile.production
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Kraken2
RUN wget https://github.com/DerrickWood/kraken2/archive/v2.1.2.tar.gz \
    && tar -xzf v2.1.2.tar.gz \
    && cd kraken2-2.1.2 \
    && ./install_kraken2.sh /usr/local/bin \
    && cd .. && rm -rf kraken2-2.1.2 v2.1.2.tar.gz

# Install Python packages
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/
WORKDIR /app

# Create directories
RUN mkdir -p /app/data /app/results /app/databases

# Download standard database (in production, mount as volume)
RUN kraken2-build --download-taxonomy --db /app/databases/kraken2_standard
RUN kraken2-build --download-library bacteria --db /app/databases/kraken2_standard
RUN kraken2-build --build --db /app/databases/kraken2_standard --threads 4

EXPOSE 8080

CMD ["python3", "-m", "src.production_fastq_processor"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  fastq-processor:
    build:
      context: .
      dockerfile: Dockerfile.production
    volumes:
      - ./data:/app/data
      - ./results:/app/results
      - ./databases:/app/databases
    environment:
      - KRAKEN2_DB_PATH=/app/databases/kraken2_standard
      - PYTHONPATH=/app
    deploy:
      resources:
        limits:
          memory: 32G
          cpus: '16'
        reservations:
          memory: 16G
          cpus: '8'
```

---

## Quality Control

### **Validation Framework**

```python
class ValidationSuite:
    """Comprehensive validation for production classifier"""
    
    def __init__(self, reference_datasets: Dict[str, str]):
        self.reference_datasets = reference_datasets
        self.metrics = {}
    
    def validate_accuracy(self, classifier, dataset_name: str) -> Dict[str, float]:
        """Validate classification accuracy against reference"""
        
        reference_path = self.reference_datasets[dataset_name]
        test_results = classifier.classify_fastq_file(reference_path)
        
        # Load ground truth
        ground_truth = self._load_ground_truth(dataset_name)
        
        # Calculate metrics
        metrics = {
            'sensitivity': self._calculate_sensitivity(test_results, ground_truth),
            'specificity': self._calculate_specificity(test_results, ground_truth),
            'precision': self._calculate_precision(test_results, ground_truth),
            'f1_score': self._calculate_f1_score(test_results, ground_truth),
            'species_level_accuracy': self._species_accuracy(test_results, ground_truth),
            'genus_level_accuracy': self._genus_accuracy(test_results, ground_truth)
        }
        
        return metrics
    
    def benchmark_performance(self, classifier, dataset_sizes: List[int]) -> Dict[str, List[float]]:
        """Benchmark processing speed and memory usage"""
        
        performance_metrics = {
            'processing_time': [],
            'memory_usage': [],
            'reads_per_second': []
        }
        
        for size in dataset_sizes:
            test_dataset = self._generate_test_dataset(size)
            
            # Monitor performance
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            results = classifier.classify_fastq_file(test_dataset)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            # Record metrics
            processing_time = end_time - start_time
            memory_used = end_memory - start_memory
            reads_per_second = size / processing_time
            
            performance_metrics['processing_time'].append(processing_time)
            performance_metrics['memory_usage'].append(memory_used)
            performance_metrics['reads_per_second'].append(reads_per_second)
        
        return performance_metrics
```

### **Continuous Monitoring**

```python
class ProductionMonitor:
    """Monitor production classifier performance"""
    
    def __init__(self, alert_thresholds: Dict[str, float]):
        self.alert_thresholds = alert_thresholds
        self.metrics_history = []
    
    def monitor_classification_run(self, results: List[TaxonomicHit]) -> Dict[str, Any]:
        """Monitor a single classification run"""
        
        metrics = {
            'timestamp': time.time(),
            'total_classified': len(results),
            'classification_rate': len(results) / sum(1 for _ in results),
            'species_diversity': len(set(hit.species for hit in results)),
            'confidence_distribution': self._analyze_confidence_distribution(results),
            'phylum_distribution': self._analyze_phylum_distribution(results)
        }
        
        # Check for alerts
        alerts = self._check_alert_conditions(metrics)
        if alerts:
            self._send_alerts(alerts)
        
        self.metrics_history.append(metrics)
        
        return metrics
    
    def generate_daily_report(self) -> str:
        """Generate daily performance report"""
        
        today_metrics = [m for m in self.metrics_history 
                        if time.time() - m['timestamp'] < 24 * 3600]
        
        if not today_metrics:
            return "No classification runs in the last 24 hours"
        
        report = f"""
        Daily Classification Report
        ==========================
        
        Runs: {len(today_metrics)}
        Average Classification Rate: {np.mean([m['classification_rate'] for m in today_metrics]):.2%}
        Total Sequences Processed: {sum(m['total_classified'] for m in today_metrics):,}
        Average Species Diversity: {np.mean([m['species_diversity'] for m in today_metrics]):.1f}
        
        Performance Trends:
        - Classification rate trend: {'↑' if self._is_improving('classification_rate') else '↓'}
        - Species diversity trend: {'↑' if self._is_improving('species_diversity') else '↓'}
        """
        
        return report
```

---

## Troubleshooting

### **Common Issues and Solutions**

#### **Database Issues**

| Issue | Symptom | Solution |
|-------|---------|----------|
| Database not found | `Error: Database not found` | Verify database path in config, check permissions |
| Corrupt database | `Error: Invalid database format` | Re-download and rebuild database |
| Insufficient disk space | `Error: No space left on device` | Clean up temp files, expand storage |
| Database version mismatch | `Warning: Database version mismatch` | Update Kraken2 or rebuild database |

#### **Performance Issues**

| Issue | Symptom | Solution |
|-------|---------|----------|
| High memory usage | System becomes unresponsive | Reduce thread count, use quick mode, smaller database |
| Slow processing | Long processing times | Increase thread count, enable memory mapping, use SSD |
| Low classification rate | Many unclassified reads | Lower confidence threshold, use larger database |
| Disk I/O bottleneck | High disk utilization | Move database to faster storage, increase RAM |

#### **Classification Issues**

| Issue | Symptom | Solution |
|-------|---------|----------|
| Too many false positives | Unexpected species detected | Increase confidence threshold, validate database |
| Missing expected species | Known species not detected | Check database coverage, reduce confidence threshold |
| Inconsistent results | Results vary between runs | Check for random seeding, validate input files |
| Poor genus-level accuracy | Good species but poor genus | Use genus-specific databases, adjust classification algorithm |

### **Debugging Tools**

```python
class ClassificationDebugger:
    """Debug classification issues"""
    
    def __init__(self, classifier):
        self.classifier = classifier
    
    def debug_classification(self, fastq_path: Path, read_id: str = None):
        """Debug specific read classification"""
        
        # Extract specific read or sample reads
        debug_reads = self._extract_debug_reads(fastq_path, read_id)
        
        for read in debug_reads:
            print(f"Debugging read: {read.id}")
            
            # Show k-mer extraction
            kmers = self._extract_kmers(str(read.seq))
            print(f"K-mers extracted: {len(kmers)}")
            
            # Show database matches
            matches = self._find_database_matches(kmers)
            print(f"Database matches: {len(matches)}")
            
            # Show classification process
            classification = self.classifier.classify_sequence(str(read.seq), read.id)
            if classification:
                print(f"Final classification: {classification.species} (confidence: {classification.confidence:.3f})")
            else:
                print("No classification assigned")
            
            print("-" * 50)
    
    def analyze_database_coverage(self, target_species: List[str]):
        """Analyze database coverage for specific species"""
        
        coverage_report = {}
        
        for species in target_species:
            # Search database for species
            matches = self._search_database_for_species(species)
            
            coverage_report[species] = {
                'found': len(matches) > 0,
                'reference_sequences': len(matches),
                'coverage_score': self._calculate_coverage_score(matches)
            }
        
        return coverage_report
    
    def validate_input_quality(self, fastq_path: Path) -> Dict[str, Any]:
        """Validate FASTQ file quality"""
        
        quality_metrics = {
            'total_reads': 0,
            'mean_length': 0,
            'mean_quality': 0,
            'n_content': 0,
            'low_quality_reads': 0
        }
        
        with self._open_fastq(fastq_path) as f:
            lengths = []
            qualities = []
            n_counts = []
            
            for record in SeqIO.parse(f, "fastq"):
                quality_metrics['total_reads'] += 1
                lengths.append(len(record.seq))
                qualities.append(np.mean(record.letter_annotations['phred_quality']))
                n_counts.append(str(record.seq).count('N'))
                
                if qualities[-1] < 20:  # Phred score < 20
                    quality_metrics['low_quality_reads'] += 1
        
        quality_metrics['mean_length'] = np.mean(lengths)
        quality_metrics['mean_quality'] = np.mean(qualities) 
        quality_metrics['n_content'] = np.mean(n_counts) / quality_metrics['mean_length']
        
        return quality_metrics
```

### **Log Analysis**

```python
class LogAnalyzer:
    """Analyze classification logs for issues"""
    
    def analyze_error_patterns(self, log_file: Path) -> Dict[str, int]:
        """Analyze error patterns in log files"""
        
        error_patterns = {
            'database_errors': 0,
            'memory_errors': 0,
            'file_not_found': 0,
            'permission_errors': 0,
            'classification_failures': 0
        }
        
        with open(log_file) as f:
            for line in f:
                if 'ERROR' in line:
                    if 'database' in line.lower():
                        error_patterns['database_errors'] += 1
                    elif 'memory' in line.lower() or 'out of memory' in line.lower():
                        error_patterns['memory_errors'] += 1
                    elif 'file not found' in line.lower():
                        error_patterns['file_not_found'] += 1
                    elif 'permission' in line.lower():
                        error_patterns['permission_errors'] += 1
                    elif 'classification' in line.lower():
                        error_patterns['classification_failures'] += 1
        
        return error_patterns
    
    def extract_performance_metrics(self, log_file: Path) -> List[Dict[str, float]]:
        """Extract performance metrics from logs"""
        
        metrics = []
        
        with open(log_file) as f:
            for line in f:
                if 'processing time:' in line.lower():
                    # Extract processing time
                    time_match = re.search(r'(\d+\.?\d*) seconds', line)
                    if time_match:
                        processing_time = float(time_match.group(1))
                        metrics.append({'processing_time': processing_time})
        
        return metrics
```

### **Recovery Procedures**

```bash
#!/bin/bash
# emergency_recovery.sh

echo "Starting emergency recovery procedure..."

# 1. Stop all processing
pkill -f "fastq_processor"

# 2. Check system resources
df -h
free -h

# 3. Clean temporary files
rm -rf /tmp/kraken2_*
rm -rf /tmp/classification_*

# 4. Restart with minimal configuration
export KRAKEN2_THREADS=2
export KRAKEN2_MEMORY_LIMIT=4G

# 5. Test with small dataset
python3 -c "
from src.production_fastq_processor import ProductionFASTQProcessor
processor = ProductionFASTQProcessor(threads=2)
result = processor.process_test_dataset('data/test_small.fastq')
print(f'Test result: {len(result)} classifications')
"

echo "Emergency recovery completed"
```

---

## Conclusion

This comprehensive upgrade guide provides everything needed to transition from the current k-mer based prototype to a production-grade taxonomic classification system. The recommended approach is **Kraken2 integration** due to its optimal balance of speed, accuracy, and industry adoption.

### **Next Steps**

1. **Immediate (Week 1)**: Set up Kraken2 with standard database
2. **Short-term (Month 1)**: Build custom equine microbiome database  
3. **Medium-term (Quarter 1)**: Implement hybrid multi-tool approach
4. **Long-term (Year 1)**: Full production deployment with monitoring

### **Success Metrics**

- **Classification Rate**: >95% of reads classified
- **Species Accuracy**: >90% species-level precision
- **Processing Speed**: >1M reads/minute
- **System Uptime**: >99.9% availability

The upgrade will transform the system from a development prototype to a veterinary-grade diagnostic tool capable of handling production workloads while maintaining the existing user-friendly interface and reporting capabilities.

---

*This guide serves as the definitive reference for FASTQ pipeline upgrades in the Equine Microbiome Reporter system.*