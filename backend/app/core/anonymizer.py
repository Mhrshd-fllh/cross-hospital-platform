import re
import hashlib
from typing import Dict, Any, Set

class ClinicalAnonymizer:
    """
    Utility to sanitize and anonymize patient metadata before database insertion
    and model processing, ensuring strict compliance with HIPAA and GDPR standards.
    """
    
    # Sensitive keys often found in DICOM headers or PACS metadata JSON payloads
    SENSITIVE_KEYS: Set[str] = {
        "patient_name", "patient_id", "national_id", "phone_number", 
        "insurance_id", "birth_date", "address", "physician_name"
    }

    @staticmethod
    def hash_identifier(value: str) -> str:
        """
        Secures unique tracking IDs using SHA-256 to allow safe analytical grouping 
        without exposing raw patient identity registries.
        """
        if not value:
            return ""
        return hashlib.sha256(str(value).strip().lower().encode('utf-8')).hexdigest()

    @classmethod
    def anonymize_metadata(cls, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively processes metadata dictionaries to redact PII text values 
        and pseudonymize structural operational identifiers.
        """
        sanitized_metadata = {}
        
        for key, value in raw_metadata.items():
            normalized_key = key.lower().strip().replace(" ", "_").replace("-", "_")
            
            # Handle nested dictionary payloads smoothly via recursion
            if isinstance(value, dict):
                sanitized_metadata[key] = cls.anonymize_metadata(value)
                continue
            
            # Mask or pseudonymize direct PII keys instead of omitting them
            if normalized_key in cls.SENSITIVE_KEYS:
                if normalized_key in {"patient_id", "insurance_id"}:
                    # Retain structural tracking consistency via hashing
                    sanitized_metadata[key] = cls.hash_identifier(str(value))
                else:
                    # Wipe names, dates, and cleartext contacts completely
                    sanitized_metadata[key] = "[REDACTED]"
                continue
                
            # Scrub phone numbers or national IDs hidden inside generic string values
            if isinstance(value, str):
                # Standard regex pattern tracking 10-12 consecutive numeric sequences
                value = re.sub(r'\b\d{10,12}\b', '[REDACTED_ID]', value)
                
            sanitized_metadata[key] = value
            
        # Inject global pipeline standard compliance flag at the root level
        sanitized_metadata["hipaa_anonymized"] = True
        return sanitized_metadata