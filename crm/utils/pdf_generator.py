from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from data import db_manager
from utils.localization import tr

class PrescriptionPDFGenerator:
    @staticmethod
    def generate(filename, data):
        """
        Generate a professional medical prescription PDF in A5 format with multi-medication support.
        data dict:
        - patient_name, patient_dob, patient_gender, patient_address
        - visit_date
        - doctor_name or doctor_first_name, doctor_last_name, doctor_title, doctor_speciality
        - medications: list of dicts [{'name': 'Amox', 'dosage': '500mg', 'frequency': '3x/day', 'duration': '7 days'}, ...]
        - instructions
        """
        doc = SimpleDocTemplate(
            filename,
            pagesize=A5,
            rightMargin=12*mm,
            leftMargin=12*mm,
            topMargin=12*mm,
            bottomMargin=12*mm
        )

        styles = getSampleStyleSheet()
        elements = []

        # Fetch clinic information
        clinic = db_manager.get_clinic_info()
        clinic_name = clinic['clinic_name'] if clinic and clinic['clinic_name'] else tr("Medical Clinic")
        clinic_address = clinic['clinic_address'] if clinic and clinic['clinic_address'] else ""
        license_number = clinic['license_number'] if clinic and clinic['license_number'] else ""

        # Styles
        style_clinic_title = ParagraphStyle(
            'ClinicTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1E3A8A") # Navy Blue
        )

        style_clinic_sub = ParagraphStyle(
            'ClinicSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569")
        )

        style_doctor_info = ParagraphStyle(
            'DoctorInfo',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#0F172A")
        )

        style_doctor_sub = ParagraphStyle(
            'DoctorSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#64748B")
        )

        style_patient_label = ParagraphStyle(
            'PatientLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1E293B")
        )

        style_patient_val = ParagraphStyle(
            'PatientVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )

        style_rx_symbol = ParagraphStyle(
            'RxSymbol',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=24,
            textColor=colors.HexColor("#1D4ED8")
        )

        style_doc_title = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=4,
            spaceAfter=4
        )

        style_med_name = ParagraphStyle(
            'MedName',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0F172A")
        )

        style_med_detail = ParagraphStyle(
            'MedDetail',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )

        style_instructions = ParagraphStyle(
            'Instructions',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )

        style_sig_text = ParagraphStyle(
            'SigText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748B")
        )

        style_sig_name = ParagraphStyle(
            'SigName',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0F172A")
        )

        # 1. Header (Clinic Left, Doctor Right)
        doctor_full_name = data.get('doctor_name')
        if not doctor_full_name:
            f_name = data.get('doctor_first_name', 'Doctor')
            l_name = data.get('doctor_last_name', '')
            doctor_full_name = f"Dr. {f_name} {l_name}".strip()

        doctor_spec = data.get('doctor_speciality') or tr('General Practitioner')
        doctor_title = data.get('doctor_title', 'MD')

        clinic_block = [
            Paragraph(clinic_name, style_clinic_title),
            Paragraph(clinic_address, style_clinic_sub),
            Paragraph(f"{tr('License: ')}{license_number}" if license_number else "", style_clinic_sub)
        ]

        doctor_block = [
            Paragraph(doctor_full_name, style_doctor_info),
            Paragraph(f"{doctor_spec} • {doctor_title}", style_doctor_sub),
            Paragraph(f"{tr('Date: ')}{data.get('visit_date', datetime.now().strftime('%Y-%m-%d'))}", style_doctor_sub)
        ]

        header_table = Table([[clinic_block, doctor_block]], colWidths=[2.5*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4*mm))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1D4ED8"), spaceBefore=2, spaceAfter=8))

        # 2. Patient Demographics Box
        p_name = data.get('patient_name', 'N/A')
        p_dob = data.get('patient_dob', 'N/A')
        p_gender = data.get('patient_gender', '')
        p_age = data.get('patient_age', '')
        age_text = f"({p_age} {tr('yrs')})" if p_age else ""

        patient_info_rows = [
            [
                Paragraph(tr("<b>Patient Name:</b>"), style_patient_label),
                Paragraph(p_name, style_patient_val),
                Paragraph(tr("<b>Date of Birth:</b>"), style_patient_label),
                Paragraph(f"{p_dob} {age_text}", style_patient_val),
            ]
        ]
        patient_table = Table(patient_info_rows, colWidths=[1.1*inch, 1.8*inch, 1.0*inch, 1.1*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(patient_table)
        elements.append(Spacer(1, 6*mm))

        # 3. Rx Symbol & Title
        rx_row = [[Paragraph("℞", style_rx_symbol), Paragraph(tr("PRESCRIPTION ORDER"), style_doc_title)]]
        rx_table = Table(rx_row, colWidths=[0.5*inch, 4.5*inch])
        rx_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(rx_table)
        elements.append(Spacer(1, 4*mm))

        # 4. Multi-Medication List
        medications = data.get('medications', [])
        if not isinstance(medications, list):
            medications = [medications]

        med_table_data = [
            [
                Paragraph("<b>#</b>", style_med_name),
                Paragraph(tr("<b>Medication & Dosage</b>"), style_med_name),
                Paragraph(tr("<b>Frequency</b>"), style_med_name),
                Paragraph(tr("<b>Duration</b>"), style_med_name)
            ]
        ]

        for i, med in enumerate(medications, 1):
            if isinstance(med, dict):
                m_name = med.get('medication_name') or med.get('name', '')
                m_dosage = med.get('dosage', '')
                m_freq = med.get('frequency', '')
                m_dur = med.get('duration', '')
            else:
                m_name = str(med)
                m_dosage = ""
                m_freq = ""
                m_dur = ""

            name_dosage = f"<b>{m_name}</b>"
            if m_dosage:
                name_dosage += f" &nbsp;({m_dosage})"

            med_table_data.append([
                Paragraph(str(i), style_med_detail),
                Paragraph(name_dosage, style_med_detail),
                Paragraph(m_freq, style_med_detail),
                Paragraph(m_dur, style_med_detail)
            ])

        med_table = Table(med_table_data, colWidths=[0.3*inch, 2.3*inch, 1.4*inch, 1.0*inch])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EFF6FF")),
            ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#3B82F6")),
            ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(med_table)

        # 5. Clinical Instructions / Notes
        instructions = data.get('instructions')
        if instructions and instructions.strip():
            elements.append(Spacer(1, 6*mm))
            instr_block = [
                Paragraph(tr("<b>Special Instructions / Advice:</b>"), style_patient_label),
                Spacer(1, 2*mm),
                Paragraph(instructions.replace('\n', '<br/>'), style_instructions)
            ]
            instr_table = Table([[instr_block]], colWidths=[5.0*inch])
            instr_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFBEB")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#FDE68A")),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(instr_table)

        # 6. Signature & Verification Footer
        elements.append(Spacer(1, 10*mm))
        date_str = data.get('visit_date', datetime.now().strftime('%Y-%m-%d'))
        sig_box = [
            [Paragraph(tr("Practitioner Signature"), style_sig_text)],
            [Spacer(1, 4*mm)],
            [Paragraph(f"<i>{doctor_full_name}</i>", style_sig_name)],
            [Paragraph(f"{tr('Date: ')}{date_str}", style_sig_text)],
        ]
        sig_table = Table(sig_box, colWidths=[45*mm])
        sig_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor("#475569")),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))

        footer_table = Table([[None, sig_table]], colWidths=[2.8*inch, 2.2*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (1,0), (1,0), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(footer_table)

        doc.build(elements)
