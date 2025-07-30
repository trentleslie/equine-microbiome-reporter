"""
Comprehensive test suite for data_models.py

Tests both PatientInfo and MicrobiomeData dataclasses including:
- Valid instantiation
- Default value handling  
- Field validation
- Edge cases and boundary conditions
- Serialization/deserialization
- Business logic validation
"""

import pytest
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Any
import json

from src.data_models import PatientInfo, MicrobiomeData


class TestPatientInfo:
    """Test suite for PatientInfo dataclass"""
    
    def test_valid_instantiation(self):
        """Test creating PatientInfo with valid data"""
        patient = PatientInfo(
            name="Montana",
            species="Horse", 
            age="20 years",
            sample_number="506",
            performed_by="Julia Kończak",
            requested_by="Dr. Alexandra Matusiak"
        )
        
        assert patient.name == "Montana"
        assert patient.species == "Horse"
        assert patient.age == "20 years"
        assert patient.sample_number == "506"
        assert patient.performed_by == "Julia Kończak"
        assert patient.requested_by == "Dr. Alexandra Matusiak"
        
    def test_default_values(self):
        """Test default value handling"""
        patient = PatientInfo()
        
        assert patient.name == "Unknown"
        assert patient.species == "Horse"
        assert patient.age == "Unknown"
        assert patient.sample_number == "001"
        assert patient.performed_by == "Laboratory Staff"
        assert patient.requested_by == "Veterinarian"
        
    def test_date_auto_generation(self):
        """Test that dates are auto-generated with current date"""
        patient = PatientInfo()
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        assert patient.date_received == current_date
        assert patient.date_analyzed == current_date
        
    def test_partial_instantiation(self):
        """Test creating PatientInfo with some fields specified"""
        patient = PatientInfo(
            name="Thunder",
            age="15 years"
        )
        
        assert patient.name == "Thunder"
        assert patient.age == "15 years"
        assert patient.species == "Horse"  # default
        assert patient.sample_number == "001"  # default
        
    def test_empty_string_handling(self):
        """Test handling of empty strings"""
        patient = PatientInfo(
            name="",
            age="",
            sample_number=""
        )
        
        assert patient.name == ""
        assert patient.age == ""
        assert patient.sample_number == ""
        
    def test_special_characters_in_fields(self):
        """Test handling of special characters and unicode"""
        patient = PatientInfo(
            name="Bożena",
            performed_by="Dr. François López",
            requested_by="獣医師 田中"
        )
        
        assert patient.name == "Bożena"
        assert patient.performed_by == "Dr. François López"
        assert patient.requested_by == "獣医師 田中"
        
    def test_long_field_values(self):
        """Test handling of very long field values"""
        long_name = "A" * 1000
        patient = PatientInfo(name=long_name)
        
        assert patient.name == long_name
        assert len(patient.name) == 1000
        
    def test_serialization_to_dict(self):
        """Test conversion to dictionary"""
        patient = PatientInfo(
            name="Montana",
            age="20 years",
            sample_number="506"
        )
        
        patient_dict = asdict(patient)
        
        assert isinstance(patient_dict, dict)
        assert patient_dict["name"] == "Montana"
        assert patient_dict["age"] == "20 years"
        assert patient_dict["sample_number"] == "506"
        assert "date_received" in patient_dict
        assert "date_analyzed" in patient_dict
        
    def test_json_serialization(self):
        """Test JSON serialization and deserialization"""
        patient = PatientInfo(
            name="Thunder",
            species="Horse",
            age="15 years"
        )
        
        # Serialize to JSON
        patient_json = json.dumps(asdict(patient))
        assert isinstance(patient_json, str)
        
        # Deserialize from JSON
        patient_data = json.loads(patient_json)
        reconstructed = PatientInfo(**patient_data)
        
        assert reconstructed.name == patient.name
        assert reconstructed.species == patient.species
        assert reconstructed.age == patient.age
        
    def test_field_types(self):
        """Test that all fields accept string values"""
        patient = PatientInfo(
            name="Test",
            species="Horse",
            age="10",
            sample_number="123",
            date_received="2024-01-01",
            date_analyzed="2024-01-02",
            performed_by="Staff",
            requested_by="Vet"
        )
        
        # All fields should be strings
        assert isinstance(patient.name, str)
        assert isinstance(patient.species, str)
        assert isinstance(patient.age, str)
        assert isinstance(patient.sample_number, str)
        assert isinstance(patient.date_received, str)
        assert isinstance(patient.date_analyzed, str)
        assert isinstance(patient.performed_by, str)
        assert isinstance(patient.requested_by, str)


