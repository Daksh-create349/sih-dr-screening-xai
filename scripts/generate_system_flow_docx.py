import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

DOC_PATH = "/Users/dakshsrivastava/Desktop/DR /RetinaScan_AI_System_Flow_and_PS_Guide.docx"
ASSETS_DIR = "/Users/dakshsrivastava/Desktop/DR /docs/assets"
SCRATCH_DIR = "/Users/dakshsrivastava/.gemini/antigravity-ide/brain/55ce27ec-16f4-45fe-9e80-3876e1585bb8/scratch"

doc = Document()

# Page Margins: 0.8 inches all around for rich technical layout
for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Color Palette
HEX_NAVY = "0F294A"       # Primary Headings
HEX_TEAL = "0E7490"       # Secondary Accents / Subheadings
HEX_MUTED = "475569"      # Body Subdued / Captions
HEX_CARD_BG = "F0F7FF"    # Highlight Callout Fill
HEX_BORDER = "BAD7F2"     # Border Blue
HEX_WHITE = "FFFFFF"
HEX_ZEBRA = "F8FAFC"      # Alternating Table Row Fill

COLOR_NAVY = RGBColor(15, 41, 74)
COLOR_TEAL = RGBColor(14, 116, 144)
COLOR_DARK = RGBColor(17, 24, 39)
COLOR_MUTED = RGBColor(71, 85, 105)

# Helper XML styling functions
def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_callout_borders(cell, border_hex="0E7490", border_size="24"):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="single" w:sz="{border_size}" w:space="0" w:color="{border_hex}"/><w:bottom w:val="none"/><w:right w:val="none"/></w:tcBorders>')
    tcPr.append(borders)

def set_table_borders(table, border_hex="CBD5E1"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="6" w:space="0" w:color="{border_hex}"/><w:bottom w:val="single" w:sz="6" w:space="0" w:color="{border_hex}"/><w:left w:val="none"/><w:right w:val="none"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_hex}"/><w:insideV w:val="none"/></w:tblBorders>')
    tblPr.append(borders)

