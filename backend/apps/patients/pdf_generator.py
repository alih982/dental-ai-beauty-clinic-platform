"""
PDF Generator for Prescriptions and Invoices
============================================
Generates professional PDF documents for medical prescriptions and invoices.

Author: Hospital Application
Version: 2.0.0
"""

import io
import base64
import hashlib
import hmac
from datetime import datetime
from typing import Optional
from decimal import Decimal

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
        Image, PageBreak, TableStyle
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFGenerator:
    """Base PDF Generator with common functionality"""
    
    # Hospital Information
    HOSPITAL_NAME = "بیمارستان هوشمند DoctorHub"
    HOSPITAL_NAME_EN = "DoctorHub Smart Hospital"
    HOSPITAL_ADDRESS = "تهران، خیابان ولیعصر، پلاک 1"
    HOSPITAL_PHONE = "021-88888888"
    HOSPITAL_EMAIL = "info@DoctorHub.ir"
    HOSPITAL_WEBSITE = "www.DoctorHub.ir"
    
    # Colors
    PRIMARY_COLOR = colors.HexColor("#2563eb")
    SECONDARY_COLOR = colors.HexColor("#059669")
    ACCENT_COLOR = colors.HexColor("#7c3aed")
    TEXT_COLOR = colors.HexColor("#1f2937")
    LIGHT_GRAY = colors.HexColor("#f3f4f6")
    BORDER_COLOR = colors.HexColor("#e5e7eb")
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install with: pip install reportlab"
            )
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title Style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle Style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.SECONDARY_COLOR,
            alignment=TA_CENTER,
            spaceAfter=10
        ))
        
        # Header Style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=self.TEXT_COLOR,
            spaceBefore=15,
            spaceAfter=5,
            fontName='Helvetica-Bold'
        ))
        
        # Normal Style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.TEXT_COLOR,
            spaceBefore=5,
            spaceAfter=5
        ))
        
        # Right-to-Left Persian Style
        self.styles.add(ParagraphStyle(
            name='PersianNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.TEXT_COLOR,
            textDirection='RTL',
            alignment=TA_RIGHT,
            spaceBefore=3,
            spaceAfter=3
        ))
    
    def create_header(self, title: str, subtitle: str = ""):
        """Create PDF header with hospital info"""
        elements = []
        
        # Hospital Logo/Name
        elements.append(Paragraph(self.HOSPITAL_NAME, self.styles['CustomTitle']))
        elements.append(Paragraph(self.HOSPITAL_NAME_EN, self.styles['CustomSubtitle']))
        
        # Address and contact info
        contact_info = f"""
        {self.HOSPITAL_ADDRESS} | تلفن: {self.HOSPITAL_PHONE} | وبسایت: {self.HOSPITAL_WEBSITE}
        """
        elements.append(Paragraph(contact_info, self.styles['CustomNormal']))
        
        # Separator line
        elements.append(Spacer(1, 10))
        
        # Title
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles['CustomSubtitle']))
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def create_footer(self):
        """Create PDF footer"""
        elements = []
        
        # Separator line
        line_table = Table(
            [['', '']],
            colWidths=[19*cm, 1*cm],
            style=TableStyle([
                ('LINEABOVE', (0, 0), (-1, 0), 1, self.BORDER_COLOR),
            ])
        )
        elements.append(line_table)
        
        # Footer text
        footer_text = f"""
        تاریخ صدور: {datetime.now().strftime('%Y/%m/%d')} | 
        سیستم مدیریت بیمارستان DoctorHub
        """
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(footer_text, self.styles['CustomNormal']))
        
        return elements
    
    def generate_signature(self, data: str) -> str:
        """Generate digital signature for document"""
        signature = hmac.new(
            b"DoctorHub_secret_key",
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature


class PrescriptionPDFGenerator(PDFGenerator):
    """Generate PDF for electronic prescriptions"""
    
    def generate(self, prescription) -> bytes:
        """Generate prescription PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # Header
        elements.extend(self.create_header(
            "نسخه الکترونیکی",
            "Electronic Prescription"
        ))
        
        # Prescription Info
        elements.extend(self._create_prescription_info(prescription))
        
        # Patient Info
        elements.extend(self._create_patient_info(prescription))
        
        # Doctor Info
        elements.extend(self._create_doctor_info(prescription))
        
        # Diagnosis
        if prescription.diagnosis:
            elements.extend(self._create_diagnosis(prescription.diagnosis))
        
        # Medications
        elements.extend(self._create_medications(prescription))
        
        # Instructions
        if prescription.instructions:
            elements.extend(self._create_instructions(prescription.instructions))
        
        # Digital Signature
        elements.extend(self._create_signature_section(prescription))
        
        # Footer
        elements.extend(self.create_footer())
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def _create_prescription_info(self, prescription) -> list:
        """Create prescription information section"""
        elements = []
        
        # Prescription number and dates
        data = [
            ['شماره نسخه:', prescription.prescription_number, 'تاریخ صدور:', prescription.issue_date.strftime('%Y/%m/%d')],
            ['تاریخ انقضا:', prescription.expiry_date.strftime('%Y/%m/%d'), 'وضعیت:', prescription.status.upper()],
        ]
        
        table = Table(data, colWidths=[4*cm, 5*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_GRAY),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_patient_info(self, prescription) -> list:
        """Create patient information section"""
        elements = []
        
        patient = prescription.patient
        
        elements.append(Paragraph("اطلاعات بیمار", self.styles['CustomHeader']))
        
        data = [
            ['شماره پرونده:', patient.record_number, 'نام و نام خانوادگی:', patient.full_name],
            ['سن:', str(patient.age), 'جنسیت:', patient.get_gender_display()],
            ['گروه خونی:', patient.blood_type or 'N/A', 'شماره ملی:', patient.national_id],
        ]
        
        if patient.allergies:
            allergies = ', '.join(patient.allergies) if isinstance(patient.allergies, list) else patient.allergies
            data.append(['آلرژی‌ها:', allergies, '', ''])
        
        if patient.chronic_diseases:
            chronic = ', '.join(patient.chronic_diseases) if isinstance(patient.chronic_diseases, list) else patient.chronic_diseases
            data.append(['بیماری‌های زمینه‌ای:', chronic, '', ''])
        
        table = Table(data, colWidths=[4*cm, 5*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_doctor_info(self, prescription) -> list:
        """Create doctor information section"""
        elements = []
        
        doctor = prescription.doctor
        
        elements.append(Paragraph("اطلاعات پزشک", self.styles['CustomHeader']))
        
        data = [
            ['پزشک معالج:', doctor.full_name if doctor else 'N/A', 'تخصص:', doctor.specialty if doctor else 'N/A'],
            ['شماره نظام پزشکی:', doctor.medical_license_number if doctor else 'N/A', 'مهر و امضا:', ''],
        ]
        
        table = Table(data, colWidths=[4*cm, 5*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_diagnosis(self, diagnosis: str) -> list:
        """Create diagnosis section"""
        elements = []
        
        elements.append(Paragraph("تشخیص پزشک", self.styles['CustomHeader']))
        
        diag_table = Table(
            [[diagnosis]],
            colWidths=[17*cm],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.LIGHT_GRAY),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.TEXT_COLOR),
                ('ALIGN', (0, 0), (-1, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ])
        )
        
        elements.append(diag_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_medications(self, prescription) -> list:
        """Create medications section"""
        elements = []
        
        elements.append(Paragraph("داروهای تجویزی", self.styles['CustomHeader']))
        
        # Table header
        header_data = [['#', 'نام دارو', 'دوز', 'تعداد', 'زمان مصرف', 'دستورات']]
        
        # Table rows
        items = prescription.items.all()
        row_data = []
        
        for idx, item in enumerate(items, 1):
            row = [
                str(idx),
                item.medication_name,
                item.dosage,
                str(item.quantity),
                item.frequency,
                item.instructions or '-'
            ]
            row_data.append(row)
        
        if not row_data:
            row_data = [['-', '-', '-', '-', '-', '-']]
        
        full_data = header_data + row_data
        
        table = Table(full_data, colWidths=[1*cm, 4*cm, 3*cm, 2*cm, 4*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_GRAY]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_instructions(self, instructions: str) -> list:
        """Create general instructions section"""
        elements = []
        
        elements.append(Paragraph("دستورات کلی", self.styles['CustomHeader']))
        
        instr_table = Table(
            [[instructions]],
            colWidths=[17*cm],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.TEXT_COLOR),
                ('ALIGN', (0, 0), (-1, 0), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ])
        )
        
        elements.append(instr_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_signature_section(self, prescription) -> list:
        """Create digital signature section"""
        elements = []
        
        elements.append(Paragraph("امضای دیجیتال", self.styles['CustomHeader']))
        
        # Generate signature
        signature_data = f"{prescription.prescription_number}{prescription.patient.national_id}{prescription.issue_date.isoformat()}"
        digital_signature = self.generate_signature(signature_data)
        
        # Save signature to prescription
        prescription.digital_signature = digital_signature
        prescription.signature_timestamp = datetime.now()
        
        data = [
            ['امضای دیجیتال:', digital_signature[:32] + '...'],
            ['زمان امضا:', prescription.signature_timestamp.strftime('%Y/%m/%d %H:%M:%S')],
            ['اعتبارسنجی:', 'این نسخه توسط سیستم DoctorHub صادر شده است'],
        ]
        
        table = Table(data, colWidths=[4*cm, 13*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_GRAY),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        
        return elements


class InvoicePDFGenerator(PDFGenerator):
    """Generate PDF for medical invoices"""
    
    def generate(self, invoice) -> bytes:
        """Generate invoice PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # Header
        elements.extend(self.create_header(
            "فاکتور پزشکی",
            "Medical Invoice"
        ))
        
        # Invoice Info
        elements.extend(self._create_invoice_info(invoice))
        
        # Patient Info
        elements.extend(self._create_patient_info(invoice))
        
        # Items
        elements.extend(self._create_invoice_items(invoice))
        
        # Totals
        elements.extend(self._create_totals(invoice))
        
        # Payment Info
        elements.extend(self._create_payment_info(invoice))
        
        # Digital Signature
        elements.extend(self._create_signature_section(invoice))
        
        # Footer
        elements.extend(self.create_footer())
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def _create_invoice_info(self, invoice) -> list:
        """Create invoice information section"""
        elements = []
        
        status_colors = {
            'draft': colors.gray,
            'pending': colors.orange,
            'paid': colors.green,
            'cancelled': colors.red,
            'refunded': colors.blue
        }
        
        status_color = status_colors.get(invoice.status, colors.gray)
        
        data = [
            ['شماره فاکتور:', invoice.invoice_number, 'نوع فاکتور:', invoice.get_invoice_type_display()],
            ['تاریخ صدور:', invoice.issue_date.strftime('%Y/%m/%d'), 'مهلت پرداخت:', invoice.due_date.strftime('%Y/%m/%d') if invoice.due_date else 'نامحدود'],
            ['وضعیت:', invoice.status.upper(), '', ''],
        ]
        
        table = Table(data, colWidths=[4*cm, 5*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_GRAY),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_patient_info(self, invoice) -> list:
        """Create patient information section"""
        elements = []
        
        patient = invoice.patient
        
        elements.append(Paragraph("اطلاعات بیمار", self.styles['CustomHeader']))
        
        data = [
            ['شماره پرونده:', patient.record_number, 'نام و نام خانوادگی:', patient.full_name],
            ['شماره ملی:', patient.national_id, 'بیمه:', patient.insurance_provider or 'ندارد'],
            ['شماره بیمه:', patient.insurance_number or 'N/A', '', ''],
        ]
        
        table = Table(data, colWidths=[4*cm, 5*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_invoice_items(self, invoice) -> list:
        """Create invoice items section"""
        elements = []
        
        elements.append(Paragraph("خدمات و اقلام", self.styles['CustomHeader']))
        
        # Table header
        header_data = [['#', 'شرح خدمات', 'کد', 'تعداد', 'قیمت واحد', 'تخفیف', 'جمع']]
        
        # Table rows
        items = invoice.items.all()
        row_data = []
        
        for idx, item in enumerate(items, 1):
            total = item.total
            row = [
                str(idx),
                item.description,
                item.service_code or '-',
                str(item.quantity),
                f"{item.unit_price:,.0f}",
                f"{item.discount:,.0f}" if item.discount > 0 else '-',
                f"{total:,.0f}"
            ]
            row_data.append(row)
        
        if not row_data:
            row_data = [['-', '-', '-', '-', '-', '-', '-']]
        
        full_data = header_data + row_data
        
        table = Table(full_data, colWidths=[1*cm, 6*cm, 2*cm, 1.5*cm, 2.5*cm, 2*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_GRAY]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_totals(self, invoice) -> list:
        """Create totals section"""
        elements = []
        
        elements.append(Paragraph("جمع‌آوری", self.styles['CustomHeader']))
        
        data = [
            ['جمع کل:', f"{invoice.subtotal:,.0f} ریال"],
            ['تخفیف:', f"- {invoice.discount:,.0f} ریال"],
            ['مالیات:', f"+ {invoice.tax:,.0f} ریال"],
            ['جمع نهایی:', f"<b>{invoice.total:,.0f}</b> ریال"],
        ]
        
        table = Table(data, colWidths=[10*cm, 7*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 10))
        
        # Insurance and patient pay
        if invoice.insurance_coverage > 0:
            insurance_data = [
                ['پوشش بیمه:', f"{invoice.insurance_coverage}% ({invoice.insurance_amount:,.0f} ریال)"],
                ['مبلغ پرداختی بیمار:', f"<b>{invoice.patient_pay:,.0f}</b> ریال"],
            ]
            
            ins_table = Table(insurance_data, colWidths=[10*cm, 7*cm])
            ins_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_GRAY),
                ('TEXTCOLOR', (0, 0), (-1, -1), self.SECONDARY_COLOR),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, self.SECONDARY_COLOR),
            ]))
            
            elements.append(ins_table)
        
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_payment_info(self, invoice) -> list:
        """Create payment information section"""
        elements = []
        
        elements.append(Paragraph("اطلاعات پرداخت", self.styles['CustomHeader']))
        
        if invoice.status == 'paid':
            data = [
                ['روش پرداخت:', invoice.get_payment_method_display() if invoice.payment_method else 'N/A'],
                ['شماره مرجع:', invoice.payment_reference or 'N/A'],
                ['تاریخ پرداخت:', invoice.paid_at.strftime('%Y/%m/%d %H:%M:%S') if invoice.paid_at else 'N/A'],
            ]
        else:
            data = [
                ['وضعیت پرداخت:', 'در انتظار پرداخت'],
                ['مبلغ قابل پرداخت:', f"{invoice.patient_pay:,.0f} ریال"],
                ['شماره شبا:', 'IR-000000000000000000000000'],
                ['شماره کارت:', '0000-0000-0000-0000'],
            ]
        
        table = Table(data, colWidths=[4*cm, 13*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_signature_section(self, invoice) -> list:
        """Create digital signature section"""
        elements = []
        
        # Generate signature
        signature_data = f"{invoice.invoice_number}{invoice.patient.national_id}{invoice.issue_date.isoformat()}{invoice.total}"
        digital_signature = self.generate_signature(signature_data)
        
        data = [
            ['امضای دیجیتال:', digital_signature[:32] + '...'],
            ['اعتبارسنجی:', 'این فاکتور توسط سیستم DoctorHub صادر شده است'],
        ]
        
        table = Table(data, colWidths=[4*cm, 13*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_GRAY),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
        ]))
        
        elements.append(table)
        
        return elements


# ============== Helper Functions ==============
def generate_prescription_pdf(prescription) -> bytes:
    """Generate prescription PDF - convenience function"""
    generator = PrescriptionPDFGenerator()
    return generator.generate(prescription)


def generate_invoice_pdf(invoice) -> bytes:
    """Generate invoice PDF - convenience function"""
    generator = InvoicePDFGenerator()
    return generator.generate(invoice)


def get_pdf_base64(pdf_bytes: bytes) -> str:
    """Convert PDF bytes to base64 for embedding in HTML"""
    return base64.b64encode(pdf_bytes).decode('utf-8')

