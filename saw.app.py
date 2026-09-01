import io
import streamlit as st
from PIL import Image

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

EQUIPMENT_CONFIGS = {
    "Band Mill Carriage Track": [
        ("Vee Rail Straightness (Guide Side)", 0.015),
        ("Flat Rail Straightness (Support Side)", 0.015),
        ("Lateral Rail Parallelism Error", 0.010),
        ("Knee-to-Blade Parallelism", 0.010)
    ],
    "Endogger": [
        ("Overhead Chain Parallelism", 0.012),
        ("Dog Pin Elevation Variance", 0.010),
        ("Feed Track Runout", 0.015),
        ("Blade-to-Cradle Centerline Offset", 0.008)
    ],
    "Curve Sawing Gang": [
        ("Saw Arbor Axial Play", 0.005),
        ("Feed Roll Parallelism", 0.010),
        ("Curved Guide Slewing Tolerance", 0.012),
        ("Cant Centering Alignment", 0.010)
    ],
    "Resaw": [
        ("Feed Wheel Vertical Alignment", 0.008),
        ("Fence-to-Blade Parallelism", 0.006),
        ("Band Flywheel Tracking Alignment", 0.010),
        ("Bed Plate Levelness Deviation", 0.008)
    ],
    "Edger": [
        ("Shift Saw Arbor Alignment", 0.008),
        ("Press Roll Parallelism", 0.010),
        ("Laser Guide Offset Alignment", 0.015),
        ("Outfeed Table Levelness", 0.010)
    ],
    "Planer": [
        ("Cutterhead Parallelism to Bed", 0.004),
        ("Top Feed Roll Pressure Sync", 0.008),
        ("Side Head Spindle Squareness", 0.005),
        ("Bed Plate Wear Deviation", 0.008)
    ],
    "Chipping Canter": [
        ("Chipping Head Offset Calibration", 0.008),
        ("Infeed Spike Roll Centering", 0.012),
        ("Anvil-to-Knife Clearance", 0.006),
        ("Bottom Chain Bed Levelness", 0.010)
    ]
}