class TestMicrobiomeData:
    """Test suite for MicrobiomeData dataclass"""
    
    def test_valid_instantiation(self):
        """Test creating MicrobiomeData with valid data"""
        species_data = [
            {"name": "Bacteroides fragilis", "percentage": 15.5, "phylum": "Bacteroidota", "genus": "Bacteroides"},
            {"name": "Escherichia coli", "percentage": 8.2, "phylum": "Pseudomonadota", "genus": "Escherichia"}
        ]
        
        phylum_dist = {
            "Bacteroidota": 25.5,
            "Pseudomonadota": 18.2,
            "Bacillota": 45.0,
            "Actinomycetota": 11.3
        }
        
        microbiome = MicrobiomeData(
            species_list=species_data,
            phylum_distribution=phylum_dist,
            dysbiosis_index=35.5,
            total_species_count=150,
            dysbiosis_category="mild",
            clinical_interpretation="Mild dysbiosis detected",
            recommendations=["Probiotic supplementation", "Dietary modification"]
        )
        
        assert len(microbiome.species_list) == 2
        assert microbiome.species_list[0]["name"] == "Bacteroides fragilis"
        assert microbiome.phylum_distribution["Bacillota"] == 45.0
        assert microbiome.dysbiosis_index == 35.5
        assert microbiome.total_species_count == 150
        assert microbiome.dysbiosis_category == "mild"
        assert len(microbiome.recommendations) == 2
        
    def test_default_values(self):
        """Test default value handling"""
        microbiome = MicrobiomeData()
        
        assert microbiome.species_list == []
        assert microbiome.phylum_distribution == {}
        assert microbiome.dysbiosis_index == 0.0
        assert microbiome.total_species_count == 0
        assert microbiome.dysbiosis_category == "normal"
        assert microbiome.clinical_interpretation == ""
        assert microbiome.recommendations == []
        assert microbiome.parasite_results == []
        assert microbiome.microscopic_results == []
        assert microbiome.biochemical_results == []
        assert microbiome.llm_summary is None
        assert microbiome.llm_recommendations is None
        
    def test_species_list_structure(self):
        """Test species list has correct structure"""
        species_data = [
            {"name": "Lactobacillus acidophilus", "percentage": 12.5, "phylum": "Bacillota", "genus": "Lactobacillus"},
            {"name": "Bifidobacterium longum", "percentage": 8.3, "phylum": "Actinomycetota", "genus": "Bifidobacterium"}
        ]
        
        microbiome = MicrobiomeData(species_list=species_data)
        
        # Check structure of each species entry
        for species in microbiome.species_list:
            assert "name" in species
            assert "percentage" in species
            assert "phylum" in species
            assert "genus" in species
            assert isinstance(species["name"], str)
            assert isinstance(species["percentage"], (int, float))
            assert isinstance(species["phylum"], str)
            assert isinstance(species["genus"], str)
            
    def test_phylum_distribution_validation(self):
        """Test phylum distribution percentages"""
        # Test normal distribution
        phylum_dist = {
            "Bacteroidota": 25.0,
            "Pseudomonadota": 15.0,
            "Bacillota": 50.0,
            "Actinomycetota": 10.0
        }
        
        microbiome = MicrobiomeData(phylum_distribution=phylum_dist)
        
        # Should sum to 100%
        total_percentage = sum(microbiome.phylum_distribution.values())
        assert abs(total_percentage - 100.0) < 0.1  # Allow small floating point errors
        
        # All values should be positive
        for percentage in microbiome.phylum_distribution.values():
            assert percentage >= 0
            
    def test_dysbiosis_index_boundary_conditions(self):
        """Test dysbiosis index edge cases"""
        # Test zero dysbiosis
        microbiome_normal = MicrobiomeData(dysbiosis_index=0.0, dysbiosis_category="normal")
        assert microbiome_normal.dysbiosis_index == 0.0
        assert microbiome_normal.dysbiosis_category == "normal"
        
        # Test mild dysbiosis threshold
        microbiome_mild = MicrobiomeData(dysbiosis_index=35.0, dysbiosis_category="mild")
        assert microbiome_mild.dysbiosis_index == 35.0
        assert microbiome_mild.dysbiosis_category == "mild"
        
        # Test severe dysbiosis
        microbiome_severe = MicrobiomeData(dysbiosis_index=75.0, dysbiosis_category="severe")
        assert microbiome_severe.dysbiosis_index == 75.0
        assert microbiome_severe.dysbiosis_category == "severe"
        
    def test_clinical_interpretation_categories(self):
        """Test valid dysbiosis categories"""
        valid_categories = ["normal", "mild", "severe"]
        
        for category in valid_categories:
            microbiome = MicrobiomeData(dysbiosis_category=category)
            assert microbiome.dysbiosis_category == category
            
    def test_laboratory_results_structure(self):
        """Test laboratory results have correct structure"""
        parasite_results = [
            {"parameter": "Giardia", "result": "Negative", "reference": "Negative"},
            {"parameter": "Cryptosporidium", "result": "Negative", "reference": "Negative"}
        ]
        
        microscopic_results = [
            {"parameter": "Leukocytes", "result": "2-4/hpf", "reference": "0-5/hpf"},
            {"parameter": "Erythrocytes", "result": "0/hpf", "reference": "0-2/hpf"}
        ]
        
        biochemical_results = [
            {"parameter": "pH", "result": "7.2", "reference": "6.5-7.5"},
            {"parameter": "Occult Blood", "result": "Negative", "reference": "Negative"}
        ]
        
        microbiome = MicrobiomeData(
            parasite_results=parasite_results,
            microscopic_results=microscopic_results,
            biochemical_results=biochemical_results
        )
        
        # Check parasite results structure
        for result in microbiome.parasite_results:
            assert "parameter" in result
            assert "result" in result
            assert "reference" in result
            
        # Check microscopic results structure
        for result in microbiome.microscopic_results:
            assert "parameter" in result
            assert "result" in result
            assert "reference" in result
            
        # Check biochemical results structure
        for result in microbiome.biochemical_results:
            assert "parameter" in result
            assert "result" in result
            assert "reference" in result
            
    def test_recommendations_list(self):
        """Test recommendations handling"""
        recommendations = [
            "Probiotic supplementation with Lactobacillus species",
            "Increase fiber intake through hay quality improvement",
            "Consider prebiotic supplementation",
            "Follow-up testing in 6-8 weeks"
        ]
        
        microbiome = MicrobiomeData(recommendations=recommendations)
        
        assert len(microbiome.recommendations) == 4
        assert all(isinstance(rec, str) for rec in microbiome.recommendations)
        assert "Probiotic supplementation" in microbiome.recommendations[0]
        
    def test_llm_content_optional(self):
        """Test LLM content fields are optional"""
        # Test with LLM content
        microbiome_with_llm = MicrobiomeData(
            llm_summary="AI-generated clinical summary",
            llm_recommendations=["AI recommendation 1", "AI recommendation 2"]
        )
        
        assert microbiome_with_llm.llm_summary == "AI-generated clinical summary"
        assert len(microbiome_with_llm.llm_recommendations) == 2
        
        # Test without LLM content (defaults)
        microbiome_no_llm = MicrobiomeData()
        assert microbiome_no_llm.llm_summary is None
        assert microbiome_no_llm.llm_recommendations is None
        
    def test_large_species_list(self):
        """Test handling of large species lists"""
        # Create large species list (typical microbiome has 100-500 species)
        large_species_list = []
        for i in range(300):
            species = {
                "name": f"Species_{i}",
                "percentage": round(100.0 / 300, 3),  # Equal distribution
                "phylum": f"Phylum_{i % 5}",  # Rotate through 5 phyla
                "genus": f"Genus_{i}"
            }
            large_species_list.append(species)
            
        microbiome = MicrobiomeData(
            species_list=large_species_list,
            total_species_count=300
        )
        
        assert len(microbiome.species_list) == 300
        assert microbiome.total_species_count == 300
        
        # Check that all entries are properly structured
        for species in microbiome.species_list:
            assert all(key in species for key in ["name", "percentage", "phylum", "genus"])
            
    def test_serialization_to_dict(self):
        """Test conversion to dictionary"""
        microbiome = MicrobiomeData(
            dysbiosis_index=42.5,
            total_species_count=125,
            dysbiosis_category="mild",
            clinical_interpretation="Moderate dysbiosis",
            recommendations=["Diet change", "Probiotics"]
        )
        
        microbiome_dict = asdict(microbiome)
        
        assert isinstance(microbiome_dict, dict)
        assert microbiome_dict["dysbiosis_index"] == 42.5
        assert microbiome_dict["total_species_count"] == 125
        assert microbiome_dict["dysbiosis_category"] == "mild"
        assert len(microbiome_dict["recommendations"]) == 2
        
    def test_json_serialization(self):
        """Test JSON serialization and deserialization"""
        original_data = MicrobiomeData(
            species_list=[{"name": "Test species", "percentage": 10.0, "phylum": "Test", "genus": "Test"}],
            phylum_distribution={"Test": 100.0},
            dysbiosis_index=25.0,
            total_species_count=50,
            recommendations=["Test recommendation"]
        )
        
        # Serialize to JSON
        data_dict = asdict(original_data)
        json_str = json.dumps(data_dict)
        assert isinstance(json_str, str)
        
        # Deserialize from JSON
        restored_dict = json.loads(json_str)
        restored_data = MicrobiomeData(**restored_dict)
        
        assert restored_data.dysbiosis_index == original_data.dysbiosis_index
        assert restored_data.total_species_count == original_data.total_species_count
        assert len(restored_data.species_list) == len(original_data.species_list)
        assert restored_data.recommendations == original_data.recommendations
        
    def test_empty_collections_handling(self):
        """Test handling of empty lists and dictionaries"""
        microbiome = MicrobiomeData(
            species_list=[],
            phylum_distribution={},
            recommendations=[],
            parasite_results=[],
            microscopic_results=[],
            biochemical_results=[]
        )
        
        assert microbiome.species_list == []
        assert microbiome.phylum_distribution == {}
        assert microbiome.recommendations == []
        assert microbiome.parasite_results == []
        assert microbiome.microscopic_results == []
        assert microbiome.biochemical_results == []