def add_callout(doc, text_list, title="KEY ARCHITECTURAL PRINCIPLE"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.9)
    set_cell_background(cell, HEX_CARD_BG)
    set_cell_margins(cell, top=160, bottom=160, left=220, right=200)
    set_callout_borders(cell, HEX_TEAL, "30")
    
    p0 = cell.paragraphs[0]
    p0.paragraph_format.space_before = Pt(2)
    p0.paragraph_format.space_after = Pt(4)
    r_title = p0.add_run(f"📌  {title.upper()}")
    r_title.bold = True
    r_title.font.name = "Arial"
    r_title.font.size = Pt(11)
    r_title.font.color.rgb = COLOR_TEAL
    
    for item in text_list:
        p = cell.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r_bullet = p.add_run("•  ")
        r_bullet.bold = True
        r_bullet.font.name = "Arial"
        r_bullet.font.size = Pt(10)
        r_bullet.font.color.rgb = COLOR_TEAL
        if isinstance(item, tuple):
            k, v = item
            rk = p.add_run(k + " ")
            rk.bold = True
            rk.font.name = "Arial"
            rk.font.size = Pt(10)
            rk.font.color.rgb = COLOR_NAVY
            rv = p.add_run(v)
            rv.font.name = "Arial"
            rv.font.size = Pt(10)
            rv.font.color.rgb = COLOR_DARK
        else:
            r = p.add_run(item)
            r.font.name = "Arial"
            r.font.size = Pt(10)
            r.font.color.rgb = COLOR_DARK
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def add_heading_1(doc, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(title)
    r.font.name = "Arial"
    r.font.size = Pt(16)
    r.bold = True
    r.font.color.rgb = COLOR_NAVY
    return h

def add_heading_2(doc, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(title)
    r.font.name = "Arial"
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = COLOR_TEAL
    return h

def add_heading_3(doc, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(title)
    r.font.name = "Arial"
    r.font.size = Pt(11)
    r.bold = True
    r.font.color.rgb = COLOR_DARK
    return h

def add_body_p(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + " ")
        r_pre.bold = True
        r_pre.font.name = "Arial"
        r_pre.font.size = Pt(10.5)
        r_pre.font.color.rgb = COLOR_NAVY
    r_body = p.add_run(text)
    r_body.font.name = "Arial"
    r_body.font.size = Pt(10.5)
    r_body.font.color.rgb = COLOR_DARK
    return p

def add_bullet_p(doc, bold_prefix, body_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(3.5)
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.line_spacing = 1.15
    r_dot = p.add_run("•  ")
    r_dot.bold = True
    r_dot.font.name = "Arial"
    r_dot.font.size = Pt(10)
    r_dot.font.color.rgb = COLOR_TEAL
    r_pre = p.add_run(bold_prefix + " ")
    r_pre.bold = True
    r_pre.font.name = "Arial"
    r_pre.font.size = Pt(10.5)
    r_pre.font.color.rgb = COLOR_NAVY
    r_body = p.add_run(body_text)
    r_body.font.name = "Arial"
    r_body.font.size = Pt(10.5)
    r_body.font.color.rgb = COLOR_DARK
    return p

def add_caption(doc, caption_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(10)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(caption_text)
    r.font.name = "Arial"
    r.font.size = Pt(9.5)
    r.font.italic = True
    r.font.color.rgb = COLOR_MUTED

# ==========================================
# HEADER & TITLE BLOCK
# ==========================================
p_meta_top = doc.add_paragraph()
p_meta_top.paragraph_format.space_after = Pt(2)
r_tag = p_meta_top.add_run("SMART INDIA HACKATHON 2026  |  TECHNICAL & OPERATIONAL BLUEPRINT")
r_tag.font.name = "Arial"
r_tag.font.size = Pt(9.5)
r_tag.bold = True
r_tag.font.color.rgb = COLOR_TEAL

p_main_title = doc.add_paragraph()
p_main_title.paragraph_format.space_before = Pt(2)
p_main_title.paragraph_format.space_after = Pt(4)
r_title = p_main_title.add_run("RETINASCAN-AI: End-to-End System Architecture & PS-26038 Engineering Flow Guide")
r_title.font.name = "Arial"
r_title.font.size = Pt(20)
r_title.bold = True
r_title.font.color.rgb = COLOR_NAVY

p_sub = doc.add_paragraph()
p_sub.paragraph_format.space_after = Pt(12)
r_sub = p_sub.add_run("Autonomous Optical Quality Assurance, 5-Class ICDR Staging, Dual-Level XAI & MathWorks Verified Capacity (100k Screening Mandate)")
r_sub.font.name = "Arial"
r_sub.font.size = Pt(11.5)
r_sub.font.italic = True
r_sub.font.color.rgb = COLOR_MUTED

# Project Metadata Table
meta_table = doc.add_table(rows=5, cols=2)
meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
meta_table.autofit = False
set_table_borders(meta_table)

meta_data = [
    ("Problem Statement ID & Title", "PS ID: 26038 — Explainable AI for Diabetic Retinopathy Screening in Rural India"),
    ("Partner Organization & Theme", "MathWorks India  |  MedTech / Healthcare & Biomedical Devices"),
    ("Team Name & Registered ID", "selfNprove  |  Team ID: "),
    ("Team Leader & Contact", "Daksh Srivastava (dakshshrivastav56@gmail.com)"),
    ("Engineering Team Members", "Samarth Navale, Aaryan Kuchekar, Gaurav Patel, Aaditya Bhosale, Jiya Jana")
]

col_widths = [Inches(2.5), Inches(4.4)]
for i, (k, v) in enumerate(meta_data):
    row = meta_table.rows[i]
    for c_idx, text in enumerate([k, v]):
        cell = row.cells[c_idx]
        cell.width = col_widths[c_idx]
        set_cell_margins(cell, top=90, bottom=90, left=140, right=140)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        if c_idx == 0:
            set_cell_background(cell, HEX_ZEBRA)
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(10)
            run.bold = True
            run.font.color.rgb = COLOR_NAVY
        else:
            run = p.add_run(text)
            run.font.name = "Arial"
            run.font.size = Pt(10)
            run.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(10)

# ==========================================
# SECTION 1: PROBLEM STATEMENT & CLINICAL CRISIS
# ==========================================
add_heading_1(doc, "1. Problem Statement Breakdown & The Rural India Healthcare Crisis")

add_body_p(doc, 
    "Diabetic Retinopathy (DR) is a microvascular complication of diabetes mellitus and stands as the single leading cause of preventable adult blindness in India. The epidemiological crisis in India is characterized by severe asymmetries in healthcare delivery, specialist availability, and diagnostic infrastructure:",
    "Clinical Ground Reality:")

add_bullet_p(doc, "The 77-Million Patient Burden:", "India houses over 77 million diagnosed diabetic citizens—a number projected to surpass 100 million by 2030. Approximately 1 in 5 diabetics will develop retinal microvascular complications.")
add_bullet_p(doc, "The Remote Doctor Gap (1:100,000):", "Over 70% of India's population resides in rural villages, while over 85% of certified ophthalmologists and vitreoretinal surgeons are concentrated in tier-1/tier-2 urban hospital networks. In remote Primary Health Centres (PHCs) and Community Health Centres (CHCs), the ratio of eye care specialists to diabetic citizens exceeds 1:100,000.")
add_bullet_p(doc, "The Asymptomatic Silent Threat:", "Retinal microaneurysms, hard exudate lipid leakages, and microvascular hemorrhages progress silently without causing visual blurring for 12 to 24 months. Rural farmers and daily-wage laborers present to clinics only when maculopathy or vitreous hemorrhaging has already triggered permanent, irreversible vision loss.")
add_bullet_p(doc, "The Economic Devastation of Late Referrals:", "When an undiagnosed patient finally suffers vision impairment, emergency transit to a district hospital costs INR 1,500 to INR 3,000 in travel and logistics, plus 2 to 3 days of lost daily wages. Conversely, detecting mild/moderate stages at the village PHC enables early glycemic control, laser photocoagulation, or anti-VEGF injections that prevent total blindness.")

add_heading_2(doc, "Why Existing AI Solutions Fail in Frontline Rural Practice")
add_body_p(doc, 
    "Numerous research algorithms claim high accuracy on clean benchmark datasets, yet almost zero are deployed in Indian village PHCs. There are four fatal failure modes in conventional AI approaches:")

add_bullet_p(doc, "Black-Box Clinician Distrust:", "Ophthalmologists legally and ethically refuse to accept unexplained softmax probabilities (e.g., 'DR Probability: 91%') without verifiable anatomical proof, lesion localization, and foveal clearance measurements.")
add_bullet_p(doc, "Garbage-In, Garbage-Out Degradation:", "Frontline ASHA/ANM health workers use low-cost non-mydriatic smartphone fundus attachments (e.g., Remidio, Volk iNview). Over 30% of field captures suffer from camera shake, eyelid occlusion, cataract haze, or poor focus. Unchecked standard classifiers process these blurred images and produce catastrophic false negatives.")
add_bullet_p(doc, "Total Cloud Dependency:", "Most commercial AI solutions rely on multi-gigabyte cloud APIs. Remote PHCs in tribal and rural regions operate under intermittent 2G/3G connectivity or zero cellular reception, paralyzing cloud-dependent screening.")
add_bullet_p(doc, "Binary Outputs with Zero Triage Context:", "Standard binary classifiers ('Refer' vs 'No Refer') fail to quantify whether an exudate is threatening the fovea (Clinically Significant Macular Edema) or whether the patient has 4-quadrant hemorrhages requiring urgent 48-hour hospital escalation.")

add_callout(doc, [
    ("Core Project Mission:", "RetinaScan AI replaces black-box guessing with an autonomous, mathematically verified, 100% offline-capable tele-screening workstation that enforces strict upstream optical quality gates, delivers dual-level anatomical explainability (Grad-CAM + 6 lesion U-Nets), and is verified on MathWorks Simulink for 100,000+ annual screenings.")
], "RETINASCAN-AI CORE MANDATE")

# ==========================================
# SECTION 2: 8-SUBSYSTEM ARCHITECTURAL FLOW
# ==========================================
add_heading_1(doc, "2. The 8-Subsystem Architecture & End-to-End Dataflow")

add_body_p(doc, 
    "The RetinaScan AI system is architected as an 8-subsystem sequential and feedback-governed pipeline. Each subsystem possesses formal signal invariants, strict interface boundaries, and verifiable error fallbacks:")

# Embed Architecture Flowchart Image if available
arch_flow_img = os.path.join(SCRATCH_DIR, "winner_assets", "arch_flowchart_clean.png")
if os.path.exists(arch_flow_img):
    doc.add_paragraph().paragraph_format.space_before = Pt(4)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_after = Pt(2)
    doc.add_picture(arch_flow_img, width=Inches(6.8))
    add_caption(doc, "Figure 1: RetinaScan AI 8-Subsystem Clinical Architecture Pipeline (MathWorks Simulink Verified)")

add_heading_2(doc, "Subsystem-by-Subsystem Technical Deep Dive")

# Subsystem 1
add_heading_3(doc, "Subsystem 1: Patient Retinal Ingestion & Signal Acquisition")
add_bullet_p(doc, "Acquisition Hardware:", "Engineered for 45° non-mydriatic handheld mobile fundus lenses (Volk iNview, Remidio Fundus on Phone) and standard tabletop ophthalmic cameras.")
add_bullet_p(doc, "Zero Chemical Dilation:", "Operates without pharmacological pupil dilation (tropicamide-free), eliminating patient photophobia, stinging, and the mandatory 30-minute clinic wait time.")
add_bullet_p(doc, "Payload Security & Ingestion:", "Ingests DICOM, 24-bit RGB JPEG, or lossless PNG fundus images. Strips unencrypted patient PII and assigns an encrypted ephemeral screening token with SHA-256 integrity hashing.")

# Subsystem 2
add_heading_3(doc, "Subsystem 2: Autonomous Optical Image Quality Assessment (IQA) Gatekeeper")
add_body_p(doc, "The upstream gatekeeper evaluates four objective optical criteria on the native green channel before any neural weights execute:")
add_bullet_p(doc, "Focus Score (Modified Laplacian Variance):", "Computes the variance of the second spatial derivative of pixel intensities: Score_focus = Var(Laplacian(I_green)). Detects defocus blur and operator motion tremor.")
add_bullet_p(doc, "Illumination & Entropy Score:", "Calculates Shannon Entropy and dynamic histogram range: Score_illum = -Sum(p_i * log2(p_i)). Detects underexposure (shadowed retina) and overexposure (corneal glare flash artifacts).")
add_bullet_p(doc, "Field of View (FOV) Aperture Masking:", "Computes Otsu's adaptive thresholding on the circular retina border to ensure >=85% circular retinal disc inclusion.")
add_bullet_p(doc, "Optic Disc Centering Distance:", "Measures anatomical landmark offset from the nasal/horizontal quadrant reference center.")
add_bullet_p(doc, "Three-Way Routing Protocol:", 
    "1. UNGRADEABLE (Score < 45): Classifier is strictly bypassed. Immediate audio-visual feedback is provided to the ASHA worker ('Hold camera steady', 'Re-align pupil illumination').\n"
    "2. BORDERLINE (45 <= Score <= 65): Automatically routed to Subsystem 3 for adaptive enhancement.\n"
    "3. GOOD (Score > 65): Passed directly to Subsystem 4 for deep classification.")

# Subsystem 3
add_heading_3(doc, "Subsystem 3: Adaptive Contrast Enhancement (CLAHE Engine)")
add_bullet_p(doc, "Algorithm:", "Contrast-Limited Adaptive Histogram Equalization (CLAHE) applied selectively to the green channel (where hemoglobin absorption and lipid reflectivity exhibit highest SNR).")
add_bullet_p(doc, "Parameters:", "Clip Limit: 2.0; Tile Grid Size: 8x8 pixels. Prevents noise amplification in dark peripheral zones while accentuating faint microaneurysms and deep vascular arcades.")
add_bullet_p(doc, "Post-Enhancement Quality Re-Audit:", "The enhanced frame undergoes a mandatory second IQA verification. If the enhanced score crosses 65, it is approved for classifier inference; if it fails, it is aborted to prevent hallucinatory neural outputs.")

# Subsystem 4
add_heading_3(doc, "Subsystem 4: Deep Severity Classifier (5-Class ICDR Staging)")
add_bullet_p(doc, "Neural Architecture:", "EfficientNetB3 backbone with compound scaling (depth, width, resolution), accepting 384x384 input tensors. Lightweight with only 12.2M parameters.")
add_bullet_p(doc, "Validation Performance:", "Achieves 81.15% 5-class validation accuracy and a Quadratic Weighted Kappa (QWK) score of 0.842 across multi-center clinical cohorts.")
add_bullet_p(doc, "Cryptographically Frozen Checkpoint:", "Model weights are signed and frozen (dr_classifier_frozen.pt) to guarantee zero post-deployment drift in clinical settings.")
add_bullet_p(doc, "International Clinical DR (ICDR) Grading Scale:",
    "• Grade 0 (No DR): Normal retinal fundus; zero microaneurysms or hemorrhages.\n"
    "• Grade 1 (Mild NPDR): Presence of microaneurysms only.\n"
    "• Grade 2 (Moderate NPDR): More than just microaneurysms, but less than Severe NPDR (scattered exudates and flame hemorrhages).\n"
    "• Grade 3 (Severe NPDR): Meets the '4-2-1 rule' (>20 intraretinal hemorrhages in each of 4 quadrants, definite venous beading in 2+ quadrants, prominent IRMA in 1+ quadrant).\n"
    "• Grade 4 (Proliferative DR - PDR): Pathological neovascularization of the disc/retina, preretinal or vitreous hemorrhage.")

# Subsystem 5
add_heading_3(doc, "Subsystem 5: High-Sensitivity Referable Triage Gate")
add_bullet_p(doc, "Clinical Triage Mandate:", "Distinguishes between Non-Referable DR (Grades 0–1, manageable via PHC lifestyle and annual checkups) and Referable DR (Grades 2–4, requiring urgent specialist referral).")
add_bullet_p(doc, "Dual-Threshold Calibration:",
    "• Standard Balanced Operating Point (t = 0.33): Sensitivity = 89.78%, Specificity = 86.40%.\n"
    "• Rural Calibrated High-Sensitivity Point (t = 0.1181): Sensitivity = 99.27%, False Negative Rate = 0.73% (<1 in 135 cases missed). This ensures zero proliferative vision-threatening DR cases slip past the frontline screening gate.")

# Subsystem 6
add_heading_3(doc, "Subsystem 6: Dual-Level Explainable AI (XAI) & 6-System Deep Biomarker Engine")
add_body_p(doc, "To provide complete diagnostic trust to ophthalmologists, Subsystem 6 generates two complementary layers of explainability:")

add_bullet_p(doc, "Level A — Macroscopic Attribution (Grad-CAM):", 
    "Gradient-weighted Class Activation Mapping backpropagated to the top_conv layer of EfficientNetB3. Generates a 384x384 continuous activation heatmap highlighting the anatomical sectors driving the severity decision, mapped across a standardized 9-sector grid (Superior-Temporal, Superior-Nasal, Posterior Pole, etc.).")

add_bullet_p(doc, "Level B — Microscopic Lesion Segmentation (4x PyTorch ResNet34 U-Nets):",
    "1. Optic Disc U-Net (Dice: 0.9859): Segments the anatomical disc anchor to establish spatial coordinate reference.\n"
    "2. Hard Exudates U-Net (Dice: 0.7580): Isolates lipid deposits and computes total lesion surface area.\n"
    "3. Retinal Hemorrhages U-Net (Dice: 0.7482): Maps flame, dot, and blot hemorrhages across quadrants.\n"
    "4. Soft Exudates / Cotton Wool U-Net (Dice: 0.7595): Segments nerve fiber layer micro-infarcts.")

add_bullet_p(doc, "Level C — Classical Computer Vision Biomarkers:",
    "5. Retinal Microvasculature Tree: Multiscale Frangi Hessian vesselness filter (sigma in [1.0, 2.0]) isolating vessel caliber, arteriolar narrowing, and neovascular loops.\n"
    "6. Pinpoint Microaneurysms: Inverted green-channel Top-Hat mathematical morphological filter isolating 2–45 px microaneurysms.")

add_bullet_p(doc, "Spatial Geometry — CSME Foveal Threat Clearance:",
    "Clinically Significant Macular Edema (CSME) is automatically evaluated by measuring the Euclidean distance between detected hard exudates and the center of the fovea. Any lipid deposits located < 1 disc diameter (DD) from the fovea center trigger an immediate 'HIGH CSME BLINDNESS THREAT' clinical flag.")

# Subsystem 7
add_heading_3(doc, "Subsystem 7: Frontline PACS Workstation & Instant Report Compiler")
add_bullet_p(doc, "Diagnostic Workstation UI:", "Responsive web-based PACS console (Next.js 14 / React) featuring real-time image quality inspection, 5-class probability meters, and interactive multi-layer lesion toggle switches.")
add_bullet_p(doc, "Zero-Latency In-Browser PDF Exporter:", "Generates a clean, hospital-grade vector PDF screening referral report in <500ms containing patient demographics, color-coded IQA stamp, severity distribution, high-res multi-modal overlay, quantitative lesion counts, and doctor sign-off blocks.")

# Subsystem 8
add_heading_3(doc, "Subsystem 8: Offline-First Rural Health Node Queue & Tele-Consultation Handoff")
add_bullet_p(doc, "100% Offline Edge Processing:", "Executes entirely on local field laptops or $100 embedded edge SBCs (Jetson Orin Nano, Raspberry Pi 5) without active internet.")
add_bullet_p(doc, "Store-and-Forward Sync:", "All patient screening records, encrypted vector PDFs, and diagnostic payloads are persisted locally in SQLite/encrypted storage. When cellular connectivity or Wi-Fi is detected during village-to-city transit, records automatically synchronize to the District Eye Hospital central server via FHIR HL7 compliant endpoints.")

# Embed Modalities Quad Panel
quad_img = os.path.join(ASSETS_DIR, "clinical_modalities_quad_panel.png")
if os.path.exists(quad_img):
    doc.add_paragraph().paragraph_format.space_before = Pt(4)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_after = Pt(2)
    doc.add_picture(quad_img, width=Inches(6.8))
    add_caption(doc, "Figure 2: Multi-Modal Clinical Inference Quad-Panel — (A) 45° Color Fundus, (B) Frangi Retinal Angiogram, (C) 6-System Deep Lesion Overlay, (D) Grad-CAM Attribution Heatmap")

# ==========================================
# SECTION 3: MATHWORKS SIMULINK VERIFICATION
# ==========================================
add_heading_1(doc, "3. MathWorks Simulink Modeling & Discrete-Event Capacity Proof")

add_body_p(doc, 
    "A cornerstone of RetinaScan AI is its formal modeling, signal validation, and queueing verification using MathWorks Simulink (model file: DR_screening_workflow.slx). Rather than treating edge deployment as an untested assumption, the entire screening throughput was mathematically verified against national rural deployment mandates:")

# Embed Simulink Model Screenshot
sim_img = os.path.join(ASSETS_DIR, "simulink_model_screenshot.png")
if os.path.exists(sim_img):
    doc.add_paragraph().paragraph_format.space_before = Pt(4)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_after = Pt(2)
    doc.add_picture(sim_img, width=Inches(6.8))
    add_caption(doc, "Figure 3: MathWorks Simulink Discrete-Event Screening Architecture (DR_screening_workflow.slx)")

add_heading_2(doc, "Discrete-Event M/M/1 Queuing Model & Throughput Proof")
add_body_p(doc, "The operational capacity was modeled using discrete-event queuing theory (SimEvents / SimBiology principles):")

add_bullet_p(doc, "Mandated Rural Target (Arrival Rate lambda):", 
    "The national screening target mandates screening 100,000 rural diabetic patients per year per operational cluster.\n"
    "lambda = 100,000 patients / year = 0.00317 patients/second (across 24/7 basis) or 0.0137 patients/second (across standard 8-hour field clinic shifts).")

add_bullet_p(doc, "Empirical Edge Service Time (Ts):",
    "Across the 8 subsystems (IQA + CLAHE + EfficientNetB3 + 4x U-Nets + Grad-CAM + Report Generation), the mean edge execution time is:\n"
    "Mean Service Time (Ts) = 1.22 seconds.\n"
    "Service Rate (mu) = 1 / Ts = 1 / 1.22 s = 0.8197 screenings/second.")

add_bullet_p(doc, "Annualized System Throughput Capacity:",
    "At 0.8197 screenings/second, a single standard field workstation possesses an annual processing capacity of:\n"
    "Capacity = 0.8197 * 3,600 s/hr * 2,000 working hrs/year = 5,901,840 screenings / year (~5.9 Million screenings/year).\n"
    "Safety Margin: 5,901,840 / 100,000 = 58x Margin of Safety over the mandated 100k quota.")

add_bullet_p(doc, "System Utilization (rho) & Queue Stability:",
    "Traffic Intensity rho = lambda / mu = 0.0137 / 0.8197 = 0.0167 (rho << 1.0).\n"
    "Under steady-state M/M/1 queuing dynamics, the mean waiting queue length Lq is:\n"
    "Lq = rho^2 / (1 - rho) = (0.0167)^2 / (1 - 0.0167) = 0.00028 patients in queue.\n"
    "Conclusion: The system exhibits ZERO queue buildup, near-instantaneous response times, and immune resilience against field clinic traffic surges.")

add_heading_2(doc, "Edge Hardware Performance Profiles")

hw_table = doc.add_table(rows=4, cols=4)
hw_table.alignment = WD_TABLE_ALIGNMENT.CENTER
hw_table.autofit = False
set_table_borders(hw_table)

hw_headers = ["Target Hardware Platform", "Inference Latency (Ts)", "RAM Footprint", "Field Viability / Power"]
for c_idx, title in enumerate(hw_headers):
    cell = hw_table.rows[0].cells[c_idx]
    set_cell_background(cell, HEX_NAVY)
    set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
    p = cell.paragraphs[0]
    r = p.add_run(title)
    r.font.name = "Arial"
    r.font.size = Pt(9.5)
    r.bold = True
    r.font.color.rgb = RGBColor(255, 255, 255)

hw_rows = [
    ("NVIDIA Jetson Orin Nano (TensorRT INT8)", "680 ms / patient", "1.4 GB RAM", "7W–15W (Solar / Van Battery Compatible)"),
    ("Standard Clinical Laptop (Intel Core i5, ONNX)", "1.10 s / patient", "1.8 GB RAM", "Standard 45W Charger (Frontline PHC)"),
    ("Raspberry Pi 5 (4GB RAM, Quantized TFLite)", "2.40 s / patient", "1.1 GB RAM", "5V / 5A USB-C (Mobile Backpack Kit)")
]

col_w_hw = [Inches(2.3), Inches(1.4), Inches(1.2), Inches(2.0)]
for r_idx, row_data in enumerate(hw_rows):
    row = hw_table.rows[r_idx + 1]
    bg = HEX_ZEBRA if r_idx % 2 == 1 else HEX_WHITE
    for c_idx, val in enumerate(row_data):
        cell = row.cells[c_idx]
        cell.width = col_w_hw[c_idx]
        set_cell_background(cell, bg)
        set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
        p = cell.paragraphs[0]
        r = p.add_run(val)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        if c_idx == 0:
            r.bold = True
            r.font.color.rgb = COLOR_NAVY
        elif c_idx == 1:
            r.bold = True
            r.font.color.rgb = COLOR_TEAL
        else:
            r.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(8)

# ==========================================
# SECTION 4: COMPLETE STEP-BY-STEP DATAFLOW TABLE
# ==========================================
add_heading_1(doc, "4. Complete Step-by-Step Dataflow & Signal Routing Matrix")

add_body_p(doc, 
    "This matrix tracks the life-cycle of a single patient fundus image from initial optical capture to final signed clinical PDF export:")

flow_matrix_data = [
    ("1", "Patient Retinal Ingestion", "Raw 45° Fundus Capture (DICOM / JPEG / PNG)", "24-bit RGB decoding, PII scrubbing, SHA-256 session token generation", "Clean 3-channel RGB image tensor (100% anonymized)"),
    ("2", "Autonomous IQA Gatekeeper", "Green channel of raw image tensor", "Laplacian Var (Focus) + Entropy (Illum) + Circular Mask (FOV) + Centering", "Score <45: Interlock Recapture\nScore 45–65: Route SS-3\nScore >65: Route SS-4"),
    ("3", "Adaptive CLAHE Enhancer", "Borderline image (45 <= Score <= 65)", "Contrast-Limited Adaptive Hist Eq (Clip: 2.0, Grid: 8x8) on Green channel", "Enhanced RGB image; re-audited by IQA before classifier admission"),
    ("4", "Deep ICDR Classifier", "Passed/Enhanced image (Resized to 384x384)", "EfficientNetB3 forward pass (Frozen cryptographically verified weights)", "5-class softmax vector: [P0, P1, P2, P3, P4] (81.15% Val Acc)"),
    ("5", "Referable Triage Gate", "Softmax vector [P0..P4]", "Binary risk aggregation (P_ref = Sum(P2..P4)); calibrated threshold t=0.1181", "Referable Flag (YES/NO); 99.27% rural sensitivity (<1 in 135 missed)"),
    ("6A", "Macroscopic XAI (Grad-CAM)", "top_conv layer gradients + predicted class", "Grad-CAM backpropagation, bicubic upscaling to 384x384, jet colormap", "Attribution heatmap mapped across 9 anatomical grid sectors"),
    ("6B", "Deep Biomarker Segmentation", "Raw image tensor (Preprocessed)", "4x PyTorch ResNet34 U-Nets + Frangi filter + Top-Hat morphology", "Pixel binary masks for Optic Disc, Exudates, Hemorrhages, Vessels, MAs"),
    ("7", "Frontline PACS Console & PDF", "All inference masks + Softmax vector + IQA metrics", "Browser vector PDF compilation, CSME spatial calculation, Doctor block", "Interactive PACS UI + Signed clinical referral PDF report (<500ms)"),
    ("8", "Offline Queue & Sync", "Encrypted PDF payload + Structured JSON report", "Local SQLite queue storage; Store-and-Forward cellular auto-sync", "Offline persistence; automatic background sync to District Hospital PACS")
]

flow_table = doc.add_table(rows=len(flow_matrix_data) + 1, cols=5)
flow_table.alignment = WD_TABLE_ALIGNMENT.CENTER
flow_table.autofit = False
set_table_borders(flow_table)

flow_headers = ["Step #", "Subsystem & Component", "Input Data", "Algorithmic Mechanism", "Output Payload & Fail-Safe"]
flow_widths = [Inches(0.6), Inches(1.6), Inches(1.3), Inches(1.8), Inches(1.6)]

for c_idx, title in enumerate(flow_headers):
    cell = flow_table.rows[0].cells[c_idx]
    cell.width = flow_widths[c_idx]
    set_cell_background(cell, HEX_NAVY)
    set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
    p = cell.paragraphs[0]
    r = p.add_run(title)
    r.font.name = "Arial"
    r.font.size = Pt(9)
    r.bold = True
    r.font.color.rgb = RGBColor(255, 255, 255)

for r_idx, row_data in enumerate(flow_matrix_data):
    row = flow_table.rows[r_idx + 1]
    bg = HEX_ZEBRA if r_idx % 2 == 1 else HEX_WHITE
    for c_idx, val in enumerate(row_data):
        cell = row.cells[c_idx]
        cell.width = flow_widths[c_idx]
        set_cell_background(cell, bg)
        set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
        p = cell.paragraphs[0]
        r = p.add_run(val)
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        if c_idx == 0:
            r.bold = True
            r.font.color.rgb = COLOR_TEAL
        elif c_idx == 1:
            r.bold = True
            r.font.color.rgb = COLOR_NAVY
        else:
            r.font.color.rgb = COLOR_DARK

doc.add_paragraph().paragraph_format.space_after = Pt(8)

# ==========================================
# SECTION 5: TECH STACK & REPOSITORY MAPPING
# ==========================================
add_heading_1(doc, "5. Technology Stack & Codebase Module Directory Mapping")

add_body_p(doc, 
    "The implementation is structured into clean decoupled modules following strict clinical software standards:")

tech_items = [
    ("Deep Learning Framework:", "PyTorch 2.2 & Keras / TensorFlow for U-Net lesion segmentation and EfficientNetB3 backbone."),
    ("Classical Computer Vision:", "OpenCV 4.9, SciPy, and Scikit-Image for Laplacian focus, Shannon entropy, Frangi Hessian filters, and Top-Hat morphological kernels."),
    ("Edge Inference Engine:", "FastAPI production asynchronous daemon (Python 3.10) with ONNX Runtime and TensorRT INT8 optimization."),
    ("Frontline Clinical Workstation:", "Next.js 14, React, HTML5 Canvas API for real-time vector lesion toggles, and Lucide icons."),
    ("Systems Simulation & Modeling:", "MathWorks MATLAB / Simulink R2024b (DR_screening_workflow.slx) for discrete-event capacity validation."),
    ("Deployment & Containerization:", "Docker, Docker Compose, systemd edge daemons for offline field laptops and NVIDIA Jetson hardware.")
]

for k, v in tech_items:
    add_bullet_p(doc, k, v)

add_heading_2(doc, "Repository Architecture & Key Files")

repo_structure = [
    ("simulink/models/DR_screening_workflow.slx", "Official MathWorks Simulink 8-subsystem verified model file (Tracked via Git LFS)."),
    ("backend/app/main.py", "FastAPI production REST API handling multi-part image ingestion and JSON responses."),
    ("backend/app/core/classifier.py", "EfficientNetB3 inference wrapper with cryptographically frozen weights and 5-class output."),
    ("backend/app/core/iqa_gatekeeper.py", "4-metric Image Quality Assessment engine (Laplacian, Entropy, FOV, Centering)."),
    ("backend/app/core/biomarkers.py", "4x U-Net lesion segmentation engines, Frangi vesselness, and Top-Hat microaneurysm filters."),
    ("backend/app/core/explainability.py", "Grad-CAM feature attribution generator mapped across the 9-sector anatomical coordinate grid."),
    ("frontend/src/components/Workstation.tsx", "Next.js 14 PACS clinical interface with real-time lesion overlay toggles."),
    ("docs/CLINICAL_ACQUISITION_AND_SYSTEM_GUIDE.md", "Comprehensive clinical acquisition manual and hackathon pitch guide.")
]

for file_path, desc in repo_structure:
    add_bullet_p(doc, file_path + " :", desc)

# ==========================================
# SECTION 6: TEAM ROLES & WINNING PITCH STRATEGY
# ==========================================
add_heading_1(doc, "6. Team Execution Roles, Pitch Strategy & Common Judge Q&A")

add_body_p(doc, 
    "To maximize scoring during the SIH 2026 jury evaluation, each team member has dedicated ownership across the presentation flow:")

team_roles = [
    ("Daksh Srivastava (Team Leader):", "Lead Presenter. Opens the pitch with the rural crisis, explains the 8-subsystem architecture, details the MathWorks Simulink M/M/1 capacity verification, and delivers the closing user story."),
    ("Samarth Navale (Deep Learning Lead):", "Presents Subsystem 4 (EfficientNetB3 5-class classifier, 81.15% validation accuracy, QWK 0.842) and benchmark training on IDRiD/APTOS cohorts."),
    ("Aaryan Kuchekar (XAI & Biomarker Lead):", "Presents Subsystem 6 (Dual explainability, Grad-CAM 9-sector attribution, 4x ResNet34 U-Nets, and CSME foveal threat distance geometry)."),
    ("Gaurav Patel (Systems & Edge Lead):", "Presents Subsystems 1 & 2 (Hardware safety interlock, 4-metric IQA gatekeeper, CLAHE contrast feedback, and Jetson/RPi5 INT8 edge latency)."),
    ("Aaditya Bhosale (Backend & Storage Lead):", "Presents Subsystem 8 (Offline-first architecture, AES-256 local encryption, store-and-forward sync to central hospital PACS, and FHIR HL7 compliance)."),
    ("Jiya Jana (Clinical UI/UX Lead):", "Demonstrates Subsystem 7 (Live Frontline PACS Workstation, real-time multi-lesion toggle switches, and in-browser instant signed vector PDF generation).")
]

for member, role in team_roles:
    add_bullet_p(doc, member, role)

add_heading_2(doc, "Anticipated Judge Questions & Winning Strategic Responses")

judge_qa = [
    ("Q1: Why did you model this in MathWorks Simulink instead of just writing Python code?",
     "Answer: Python provides model weights, but Simulink provides formal systems engineering verification. By building the discrete-event M/M/1 model in Simulink (DR_screening_workflow.slx), we proved that the 8-subsystem pipeline can handle 5.9M screenings/year with a 58x safety margin over the government's 100k mandate. Furthermore, Simulink allowed us to formally verify the safety bypass interlock so degraded images can never reach neural inference."),
    
    ("Q2: Why not just use a modern Vision Transformer or end-to-end black box CNN?",
     "Answer: In medical diagnostics, a black-box probability is legally and clinically un-actionable. Ophthalmologists reject AI predictions without visible evidence. RetinaScan AI uses dual-level XAI: macroscopic Grad-CAM heatmaps showing which anatomical sector drove the decision, plus microscopic U-Nets segmenting actual exudates and hemorrhages. Furthermore, EfficientNetB3 runs in 680ms on $100 edge hardware, whereas large transformers require expensive GPUs unfeasible for rural PHCs."),
    
    ("Q3: What happens when an ASHA worker captures a blurred or poorly illuminated photo?",
     "Answer: Unlike conventional systems that hallucinate false predictions on blurry photos, our Subsystem 2 Optical IQA Gatekeeper evaluates Laplacian focus, Shannon entropy, FOV aperture, and centering before neural inference. If score <45, inference is strictly halted and the worker receives instant audio-visual guidance on how to re-take the photo."),
    
    ("Q4: How do you achieve 99.27% sensitivity without causing massive false alarms?",
     "Answer: We employ a dual-threshold strategy. For general telemedicine, we use standard threshold t = 0.33. For frontline rural triage where missing a vision-threatening case causes irreversible blindness, we calibrate to t = 0.1181. This yields 99.27% sensitivity on referable DR (<1 in 135 missed cases), while our upstream IQA gate and downstream lesion segmentation prevent non-DR cases from triggering false referrals."),
    
    ("Q5: How does the system work in remote tribal areas with zero internet connectivity?",
     "Answer: RetinaScan AI is 100% offline-first. The entire pipeline (IQA, ONNX-quantized classifier, U-Nets, and PDF compiler) runs locally on a battery-powered field laptop or Jetson Orin Nano. Results and signed PDFs are generated instantly in the village. Data is queued in local encrypted storage and automatically synchronizes to the District Hospital when cellular or Wi-Fi connectivity is re-established.")
]

for q, a in judge_qa:
    add_bullet_p(doc, q, a)

# Footer Note
doc.add_paragraph().paragraph_format.space_before = Pt(14)
p_end = doc.add_paragraph()
p_end.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_end = p_end.add_run("— END OF RETINASCAN-AI TECHNICAL & OPERATIONAL BLUEPRINT —")
r_end.font.name = "Arial"
r_end.font.size = Pt(10)
r_end.bold = True
r_end.font.color.rgb = COLOR_TEAL

doc.save(DOC_PATH)
print("SUCCESS: Document generated at:", DOC_PATH)
