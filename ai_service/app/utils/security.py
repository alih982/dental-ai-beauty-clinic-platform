import re
import logging

logger = logging.getLogger(__name__)

# Patterns for common PHI (Personal Health Information)
PHI_PATTERNS = {
    "phone": r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "national_id": r"\d{10,12}", 
    "uae_id": r"784-\d{4}-\d{7}-\d{1}", # Dubai/UAE Emirates ID
    "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
    "date_of_birth": r"\b(0?[1-9]|[12]\d|3[01])[-/](0?[1-9]|1[0-2])[-/](19|20)\d{2}\b"
}

def scrub_phi(text: str) -> str:
    """
    Scrubs potential PHI from the text to ensure compliance.
    Replaces sensitive data with [REDACTED].
    """
    scrubbed_text = text
    for label, pattern in PHI_PATTERNS.items():
        matches = re.findall(pattern, scrubbed_text)
        if matches:
            logger.info(f"Redacting potential {label} from AI request")
            scrubbed_text = re.sub(pattern, f"[REDACTED {label.upper()}]", scrubbed_text)
    
    return scrubbed_text
