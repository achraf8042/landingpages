from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from data import db_manager
from utils import currency as currency_mod
from utils.localization import tr

class InvoicePDFGenerator:
    @staticmethod
    def generate(filename, bill_id):
        """
        Generate a professional patient medical invoice / receipt PDF in A5 format.
        """
        details = db_manager.get_bill_details(bill_id)
        if not details:
            raise ValueError(f"Bill #{bill_id} not found")

        bill = details['bill']
        items = details['items']

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

        clinic = db_manager.get_clinic_info()
        clinic_name = clinic['clinic_name'] if clinic and clinic['clinic_name'] else tr("Medical Clinic")
        clinic_address = clinic['clinic_address'] if clinic and clinic['clinic_address'] else ""
        license_number = clinic['license_number'] if clinic and clinic['license_number'] else ""

        # The invoice's own currency wins: past receipts must not change meaning
        # when the clinic later switches currency in Settings.
        bill_keys = bill.keys()
        clinic_code, clinic_symbol, clinic_position = currency_mod.clinic_currency(clinic)
        bill_code = (bill['currency_code'] if 'currency_code' in bill_keys else '') or clinic_code
        cur_symbol = currency_mod.symbol_for(bill_code, clinic_symbol)
        cur_position = clinic_position
        money = lambda amount: currency_mod.format_money(amount, cur_symbol, cur_position)

        insurer = (bill['insurance_provider'] if 'insurance_provider' in bill_keys else '') or ""
        member_no = (bill['insurance_member_no'] if 'insurance_member_no' in bill_keys else '') or ""
        coverage_pct = float(bill['insurance_pct'] or 0.0) if 'insurance_pct' in bill_keys else 0.0
        insurance_amount = float(bill['insurance_amount'] or 0.0) if 'insurance_amount' in bill_keys else 0.0
        patient_amount = float(bill['patient_amount'] or 0.0) if 'patient_amount' in bill_keys else 0.0
        claim_status = (bill['insurance_claim_status'] if 'insurance_claim_status' in bill_keys else None) \
            or currency_mod.CLAIM_NOT_SUBMITTED
        has_claim = bool(insurer or member_no) and coverage_pct > 0

        # Styles
        style_title = ParagraphStyle(
            'InvTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=18,
            textColor=colors.HexColor("#1E3A8A")
        )

        style_sub = ParagraphStyle(
            'InvSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B")
        )

        style_inv_meta = ParagraphStyle(
            'InvMeta',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#0F172A")
        )

        style_meta_sub = ParagraphStyle(
            'InvMetaSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#64748B")
        )

        style_th = ParagraphStyle(
            'InvTH',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0F172A")
        )

        style_td = ParagraphStyle(
            'InvTD',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )

        style_td_right = ParagraphStyle(
            'InvTDRight',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#334155")
        )

        style_total_bold = ParagraphStyle(
            'InvTotalBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#1E3A8A")
        )

        # 1. Header: Clinic Left, Invoice Meta Right
        clinic_block = [
            Paragraph(clinic_name, style_title),
            Paragraph(clinic_address, style_sub),
            Paragraph(f"{tr('License: ')}{license_number}" if license_number else "", style_sub)
        ]

        status_text = bill['status']
        status_color = "#16A34A" if status_text == 'PAID' else "#EA580C" if status_text == 'PARTIAL' else "#DC2626"

        meta_block = [
            Paragraph(f"{tr('INVOICE #')}{bill['id']:04d}", style_inv_meta),
            Paragraph(f"{tr('Date: ')}{bill['created_at'][:10]}", style_meta_sub),
            Paragraph(f"<b>{tr('Status:')} <font color='{status_color}'>{tr(status_text)}</font></b>", style_meta_sub),
            Paragraph(f"{tr('Currency:')} {bill_code}", style_meta_sub),
        ]

        header_table = Table([[clinic_block, meta_block]], colWidths=[2.5*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4*mm))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceBefore=2, spaceAfter=8))

        # 2. Billed To
        p_name = f"{bill['first_name']} {bill['last_name']}"
        p_phone = bill['phone'] or 'N/A'
        p_addr = bill['address'] or ''

        patient_card = [
            [
                Paragraph(tr("<b>Billed To:</b>"), style_th),
                Paragraph(f"<b>{p_name}</b><br/>{tr('Phone:')} {p_phone}<br/>{p_addr}", style_td)
            ]
        ]
        p_table = Table(patient_card, colWidths=[1.0*inch, 4.0*inch])
        p_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(p_table)
        elements.append(Spacer(1, 6*mm))

        # 2b. Insurance (informational - no amount splitting)
        if insurer or member_no:
            ins_rows = [[Paragraph(f"<b>{tr('Insurance')}</b>", style_th), ""]]
            if insurer:
                ins_rows.append([Paragraph(f"<b>{tr('Provider:')}</b>", style_td),
                                 Paragraph(insurer, style_td)])
            if member_no:
                ins_rows.append([Paragraph(f"<b>{tr('Member No.:')}</b>", style_td),
                                 Paragraph(member_no, style_td)])

            ins_table = Table(ins_rows, colWidths=[1.2*inch, 3.8*inch])
            ins_table.setStyle(TableStyle([
                ('SPAN', (0, 0), (1, 0)),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BFDBFE")),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(ins_table)
            elements.append(Spacer(1, 6*mm))

        # 3. Line Items Table
        items_table_data = [
            [
                Paragraph("<b>#</b>", style_th),
                Paragraph(tr("<b>Service / Description</b>"), style_th),
                Paragraph(tr("<b>Amount</b>"), ParagraphStyle('THRight', parent=style_th, alignment=TA_RIGHT))
            ]
        ]

        subtotal = 0.0
        for i, item in enumerate(items, 1):
            amt = float(item['amount'])
            subtotal += amt
            items_table_data.append([
                Paragraph(str(i), style_td),
                Paragraph(item['description'], style_td),
                Paragraph(f"{money(amt)}", style_td_right)
            ])

        tax_amount = float(bill['tax_amount'] or 0.0)
        total_amount = float(bill['total_amount'])

        # Subtotal, Tax, Total rows
        items_table_data.append([
            "", Paragraph(tr("<b>Subtotal:</b>"), style_td_right), Paragraph(money(subtotal), style_td_right)
        ])
        if tax_amount > 0:
            items_table_data.append([
                "", Paragraph(tr("<b>Tax:</b>"), style_td_right), Paragraph(money(tax_amount), style_td_right)
            ])
        items_table_data.append([
            "", Paragraph(tr("<b>Total Due:</b>"), style_total_bold), Paragraph(f"<b>{money(total_amount)}</b>", style_total_bold)
        ])

        item_table = Table(items_table_data, colWidths=[0.4*inch, 3.4*inch, 1.2*inch])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EFF6FF")),
            ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#3B82F6")),
            ('LINEBELOW', (0,1), (-1,-4 if tax_amount > 0 else -3), 0.5, colors.HexColor("#E2E8F0")),
            ('LINEABOVE', (1,-1), (-1,-1), 1, colors.HexColor("#1E3A8A")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(item_table)

        # 3b. Insurance split - who pays what
        if has_claim:
            elements.append(Spacer(1, 5*mm))
            total_amount = float(bill['total_amount'])
            # Recompute defensively so an edited row can never print a split
            # that does not add back up to the total.
            insurance_amount, patient_amount = currency_mod.split_coverage(total_amount, coverage_pct)

            split_rows = [
                [Paragraph(f"<b>{tr('Insurance')}</b>", style_th),
                 Paragraph(f"{tr('Coverage')}: <b>{coverage_pct:g}%</b>", style_td_right)],
                [Paragraph(tr("Insurer pays"), style_td),
                 Paragraph(f"<b>{money(insurance_amount)}</b>", style_td_right)],
                [Paragraph(f"<b>{tr('Patient owes')}</b>", style_td),
                 Paragraph(f"<b>{money(patient_amount)}</b>", style_td_right)],
                [Paragraph(tr("Claim status"), style_td),
                 Paragraph(tr(currency_mod.claim_label(claim_status)), style_td_right)],
            ]
            split_table = Table(split_rows, colWidths=[3.4*inch, 1.6*inch])
            split_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BFDBFE")),
                ('LINEBELOW', (0,0), (-1,-2), 0.25, colors.HexColor("#BFDBFE")),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            elements.append(split_table)

        # 4. Notes / Payment confirmation
        if bill['notes']:
            elements.append(Spacer(1, 6*mm))
            note_block = [
                Paragraph(tr("<b>Notes / Terms:</b>"), style_th),
                Spacer(1, 2*mm),
                Paragraph(bill['notes'].replace('\n', '<br/>'), style_td)
            ]
            note_table = Table([[note_block]], colWidths=[5.0*inch])
            note_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(note_table)

        # 5. Footer & Thank you
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(tr("<i>Thank you for your visit. For inquiries, contact clinic reception.</i>"), ParagraphStyle('Thanks', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.HexColor("#64748B"))))

        doc.build(elements)