def generate_pdf_report(equipment_name, meta_data, param_data, notes, logo_bytes, photo_bytes, include_as_found):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    if logo_bytes:
        try:
            logo_img = RLImage(logo_bytes, width=180, height=60)
            logo_img.hAlign = 'LEFT'
            story.append(logo_img)
            story.append(Spacer(1, 10))
        except Exception:
            pass
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1A365D'))
    story.append(Paragraph(f"{equipment_name} Alignment Report", title_style))
    story.append(Spacer(1, 8))

    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#333333'))
    meta_text = f"<b>Report For:</b> {meta_data['report_for']}<br/>" \
                f"<b>Report By:</b> {meta_data['report_by']}<br/>" \
                f"<b>Equipment #:</b> {meta_data['equipment_num']}"
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 12))

    if photo_bytes:
        try:
            photo_img = RLImage(photo_bytes, width=450, height=240)
            story.append(photo_img)
            story.append(Spacer(1, 12))
        except Exception:
            pass

    if include_as_found:
        table_data = [["Parameter", "Target Spec", "As-Found", "Status", "As-Left", "Status"]]
        col_widths = [160, 75, 75, 65, 75, 65]
    else:
        table_data = [["Parameter", "Target Spec", "As-Left Reading", "Status"]]
        col_widths = [200, 100, 110, 100]

    table_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    row_idx = 1
    for row in param_data:
        target_str = f"≤ {row['target']:.3f}\""
        after_str = f"{row['after_val']:.3f}\""
        after_status = row['after_status']

        if include_as_found:
            before_str = f"{row['before_val']:.3f}\"" if row['before_val'] is not None else "N/A"
            before_status = row['before_status']
            table_data.append([row['label'], target_str, before_str, before_status, after_str, after_status])

            b_bg = colors.HexColor('#DCFCE7') if before_status == "PASS" else colors.HexColor('#FEE2E2')
            b_text = colors.HexColor('#166534') if before_status == "PASS" else colors.HexColor('#991B1B')
            table_styles.append(('BACKGROUND', (3, row_idx), (3, row_idx), b_bg))
            table_styles.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), b_text))
            table_styles.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))

            a_bg = colors.HexColor('#DCFCE7') if after_status == "PASS" else colors.HexColor('#FEE2E2')
            a_text = colors.HexColor('#166534') if after_status == "PASS" else colors.HexColor('#991B1B')
            table_styles.append(('BACKGROUND', (5, row_idx), (5, row_idx), a_bg))
            table_styles.append(('TEXTCOLOR', (5, row_idx), (5, row_idx), a_text))
            table_styles.append(('FONTNAME', (5, row_idx), (5, row_idx), 'Helvetica-Bold'))
        else:
            table_data.append([row['label'], target_str, after_str, after_status])
            a_bg = colors.HexColor('#DCFCE7') if after_status == "PASS" else colors.HexColor('#FEE2E2')
            a_text = colors.HexColor('#166534') if after_status == "PASS" else colors.HexColor('#991B1B')
            table_styles.append(('BACKGROUND', (3, row_idx), (3, row_idx), a_bg))
            table_styles.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), a_text))
            table_styles.append(('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold'))

        row_idx += 1

    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle(table_styles))
    story.append(t)
    story.append(Spacer(1, 14))

    story.append(Paragraph("<b>Technician Maintenance Notes:</b>", styles['Heading3']))
    story.append(Paragraph(notes, styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

st.set_page_config(page_title="Alignment Report Builder", layout="wide")

st.sidebar.title("Configuration & Branding")

uploaded_logo = st.sidebar.file_uploader("Upload Company Logo (Optional)", type=["png", "jpg", "jpeg"])
logo_bytes_io = None
if uploaded_logo is not None:
    logo_img = Image.open(uploaded_logo)
    logo_bytes_io = io.BytesIO()
    logo_img.save(logo_bytes_io, format="PNG")
    logo_bytes_io.seek(0)

selected_equipment = st.sidebar.selectbox("Select Equipment Type:", list(EQUIPMENT_CONFIGS.keys()))

include_as_found = st.sidebar.checkbox("Include As-Found (Before) Readings", value=True)

st.title("Equipment Alignment Report Builder")
st.markdown(f"Active Machine Profile: **{selected_equipment}**")

st.header("Job Details")
mc1, mc2, mc3 = st.columns(3)

with mc1:
    report_for = st.text_input("Report for", placeholder="enter company name")

with mc2:
    report_by = st.text_input("Report by", placeholder="enter your name")

with mc3:
    equipment_num = st.text_input("Equipment #", placeholder="enter equipment number")

st.markdown("---")

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.header("Equipment Photo")
    uploaded_photo = st.file_uploader("Upload Photo of Equipment (Optional)", type=["jpg", "jpeg", "png"])
    photo_bytes_io = None
    if uploaded_photo is not None:
        photo_img = Image.open(uploaded_photo)
        st.image(photo_img, caption="Equipment Field Photo", use_container_width=True)
        photo_bytes_io = io.BytesIO()
        photo_img.save(photo_bytes_io, format="JPEG")
        photo_bytes_io.seek(0)
    else:
        st.info("No photo uploaded. (Optional)")

with col2:
    st.header("Measurement Entry")
    param_list = EQUIPMENT_CONFIGS[selected_equipment]
    input_results = []

    with st.form("alignment_form"):
        for label, default_target in param_list:
            st.subheader(label)
            c1, c2, c3 = st.columns(3)
            
            with c1:
                target_val = st.number_input("Spec Limit (in)", value=default_target, step=0.001, format="%.3f", key=f"t_{label}")
            
            before_val = None
            if include_as_found:
                with c2:
                    before_val = st.number_input("As-Found", value=default_target + 0.005, step=0.001, format="%.3f", key=f"b_{label}")
                with c3:
                    after_val = st.number_input("As-Left", value=default_target - 0.002, step=0.001, format="%.3f", key=f"a_{label}")
            else:
                with c2:
                    after_val = st.number_input("As-Left Reading", value=default_target - 0.002, step=0.001, format="%.3f", key=f"a_{label}")

            input_results.append({
                "label": label,
                "target": target_val,
                "before_val": before_val,
                "after_val": after_val
            })

        notes = st.text_area("Maintenance Notes & Observations", "Routine alignment completed within tolerance specs.")
        submitted = st.form_submit_button("Generate Report & Evaluate")

if submitted:
    st.markdown("---")
    st.header("Tolerance Summary Table")

    all_after_passed = True
    for item in input_results:
        item["after_status"] = "PASS" if item["after_val"] <= item["target"] else "FAIL"
        if item["after_status"] == "FAIL":
            all_after_passed = False

        if include_as_found and item["before_val"] is not None:
            item["before_status"] = "PASS" if item["before_val"] <= item["target"] else "FAIL"

    st.markdown(f"**Report For:** {report_for if report_for else 'N/A'} | **Report By:** {report_by if report_by else 'N/A'} | **Equipment #:** {equipment_num if equipment_num else 'N/A'}")
    st.markdown("<br>", unsafe_allow_html=True)

    table_html = "<table style='width:100%; border-collapse:collapse; text-align:center; font-family:sans-serif;'>"
    table_html += "<tr style='background-color:#1A365D; color:white;'><th style='padding:10px; text-align:left;'>Parameter</th><th style='padding:10px;'>Spec Limit</th>"
    if include_as_found:
        table_html += "<th style='padding:10px;'>As-Found</th><th style='padding:10px;'>As-Found Status</th>"
    table_html += "<th style='padding:10px;'>As-Left</th><th style='padding:10px;'>As-Left Status</th></tr>"

    for item in input_results:
        after_bg = "#DCFCE7" if item["after_status"] == "PASS" else "#FEE2E2"
        after_fg = "#166534" if item["after_status"] == "PASS" else "#991B1B"
        
        table_html += f"<tr style='border-bottom:1px solid #e2e8f0;'><td style='padding:10px; text-align:left;'><b>{item['label']}</b></td><td style='padding:10px;'>≤ {item['target']:.3f}\"</td>"
        
        if include_as_found:
            before_bg = "#DCFCE7" if item["before_status"] == "PASS" else "#FEE2E2"
            before_fg = "#166534" if item["before_status"] == "PASS" else "#991B1B"
            table_html += f"<td style='padding:10px;'>{item['before_val']:.3f}\"</td><td style='padding:8px;'><span style='background-color:{before_bg}; color:{before_fg}; padding:4px 12px; border-radius:4px; font-weight:bold;'>{item['before_status']}</span></td>"
            
        table_html += f"<td style='padding:10px;'>{item['after_val']:.3f}\"</td><td style='padding:8px;'><span style='background-color:{after_bg}; color:{after_fg}; padding:4px 12px; border-radius:4px; font-weight:bold;'>{item['after_status']}</span></td></tr>"

    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if all_after_passed:
        st.success("✔ ALL AS-LEFT READINGS ARE WITHIN SPECIFICATION")
    else:
        st.error("✖ ONE OR MORE AS-LEFT READINGS EXCEED SPECIFICATION")

    meta_data = {
        "report_for": report_for if report_for else "N/A",
        "report_by": report_by if report_by else "N/A",
        "equipment_num": equipment_num if equipment_num else "N/A"
    }

    pdf_file = generate_pdf_report(
        selected_equipment,
        meta_data,
        input_results, 
        notes, 
        logo_bytes_io, 
        photo_bytes_io, 
        include_as_found
    )

    st.download_button(
        label=f"📄 Download Printable PDF Report ({selected_equipment})",
        data=pdf_file,
        file_name=f"{selected_equipment.lower().replace(' ', '_')}_alignment_report.pdf",
        mime="application/pdf"
    )
