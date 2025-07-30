"""
Test fixtures for PatientInfo data

Provides realistic sample patient data for testing data models
and report generation functionality.
"""

from src.data_models import PatientInfo

# Standard test patients
PATIENT_MONTANA = PatientInfo(
    name="Montana",
    species="Horse",
    age="20 years",
    sample_number="506",
    date_received="2024-04-23",
    date_analyzed="2024-04-25",
    performed_by="Julia Kończak",
    requested_by="Dr. Alexandra Matusiak"
)

PATIENT_THUNDER = PatientInfo(
    name="Thunder",
    species="Horse", 
    age="15 years",
    sample_number="507",
    date_received="2024-04-23",
    date_analyzed="2024-04-25",
    performed_by="Laboratory Staff",
    requested_by="Dr. Emily Johnson"
)

PATIENT_MINIMAL = PatientInfo(
    name="TestHorse",
    sample_number="001"
)

# Edge case patients
PATIENT_EMPTY_FIELDS = PatientInfo(
    name="",
    age="",
    sample_number="",
    performed_by="",
    requested_by=""
)

PATIENT_UNICODE = PatientInfo(
    name="Bożena",
    species="Koń", 
    age="12 lat",
    sample_number="508",
    performed_by="Dr. François López",
    requested_by="獣医師 田中"
)

PATIENT_LONG_FIELDS = PatientInfo(
    name="A" * 100,
    species="Horse",
    age="Very old horse with extensive medical history",
    sample_number="LONG_SAMPLE_NUMBER_123456789",
    performed_by="Dr. Very Long Name With Multiple Credentials PhD DVM DACVIM",
    requested_by="Another Very Long Name For Testing Purposes Only"
)

# Collection of all test patients
ALL_TEST_PATIENTS = [
    PATIENT_MONTANA,
    PATIENT_THUNDER, 
    PATIENT_MINIMAL,
    PATIENT_EMPTY_FIELDS,
    PATIENT_UNICODE,
    PATIENT_LONG_FIELDS
]

def get_patient_by_name(name: str) -> PatientInfo:
    """Get patient by name for testing"""
    for patient in ALL_TEST_PATIENTS:
        if patient.name == name:
            return patient
    raise ValueError(f"No test patient found with name: {name}")

def get_default_patient() -> PatientInfo:
    """Get default patient for simple tests"""
    return PATIENT_MONTANA

def get_sample_patient_data():
    """Get sample patient information as dict for testing"""
    return {
        "name": "Montana",
        "age": "20 years",
        "species": "Horse",
        "sample_number": "506",
        "date_received": "2024-04-23",
        "date_analyzed": "2024-04-25",
        "performed_by": "Julia Kończak",
        "requested_by": "Dr. Alexandra Matusiak"
    }

def get_batch_patient_data():
    """Get multiple patient data sets for batch testing"""
    return [
        {
            "sample_name": "sample_normal",
            "csv_file": "sample_normal.csv",
            "patient_name": "Montana",
            "patient_age": "20 years",
            "sample_number": "506",
            "barcode": "barcode01"
        },
        {
            "sample_name": "sample_dysbiotic",
            "csv_file": "sample_dysbiotic.csv", 
            "patient_name": "Thunder",
            "patient_age": "12 years",
            "sample_number": "507",
            "barcode": "barcode01"
        },
        {
            "sample_name": "sample_minimal",
            "csv_file": "sample_minimal.csv",
            "patient_name": "Lightning",
            "patient_age": "8 years", 
            "sample_number": "508",
            "barcode": "barcode01"
        }
    ]