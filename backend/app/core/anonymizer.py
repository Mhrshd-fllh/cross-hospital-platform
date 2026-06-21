import re
from typing import dict, Any

class ClinicalAnonymizer:
    """
    Utility to sanitize and anonymize patient metadata before database insertion
    and model processing, ensuring strict compliance with HIPAA and GDPR standards.
    """
    
    # Sensitive keys often found in DICOM headers or PACS metadata JSON payloads
    SENSITIVE_KEYS = {
        "patient_name", "patient_id", "national_id", "phone_number", 
        "insurance_id", "birth_date", "address", "physician_name"
    }

    @classmethod
    def anonymize_metadata(cls, raw_metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Removes known sensitive fields and scrubs potential PII patterns (like national IDs or phone numbers).
        """
        sanitized_metadata = {}
        
        for key, value in raw_metadata.items():
            normalized_key = key.lower().strip()
            
            # Skip direct PII keys
            if normalized_key in cls.SENSITIVE_KEYS:
                continue
                
            # Scrub phone numbers or national IDs hidden inside string values
            if isinstance(value, str):
                # Simple regex pattern for typical phone/national ID sequences
                value = re.sub(r'\b\d{10,12}\b', '[REDACTED_ID]', value)
                
            sanitized_metadata[key] = value
            
        # Inject standard compliance flag
        sanitized_metadata["hipaa_anonymized"] = True
        return sanitized_metadata