class TestDataModelIntegration:
    """Integration tests for both data models working together"""
    
    def test_complete_report_data_structure(self):
        """Test creating complete report data with both models"""
        # Create patient info
        patient = PatientInfo(
            name="Montana",
            age="20 years",
            sample_number="506",
            performed_by="Julia Kończak",
            requested_by="Dr. Alexandra Matusiak"
        )
        
        # Create microbiome data
        microbiome = MicrobiomeData(
            species_list=[
                {"name": "Bacteroides fragilis", "percentage": 15.5, "phylum": "Bacteroidota", "genus": "Bacteroides"}
            ],
            phylum_distribution={"Bacteroidota": 25.0, "Bacillota": 75.0},
            dysbiosis_index=18.5,
            total_species_count=147,
            dysbiosis_category="normal",
            clinical_interpretation="Normal microbiome composition",
            recommendations=["Maintain current diet", "Continue monitoring"]
        )
        
        # Test that both models work together
        assert patient.name == "Montana"
        assert patient.sample_number == "506"
        assert microbiome.dysbiosis_category == "normal"
        assert microbiome.total_species_count == 147
        
        # Test serialization of both
        patient_dict = asdict(patient)
        microbiome_dict = asdict(microbiome)
        
        combined_report = {
            "patient_info": patient_dict,
            "microbiome_data": microbiome_dict
        }
        
        assert "patient_info" in combined_report
        assert "microbiome_data" in combined_report
        assert combined_report["patient_info"]["name"] == "Montana"
        assert combined_report["microbiome_data"]["dysbiosis_category"] == "normal"