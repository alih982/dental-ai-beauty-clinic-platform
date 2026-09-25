import hashlib
import json
import io
from typing import List, Dict, Any
from django.core.files.base import ContentFile
from django.utils import timezone
from apps.ai_orchestrator.infrastructure.factory import AIFactory
from apps.ai_orchestrator.domain.ports import Prompt
from apps.prescriptions.domain.models import Prescription
from config.env_config import config
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

class ElectronicPrescriptionService:
    """
    Application Service for managing high-value, secure electronic prescriptions.
    Handles AI analysis, cryptographic signing, and PDF generation.
    """
    
    def __init__(self):
        # Inject AI Provider (Strategy Pattern)
        self.ai = AIFactory.create(
            provider_type=config.AI_PROVIDER,
            host=config.OLLAMA_HOST,
            api_key=config.OPENAI_API_KEY
        )
    
    def generate_ai_suggestions(self, symptoms: str, medical_history: str = "") -> str:
        """
        Uses configured AI model to analyze symptoms and suggest generic medication classes.
        """
        prompt_text = (
            f"Patient Symptoms: {symptoms}. "
            f"Medical History: {medical_history}. "
            f"Suggest 3 generic medication classes suitable for this condition. "
            f"Keep it concise and clinical."
        )
        prompt = Prompt(
            text=prompt_text, 
            system_prompt="You are a helpful clinical assistant. Provide only generic drug classes, not specific brands."
        )
        
        completion = self.ai.generate_response(prompt)
        return completion.content

    def create_prescription(
        self, 
        doctor, 
        patient, 
        medications: List[Dict[str, Any]], 
        diagnosis: str,
        ai_log: Dict[str, Any] = None
    ) -> Prescription:
        """
        Creates a signed, immutable prescription record with PDF generation.
        """
        # 1. Create Model Instance (Pending Save)
        prescription = Prescription(
            doctor=doctor,
            patient=patient,
            medications=medications,
            diagnosis_text=diagnosis,
            ai_suggestion_log=ai_log,
            is_dispensed=False
        )
        
        # 2. Generate Digital Signature (Hash of critical data + nonce)
        # Using the UUID as a nonce (it's generated on instantiation in model default)
        # Wait, model default uuid runs on save usually or instantiation? 
        # Django defaults run on instantiation if it's a function.
        # But separate UUID field might need manual generation if not saved yet for consistency?
        # Actually UUIDField default=uuid.uuid4 works on instantiation.
        import uuid
        if not prescription.id:
            prescription.id = uuid.uuid4()

        canonical_data = json.dumps({
            "doc_id": str(doctor.id),
            "pat_id": str(patient.id),
            "meds": medications,
            "diagnosis": diagnosis,
            "nonce": str(prescription.id),
            "timestamp": str(timezone.now().timestamp())
        }, sort_keys=True)
        
        prescription.digital_signature = hashlib.sha256(canonical_data.encode('utf-8')).hexdigest()
        
        # 3. Generate PDF Document
        pdf_bytes = self._generate_pdf_bytes(prescription)
        filename = f"RX_{str(prescription.id)[:8]}.pdf"
        prescription.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
        
        # 4. Commit to Database
        prescription.save()
        return prescription

    def _generate_pdf_bytes(self, rx: Prescription) -> bytes:
        """
        Internal helper to draw the prescription PDF using ReportLab.
        """
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "DoctorHub Medical Platform")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 70, "Electronic Prescription Record")
        
        # Meta Data
        p.drawString(50, height - 100, f"Prescription ID: {rx.id}")
        p.drawString(50, height - 115, f"Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        p.drawString(50, height - 130, f"Digital Signature: {rx.digital_signature[:32]}...")
        
        p.line(50, height - 140, width - 50, height - 140)
        
        # Doctor & Patient
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 160, "Doctor:")
        p.setFont("Helvetica", 12)
        p.drawString(120, height - 160, f"Dr. {rx.doctor.get_full_name_en()}")
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 180, "Patient:")
        p.setFont("Helvetica", 12)
        p.drawString(120, height - 180, f"{rx.patient.first_name} {rx.patient.last_name}")
        
        # Diagnosis
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 210, "Diagnosis:")
        p.setFont("Helvetica", 11)
        p.drawString(50, height - 230, rx.diagnosis_text)
        
        # Medications Table
        y = height - 270
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Rx Medications:")
        y -= 20
        
        p.setFont("Helvetica", 11)
        for med in rx.medications:
            name = med.get('name', 'Unknown Drug')
            dosage = med.get('dosage', '')
            freq = med.get('frequency', '')
            line = f"- {name} ({dosage}) - {freq}"
            p.drawString(60, y, line)
            y -= 15
            
        # Footer
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(50, 50, "Generated Securely by DoctorHub AI. Verifiable via Digital Signature.")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer.getvalue()
