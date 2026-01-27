"""
Chart Generator - Creates professional data visualizations using Matplotlib
Generates charts matching the reference PDF design
Supports multi-language chart labels
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

try:
    from .data_models import MicrobiomeData
except ImportError:
    from data_models import MicrobiomeData

logger = logging.getLogger(__name__)

# Chart label translations
CHART_LABELS = {
    'en': {
        'percentage': 'Percentage (%)',
        'species_title': 'MICROBIOTIC PROFILE - Top Species Distribution',
        'phylum_title': 'PHYLUM DISTRIBUTION IN GUT MICROFLORA',
        'reference_legend': 'Gray bars indicate reference ranges',
        'ref': 'Ref',
    },
    'pl': {
        'percentage': 'Procent (%)',
        'species_title': 'PROFIL MIKROBIOTYCZNY - Rozkład Głównych Gatunków',
        'phylum_title': 'ROZKŁAD TYPÓW W MIKROFLORZE JELITOWEJ',
        'reference_legend': 'Szare paski wskazują zakresy referencyjne',
        'ref': 'Ref',
    },
    'ja': {
        'percentage': '割合 (%)',
        'species_title': '微生物プロファイル - 主要種の分布',
        'phylum_title': '腸内細菌叢における門レベルの分布',
        'reference_legend': '灰色のバーは基準範囲を示します',
        'ref': '基準',
    },
    'de': {
        'percentage': 'Prozentsatz (%)',
        'species_title': 'MIKROBIOTISCHES PROFIL - Verteilung der Hauptarten',
        'phylum_title': 'PHYLUM-VERTEILUNG IN DER DARMFLORA',
        'reference_legend': 'Graue Balken zeigen Referenzbereiche',
        'ref': 'Ref',
    },
    'es': {
        'percentage': 'Porcentaje (%)',
        'species_title': 'PERFIL MICROBIÓTICO - Distribución de Especies Principales',
        'phylum_title': 'DISTRIBUCIÓN DE FILOS EN LA MICROFLORA INTESTINAL',
        'reference_legend': 'Las barras grises indican rangos de referencia',
        'ref': 'Ref',
    },
    'fr': {
        'percentage': 'Pourcentage (%)',
        'species_title': 'PROFIL MICROBIOTIQUE - Distribution des Espèces Principales',
        'phylum_title': 'DISTRIBUTION DES PHYLUMS DANS LA MICROFLORE INTESTINALE',
        'reference_legend': 'Les barres grises indiquent les plages de référence',
        'ref': 'Réf',
    },
}

# Color scheme matching reference design
PHYLUM_COLORS = {
    'Actinomycetota': '#14B8A6',    # Teal
    'Bacillota': '#10B981',         # Green
    'Bacteroidota': '#3B82F6',      # Blue
    'Fibrobacterota': '#8B5CF6',    # Purple
    'Pseudomonadota': '#06B6D4',    # Cyan
    'Other': '#94A3B8'              # Gray
}

class ChartGenerator:
    """Generate professional charts for microbiome reports"""

    def __init__(self, output_dir: str = "temp_charts", language: str = "en"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.language = language

        # Set professional medical report style
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Enhanced font settings for professional medical charts
        # Include fonts that support Japanese/Polish characters
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica', 'Noto Sans CJK JP', 'Noto Sans'],
            'font.size': 11,
            'axes.titlesize': 16,
            'axes.labelsize': 13,
            'xtick.labelsize': 11,
            'ytick.labelsize': 11,
            'legend.fontsize': 11,
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',
            'axes.linewidth': 1.2,
            'axes.edgecolor': '#2F2F2F',
            'grid.alpha': 0.3,
            'grid.linewidth': 0.8
        })

    def _get_label(self, key: str) -> str:
        """Get translated label for chart elements"""
        labels = CHART_LABELS.get(self.language, CHART_LABELS['en'])
        return labels.get(key, CHART_LABELS['en'].get(key, key))

    def generate_all_charts(self, data: MicrobiomeData) -> Dict[str, str]:
        """Generate all charts for the report"""
        chart_paths = {}
        
        # Generate species distribution chart
        chart_paths['species_distribution'] = self._create_species_distribution_chart(data)
        
        # Generate phylum distribution chart
        chart_paths['phylum_distribution'] = self._create_phylum_distribution_chart(data)
        
        # Generate phylum comparison chart
        chart_paths['phylum_comparison'] = self._create_phylum_comparison_chart(data)
        
        logger.info(f"Generated {len(chart_paths)} charts")
        return chart_paths
    
    def _create_species_distribution_chart(self, data: MicrobiomeData) -> str:
        """Create horizontal bar chart for top species distribution"""
        # Get top 20 species
        top_species = data.species_list[:20]
        
        # Create professional figure with optimal dimensions
        fig, ax = plt.subplots(figsize=(12, 9))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#FAFBFC')
        
        # Prepare data
        species_names = []
        percentages = []
        phyla = []
        
        for species_data in top_species:
            species_names.append(species_data['species'])
            percentages.append(species_data['percentage'])
            phyla.append(species_data.get('phylum', 'Other'))
        
        # Reverse for bottom-to-top display
        species_names = species_names[::-1]
        percentages = percentages[::-1]
        phyla = phyla[::-1]
        
        # Create gradient colors based on phylum
        colors = [PHYLUM_COLORS.get(phylum, PHYLUM_COLORS['Other']) for phylum in phyla]
        
        # Create professional gradient bars
        y_positions = np.arange(len(species_names))
        bars = ax.barh(y_positions, percentages, color=colors, alpha=0.85, height=0.7)
        
        # Add subtle background effect for depth
        for i in range(len(species_names)):
            ax.barh(y_positions[i], percentages[i], color='#E5E7EB', 
                   alpha=0.2, height=0.7, zorder=0)
        
        # Add enhanced percentage labels with better positioning
        for i, (bar, pct) in enumerate(zip(bars, percentages)):
            label_x = bar.get_width() + max(percentages) * 0.01
            ax.text(label_x, bar.get_y() + bar.get_height()/2, 
                    f'{pct:.1f}%', va='center', ha='left', 
                    fontsize=10, fontweight='600', color='#374151')
        
        # Customize axes (no numbering per feedback)
        ax.set_yticks(y_positions)
        # Note: species_names already reversed on line 150, do NOT reverse again
        ax.set_yticklabels([f"{name[:50]}" for name in species_names],
                          fontsize=9)
        ax.set_xlabel(self._get_label('percentage'))
        ax.set_title(self._get_label('species_title'),
                    fontweight='bold', pad=25, fontsize=18, color='#1F2937')
        
        # Add grid
        ax.grid(axis='x', alpha=0.3)
        ax.set_axisbelow(True)
        
        # Set x-axis limit with proper margin for labels
        ax.set_xlim(0, max(percentages) * 1.2)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        # Save with enhanced quality settings
        output_path = self.output_dir / "species_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', pad_inches=0.2)
        plt.close()
        
        return f"temp_charts/{output_path.name}"
    
    def _create_phylum_distribution_chart(self, data: MicrobiomeData) -> str:
        """Create horizontal bar chart showing phylum distribution with reference ranges"""
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#FAFBFC')
        
        # Get phylum data
        phyla = list(data.phylum_distribution.keys())
        percentages = list(data.phylum_distribution.values())
        
        # Reference ranges (from config)
        reference_ranges = {
            'Actinomycetota': (0.1, 8.0),
            'Bacillota': (20.0, 70.0),
            'Bacteroidota': (4.0, 40.0),
            'Pseudomonadota': (2.0, 35.0),
            'Fibrobacterota': (0.1, 5.0)
        }
        
        # Create professional bars with enhanced styling
        y_positions = np.arange(len(phyla))
        colors = [PHYLUM_COLORS.get(p, PHYLUM_COLORS['Other']) for p in phyla]
        bars = ax.barh(y_positions, percentages, height=0.65, 
                      color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
        
        # Add subtle gradient backgrounds
        for i, color in enumerate(colors):
            ax.barh(y_positions[i], percentages[i], height=0.65,
                   color=color, alpha=0.15, zorder=0)
        
        # Enhanced reference range indicators with professional styling
        for i, phylum in enumerate(phyla):
            if phylum in reference_ranges:
                ref_min, ref_max = reference_ranges[phylum]
                # Draw reference range as enhanced background
                ax.fill_betweenx([i-0.25, i+0.25], ref_min, ref_max,
                                color='#6B7280', alpha=0.15, zorder=1)
        
        # Add enhanced percentage labels
        for i, (bar, pct) in enumerate(zip(bars, percentages)):
            label_x = bar.get_width() + 1.0
            ax.text(label_x, bar.get_y() + bar.get_height()/2,
                    f'{pct:.1f}%', va='center', ha='left', 
                    fontsize=12, fontweight='700', color='#1F2937')
        
        # Customize axes
        ax.set_yticks(y_positions)
        ax.set_yticklabels(phyla, fontsize=11, fontweight='bold')
        ax.set_xlabel(self._get_label('percentage'), fontsize=12)
        ax.set_title(self._get_label('phylum_title'),
                    fontweight='bold', fontsize=18, pad=25, color='#1F2937')

        # Add legend for reference ranges
        ax.text(0.98, 0.02, self._get_label('reference_legend'),
                transform=ax.transAxes, ha='right', va='bottom',
                fontsize=8, style='italic', alpha=0.7)
        
        # Grid and styling
        ax.grid(axis='x', alpha=0.3)
        ax.set_axisbelow(True)
        ax.set_xlim(0, 100)
        
        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        # Save with enhanced quality settings
        output_path = self.output_dir / "phylum_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', pad_inches=0.2)
        plt.close()
        
        return f"temp_charts/{output_path.name}"
    
    def _create_phylum_comparison_chart(self, data: MicrobiomeData) -> str:
        """Create visual comparison chart for phylum levels vs reference ranges"""
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#FAFBFC')

        # Reference ranges
        reference_data = {
            'Actinomycetota': {'range': (0.1, 8.0), 'actual': 0},
            'Bacillota': {'range': (20.0, 70.0), 'actual': 0},
            'Bacteroidota': {'range': (4.0, 40.0), 'actual': 0},
            'Pseudomonadota': {'range': (2.0, 35.0), 'actual': 0}
        }

        # Update with actual values
        for phylum, percentage in data.phylum_distribution.items():
            if phylum in reference_data:
                reference_data[phylum]['actual'] = percentage

        # Sort phyla by actual percentage (descending, like species chart)
        sorted_phyla = sorted(reference_data.items(),
                            key=lambda x: x[1]['actual'],
                            reverse=True)

        # Reverse for bottom-to-top display (highest at top)
        sorted_phyla = sorted_phyla[::-1]

        # Create visual bars
        y_position = 0
        bar_height = 0.65

        for phylum, values in sorted_phyla:
            ref_min, ref_max = values['range']
            actual = values['actual']

            # Draw reference range (light background)
            rect = patches.Rectangle((ref_min, y_position - bar_height/2),
                                   ref_max - ref_min, bar_height,
                                   facecolor='#6B7280', alpha=0.15, zorder=1)
            ax.add_patch(rect)

            # Add subtle gradient background
            ax.barh(y_position, actual, height=bar_height,
                   color=PHYLUM_COLORS.get(phylum, PHYLUM_COLORS['Other']),
                   alpha=0.15, zorder=0)

            # Draw actual value bar
            color = PHYLUM_COLORS.get(phylum, PHYLUM_COLORS['Other'])
            bar = ax.barh(y_position, actual, height=bar_height * 0.6,
                         color=color, alpha=0.85, zorder=2)

            # Add label
            ax.text(-2, y_position, f"{phylum}:", ha='right', va='center',
                   fontsize=11, fontweight='bold')

            # Add percentage
            ax.text(actual + 1, y_position, f"{actual:.1f}%",
                   ha='left', va='center', fontsize=12, fontweight='700', color='#1F2937')

            # Add reference range text
            ref_label = self._get_label('ref')
            ax.text(ref_max + 2, y_position, f"({ref_label}: {ref_min}-{ref_max}%)",
                   ha='left', va='center', fontsize=8, style='italic', alpha=0.7)

            y_position += 1.2
        
        # Customize axes
        ax.set_xlim(-15, 80)
        ax.set_ylim(-0.5, y_position - 0.7)
        ax.set_xlabel(self._get_label('percentage'), fontsize=13)
        ax.set_title(self._get_label('phylum_title'),
                    fontweight='bold', fontsize=18, pad=25, color='#1F2937')

        # Remove y-axis
        ax.set_yticks([])

        # Add legend for reference ranges
        ax.text(0.98, 0.02, self._get_label('reference_legend'),
                transform=ax.transAxes, ha='right', va='bottom',
                fontsize=8, style='italic', alpha=0.7)

        # Professional grid and styling
        ax.grid(axis='x', alpha=0.3)
        ax.set_axisbelow(True)

        # Remove spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        plt.tight_layout()
        
        # Save
        output_path = self.output_dir / "phylum_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return f"temp_charts/{output_path.name}"
    
    def cleanup(self):
        """Remove temporary chart files"""
        try:
            for file in self.output_dir.glob("*.png"):
                file.unlink()
            if not list(self.output_dir.iterdir()):
                self.output_dir.rmdir()
        except Exception as e:
            logger.warning(f"Error cleaning up chart files: {e}")