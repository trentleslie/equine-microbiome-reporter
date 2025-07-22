"""
Chart Generator - Creates professional data visualizations using Matplotlib
Generates charts matching the reference PDF design
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging

from .data_models import MicrobiomeData

logger = logging.getLogger(__name__)

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
    
    def __init__(self, output_dir: str = "temp_charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set professional style
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Set default font sizes
        plt.rcParams.update({
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.dpi': 300
        })
    
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
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
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
        
        # Create bars
        y_positions = np.arange(len(species_names))
        bars = ax.barh(y_positions, percentages, color=colors, alpha=0.8)
        
        # Add percentage labels
        for i, (bar, pct) in enumerate(zip(bars, percentages)):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    f'{pct:.2f}%', va='center', fontsize=9)
        
        # Customize axes
        ax.set_yticks(y_positions)
        ax.set_yticklabels([f"{i+1}. {name[:40]}" for i, name in enumerate(species_names[::-1])], 
                          fontsize=9)
        ax.set_xlabel('Percentage (%)')
        ax.set_title('MICROBIOTIC PROFILE - Top Species Distribution', 
                    fontweight='bold', pad=20)
        
        # Add grid
        ax.grid(axis='x', alpha=0.3)
        ax.set_axisbelow(True)
        
        # Set x-axis limit
        ax.set_xlim(0, max(percentages) * 1.15)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        # Save
        output_path = self.output_dir / "species_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_path.absolute())
    
    def _create_phylum_distribution_chart(self, data: MicrobiomeData) -> str:
        """Create horizontal bar chart showing phylum distribution with reference ranges"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
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
        
        # Create bars
        y_positions = np.arange(len(phyla))
        bars = ax.barh(y_positions, percentages, height=0.6, 
                      color=[PHYLUM_COLORS.get(p, PHYLUM_COLORS['Other']) for p in phyla],
                      alpha=0.8)
        
        # Add reference range indicators
        for i, phylum in enumerate(phyla):
            if phylum in reference_ranges:
                ref_min, ref_max = reference_ranges[phylum]
                # Draw reference range as a line
                ax.plot([ref_min, ref_max], [i, i], 'k-', linewidth=8, alpha=0.2, zorder=0)
                ax.plot([ref_min, ref_min], [i-0.2, i+0.2], 'k-', linewidth=2, alpha=0.5)
                ax.plot([ref_max, ref_max], [i-0.2, i+0.2], 'k-', linewidth=2, alpha=0.5)
        
        # Add percentage labels
        for i, (bar, pct) in enumerate(zip(bars, percentages)):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{pct:.1f}%', va='center', fontweight='bold')
        
        # Customize axes
        ax.set_yticks(y_positions)
        ax.set_yticklabels(phyla, fontsize=11, fontweight='bold')
        ax.set_xlabel('Percentage (%)', fontsize=12)
        ax.set_title('PHYLUM DISTRIBUTION IN GUT MICROFLORA', 
                    fontweight='bold', fontsize=14, pad=20)
        
        # Add legend for reference ranges
        ax.text(0.98, 0.02, 'Gray bars indicate reference ranges', 
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
        
        # Save
        output_path = self.output_dir / "phylum_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_path.absolute())
    
    def _create_phylum_comparison_chart(self, data: MicrobiomeData) -> str:
        """Create visual comparison chart for phylum levels vs reference ranges"""
        fig, ax = plt.subplots(figsize=(10, 4))
        
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
        
        # Create visual bars
        y_position = 0
        bar_height = 0.8
        
        for phylum, values in reference_data.items():
            ref_min, ref_max = values['range']
            actual = values['actual']
            
            # Draw reference range (light background)
            rect = patches.Rectangle((ref_min, y_position - bar_height/2), 
                                   ref_max - ref_min, bar_height,
                                   facecolor='lightgray', alpha=0.3, zorder=1)
            ax.add_patch(rect)
            
            # Draw actual value bar
            color = PHYLUM_COLORS.get(phylum, PHYLUM_COLORS['Other'])
            bar = ax.barh(y_position, actual, height=bar_height * 0.6,
                         color=color, alpha=0.8, zorder=2)
            
            # Add label
            ax.text(-2, y_position, f"{phylum}:", ha='right', va='center', fontweight='bold')
            
            # Add percentage
            ax.text(actual + 1, y_position, f"{actual:.1f}%", 
                   ha='left', va='center', fontweight='bold')
            
            # Add reference range text
            ax.text(ref_max + 2, y_position, f"(Ref: {ref_min}-{ref_max}%)",
                   ha='left', va='center', fontsize=8, style='italic', alpha=0.7)
            
            y_position += 1.2
        
        # Customize
        ax.set_xlim(-15, 80)
        ax.set_ylim(-0.5, y_position - 0.7)
        ax.set_xlabel('Percentage (%)')
        ax.set_title('Phylum Levels vs Reference Ranges', fontweight='bold', pad=20)
        
        # Remove y-axis
        ax.set_yticks([])
        
        # Grid
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
        
        return str(output_path.absolute())
    
    def cleanup(self):
        """Remove temporary chart files"""
        try:
            for file in self.output_dir.glob("*.png"):
                file.unlink()
            if not list(self.output_dir.iterdir()):
                self.output_dir.rmdir()
        except Exception as e:
            logger.warning(f"Error cleaning up chart files: {e}")