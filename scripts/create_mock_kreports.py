#!/usr/bin/env python3
"""
Create mock Kraken2 reports for testing the pipeline without needing the full database.
Based on typical equine gut microbiome composition.
"""

import os
from pathlib import Path

def create_mock_kreport(sample_name: str, output_dir: Path):
    """Create a realistic mock Kraken2 report for testing."""
    
    # Typical equine gut microbiome composition
    mock_report = """25.50	2550	2550	S	1280	  Staphylococcus aureus
18.30	1830	1830	S	1301	  Streptococcus pneumoniae
15.20	1520	1520	S	562	  Escherichia coli
12.45	1245	1245	S	1639	  Lactobacillus acidophilus
10.80	1080	1080	S	817	  Bacteroides fragilis
8.50	850	850	S	1423	  Bacillus subtilis
6.30	630	630	S	1491	  Clostridium botulinum
5.25	525	525	S	28037	  Prevotella copri
4.80	480	480	S	1502	  Clostridium perfringens
3.60	360	360	S	1351	  Enterococcus faecalis
2.95	295	295	S	29466	  Fibrobacter succinogenes
2.40	240	240	S	1760	  Actinobacteria bacterium
1.85	185	185	S	1678	  Bifidobacterium longum
1.50	150	150	S	239935	  Akkermansia muciniphila
1.20	120	120	S	853	  Faecalibacterium prausnitzii
0.95	95	95	S	33043	  Ruminococcus flavefaciens
0.80	80	80	S	301301	  Roseburia intestinalis
0.65	65	65	S	39491	  Eubacterium rectale
0.45	45	45	S	47678	  Parabacteroides distasonis
0.35	35	35	S	239934	  Alistipes putredinis
0.25	25	25	S	74426	  Collinsella aerofaciens
0.18	18	18	S	2173	  Methanobrevibacter smithii
0.12	12	12	S	1358	  Lactococcus lactis
0.08	8	8	S	1598	  Lactobacillus reuteri
0.05	5	5	S	1613	  Lactobacillus fermentum"""
    
    # Create output file
    kreport_file = output_dir / f"{sample_name}.kreport"
    with open(kreport_file, 'w') as f:
        f.write(mock_report)
    
    print(f"Created mock report: {kreport_file}")
    return kreport_file


def main():
    """Create mock reports for all samples."""
    output_dir = Path("pipeline_output/kraken_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock reports for each barcode
    for barcode in ["barcode04", "barcode05", "barcode06"]:
        create_mock_kreport(barcode, output_dir)
    
    print("\n✅ Mock Kraken2 reports created!")
    print("You can now continue with the pipeline using:")
    print("  python scripts/continue_pipeline.py")


if __name__ == "__main__":
    main()