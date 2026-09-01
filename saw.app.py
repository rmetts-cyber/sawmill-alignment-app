import os
import io
import json
import streamlit as st
from PIL import Image
from pypdf import PdfMerger

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

CONFIG_FILE = "equipment_config.json"

# -----------------------------------------------------------------------------
# 1. Configuration Storage & JSON Persistence Engine
# -----------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "Band Mill Carriage Track": [
        {"label": "Vee Rail Straightness (Guide Side)", "target": 0.015},
        {"label": "Flat Rail Straightness (Support Side)", "target": 0.015},
        {"label": "Lateral Rail Parallelism Error", "target": 0.010},
        {"label": "Knee-to-Blade Parallelism", "target": 0.010}
    ],
    "Endogger": [
        {"label": "Overhead Chain Parallelism", "target": 0.012},
        {"label": "Dog Pin Elevation Variance", "target": 0.010},
        {"label": "Feed Track Runout", "target": 0.015},
        {"label": "Blade-to-Cradle Centerline Offset", "target": 0.008}
    ]
}

def load_config():
    """Loads equipment parameters from local JSON file or initializes defaults."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_CONFIG.copy()
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    """Saves updated equipment configurations permanently to JSON."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

# -----------------------------------------------------------------------------
# 2. PDF Report Generator & PDF Merger
# -----------------------------------------------------------------------------
def generate_pdf_report(equipment_name, param_data, notes, logo_bytes, photo_bytes, include_as_found):
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
    story.append(Spacer(1, 10))

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

            a_bg = colors.HexColor('#DCFCE7') if after_status == "PASS" else colors.HexColor('#FEE2E2')
            a_text = colors.HexColor('#166534') if after_status == "PASS" else colors.HexColor('#991B1B')
            table_styles.append(('BACKGROUND', (5, row_idx), (5, row_idx), a_bg))
            table_styles.append(('TEXTCOLOR', (5, row_idx), (5, row_idx), a_text))
        else:
            table_data.append([row['label'], target_str, after_str, after_status])
            a_bg = colors.HexColor('#DCFCE7') if after_status == "PASS" else colors.HexColor('#FEE2E2')
            a_text = colors.HexColor('#166534') if after_status == "PASS" else colors.HexColor('#991B1B')
            table_styles.append(('BACKGROUND', (3, row_idx), (3, row_idx), a_bg))
            table_styles.append(('TEXTCOLOR', (3, row_idx), (3, row_idx), a_text))

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

def merge_pdf_files(pdf_file_list):
    merger = PdfMerger()
    for pdf in pdf_file_list:
        merger.append(pdf)
    merged_buffer = io.BytesIO()
    merger.write(merged_buffer)
    merger.close()
    merged_buffer.seek(0)
    return merged_buffer

# -----------------------------------------------------------------------------
# 3. Streamlit Interface
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Alignment Report Builder", layout="wide")

# Load persistent configurations
equipment_configs = load_config()

st.sidebar.title("Branding & Options")

# Company Logo Upload
uploaded_logo = st.sidebar.file_uploader("Upload Company Logo (Optional)", type=["png", "jpg", "jpeg"])
logo_bytes_io = None
if uploaded_logo is not None:
    logo_img = Image.open(uploaded_logo)
    logo_bytes_io = io.BytesIO()
    logo_img.save(logo_bytes_io, format="PNG")
    logo_bytes_io.seek(0)

# Main Navigation Tabs
tab_report, tab_editor, tab_merger = st.tabs(["📝 Build Report", "⚙️ Manage Machines & Specs", "📑 Merge PDFs"])

# -----------------------------------------------------------------------------
# TAB 1: REPORT BUILDER
# -----------------------------------------------------------------------------
with tab_report:
    st.sidebar.title("Machine Selection")
    selected_equipment = st.sidebar.selectbox("Select Equipment Type:", list(equipment_configs.keys()))
    include_as_found = st.sidebar.checkbox("Include As-Found (Before) Readings", value=True)

    st.title("Equipment Alignment Report Builder")
    st.markdown(f"Active Machine Profile: **{selected_equipment}**")

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.header("1. Equipment Photo")
        uploaded_photo = st.file_uploader("Upload Equipment Photo (Optional)", type=["jpg", "jpeg", "png"])
        photo_bytes_io = None
        if uploaded_photo is not None:
            photo_img = Image.open(uploaded_photo)
            st.image(photo_img, caption="Equipment Field Photo", use_container_width=True)
            photo_bytes_io = io.BytesIO()
            photo_img.save(photo_bytes_io, format="JPEG")
            photo_bytes_io.seek(0)

    with col2:
        st.header("2. Measurement Entry")
        param_list = equipment_configs[selected_equipment]
        input_results = []

        with st.form("alignment_form"):
            for item in param_list:
                label = item["label"]
                default_target = item["target"]
                
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
        st.header("3. Tolerance Summary Table")

        all_after_passed = True
        for item in input_results:
            item["after_status"] = "PASS" if item["after_val"] <= item["target"] else "FAIL"
            if item["after_status"] == "FAIL":
                all_after_passed = False

            if include_as_found and item["before_val"] is not None:
                item["before_status"] = "PASS" if item["before_val"] <= item["target"] else "FAIL"

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

        pdf_file = generate_pdf_report(selected_equipment, input_results, notes, logo_bytes_io, photo_bytes_io, include_as_found)

        st.download_button(
            label=f"📄 Download Printable PDF Report ({selected_equipment})",
            data=pdf_file,
            file_name=f"{selected_equipment.lower().replace(' ', '_')}_alignment_report.pdf",
            mime="application/pdf"
        )

# -----------------------------------------------------------------------------
# TAB 2: MANAGEMENT & CONFIGURATION EDITOR
# -----------------------------------------------------------------------------
with tab_editor:
    st.header("Equipment & Measurement Editor")
    st.write("Add new machinery, modify baseline specs, or edit/delete measurement rows permanently.")

    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        st.subheader("1. Select Machine Profile to Edit")
        edit_target = st.selectbox("Machine Profile:", list(equipment_configs.keys()), key="edit_target_select")
        
        # Add New Machine Section
        new_machine_name = st.text_input("Or Create New Machine Profile Name:")
        if st.button("➕ Add New Machine Profile"):
            if new_machine_name and new_machine_name not in equipment_configs:
                equipment_configs[new_machine_name] = [
                    {"label": "General Parallelism", "target": 0.010}
                ]
                save_config(equipment_configs)
                st.success(f"Added profile '{new_machine_name}'!")
                st.rerun()

        # Delete Machine Profile
        if st.button(f"🗑️ Delete Profile '{edit_target}'", type="primary"):
            if len(equipment_configs) > 1:
                del equipment_configs[edit_target]
                save_config(equipment_configs)
                st.success(f"Deleted '{edit_target}'.")
                st.rerun()
            else:
                st.error("Cannot delete the last remaining equipment profile!")

    with col_b:
        st.subheader(f"2. Edit Measurements for '{edit_target}'")
        current_params = equipment_configs[edit_target]
        updated_params = []

        with st.form(f"edit_form_{edit_target}"):
            for idx, item in enumerate(current_params):
                st.markdown(f"**Measurement Point #{idx+1}**")
                c1, c2, c3 = st.columns([3, 2, 1])
                
                with c1:
                    new_label = st.text_input("Parameter Description", value=item["label"], key=f"lbl_{edit_target}_{idx}")
                with c2:
                    new_target = st.number_input("Default Spec Limit (in)", value=float(item["target"]), step=0.001, format="%.3f", key=f"tgt_{edit_target}_{idx}")
                with c3:
                    delete_row = st.checkbox("Delete", key=f"del_{edit_target}_{idx}")

                if not delete_row:
                    updated_params.append({"label": new_label, "target": new_target})

            st.markdown("---")
            st.markdown("**Add Additional Measurement Row:**")
            add_c1, add_c2 = st.columns([3, 2])
            with add_c1:
                add_label = st.text_input("New Parameter Label", placeholder="e.g. Bed Levelness Error", key=f"add_lbl_{edit_target}")
            with add_c2:
                add_target = st.number_input("New Spec Limit (in)", value=0.010, step=0.001, format="%.3f", key=f"add_tgt_{edit_target}")

            if add_label:
                updated_params.append({"label": add_label, "target": add_target})

            save_changes = st.form_submit_button("💾 Save Changes to Configuration")

        if save_changes:
            equipment_configs[edit_target] = updated_params
            save_config(equipment_configs)
            st.success("Configuration saved permanently!")
            st.rerun()

# -----------------------------------------------------------------------------
# TAB 3: PDF MERGER
# -----------------------------------------------------------------------------
with tab_merger:
    st.header("Merge Multiple Equipment Reports")
    st.write("Upload individual PDF reports to compile them into a single deliverable package for your customer.")

    uploaded_pdfs = st.file_uploader(
        "Upload PDF Reports", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="pdf_merger_tab"
    )

    if uploaded_pdfs:
        st.write(f"**Selected Reports ({len(uploaded_pdfs)}):**")
        for pdf in uploaded_pdfs:
            st.caption(f"• {pdf.name}")

        merged_pdf_name = st.text_input("Combined File Name", value="Complete_Sawmill_Alignment_Audit.pdf")

        if st.button("Merge PDFs into Single Package"):
            merged_file = merge_pdf_files(uploaded_pdfs)
            st.success("✔ PDFs Merged Successfully!")
            st.download_button(
                label="📥 Download Combined Report Package",
                data=merged_file,
                file_name=merged_pdf_name,
                mime="application/pdf"
            )
