import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

BASE_PPTX = "/Users/dakshsrivastava/Desktop/DR /SIH2026-IDEA-Presentation-Format.backup.pptx"
OUT_PPTX = "/Users/dakshsrivastava/Desktop/DR /SIH2026-IDEA-Presentation-Format.pptx"
SCRATCH_DIR = "/Users/dakshsrivastava/.gemini/antigravity-ide/brain/55ce27ec-16f4-45fe-9e80-3876e1585bb8/scratch"
ASSETS_DIR = os.path.join(SCRATCH_DIR, "winner_assets")
TECH_DIR = os.path.join(SCRATCH_DIR, "tech_logos")

prs = Presentation(BASE_PPTX)

# Palette
C_NAVY = RGBColor(15, 41, 74)          # #0F294A
C_TAB_BLUE = RGBColor(11, 79, 138)     # #0B4F8A
C_CARD_BG = RGBColor(248, 250, 252)    # #F8FAFC
C_ICE_BLUE = RGBColor(240, 247, 255)   # #F0F7FF
C_BORDER_BLUE = RGBColor(186, 215, 242)# #BAD7F2
C_BORDER_GRAY = RGBColor(203, 213, 225)# #CBD5E1
C_TEXT_DARK = RGBColor(17, 24, 39)     # #111827
C_TEXT_MUTED = RGBColor(55, 65, 81)    # #374151
C_WHITE = RGBColor(255, 255, 255)
C_LINK_BLUE = RGBColor(30, 64, 175)    # #1E40AF
C_EMERALD = RGBColor(5, 150, 105)      # #059669

# ==========================================
# SLIDE 1: COVER SLIDE POLISH
# ==========================================
s1 = prs.slides[0]
for sh in list(s1.shapes):
    if sh.name == "Rectangle 24":
        # Remove the giant rectangle that PowerPoint erroneously fills with accent1 blue
        sp = sh._element
        sp.getparent().remove(sp)
    elif sh.name == "TextBox 9":
        for p in sh.text_frame.paragraphs:
            if "Team Name:" in p.text:
                for r in p.runs:
                    if "RetinaScan AI" in r.text:
                        r.text = r.text.replace("RetinaScan AI", "selfNprove")
            if "Team Leader:" in p.text:
                for r in p.runs:
                    if "daksh.srivastava@email.com" in r.text or "dakshshrivastav56@gmail.com" in r.text:
                        r.text = r.text.replace("daksh.srivastava@email.com", "dakshshrivastav56@gmail.com")
            if "Registered Team ID:" in p.text:
                for r in p.runs:
                    r.text = r.text.replace("27113", "").replace("[Your Team ID]", "")
    elif sh.name == "Rounded Rectangle 37":
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor(14, 116, 144) # Cyan/Teal #0E7490
        sh.line.color.rgb = RGBColor(6, 182, 212)
        sh.line.width = Pt(1.5)
        for p in sh.text_frame.paragraphs:
            p.font.name = "Arial"
            p.font.size = Pt(12)
            p.font.bold = True
            p.font.color.rgb = C_WHITE
    elif sh.name == "Picture 4":
        clean_bulb_path = os.path.join(SCRATCH_DIR, "sih_bulb_clean.png")
        if os.path.exists(clean_bulb_path):
            with open(clean_bulb_path, "rb") as f:
                new_blob = f.read()
            rId = sh._element.xpath('.//a:blip/@r:embed')[0]
            img_part = s1.part.related_part(rId)
            img_part._blob = new_blob
            # remove srcRect crop so the whole clean bulb is displayed
            srcRects = sh._element.xpath('.//a:srcRect')
            for sr in srcRects:
                sr.getparent().remove(sr)

# Update Team Name Badge on all subsequent slides
for idx in range(1, len(prs.slides)):
    s = prs.slides[idx]
    for sh in s.shapes:
        if "Oval" in sh.name:
            sh.left = Inches(0.36)
            sh.top = Inches(0.24)
            sh.width = Inches(1.50)
            sh.height = Inches(0.68)
            sh.fill.solid()
            sh.fill.fore_color.rgb = RGBColor(15, 23, 42) # #0F172A Dark Slate Navy
            sh.line.color.rgb = RGBColor(2, 132, 199)     # #0284C7 Cyan Accent Border
            sh.line.width = Pt(1.5)
            
            tf = sh.text_frame
            tf.word_wrap = False
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.text = "selfNprove"
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            p.font.name = "Arial"
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 255, 255) # PURE CRISP WHITE

# ==========================================
# SLIDE 2: PROPOSED SOLUTION
# ==========================================
s2 = prs.slides[1]

# Polish Top Summary Banner (Rectangle 15362)
for sh in s2.shapes:
    if sh.name == "Rectangle 15362":
        sh.top = Inches(1.10)
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor(241, 245, 249) # Clean light theme banner
        sh.line.color.rgb = RGBColor(203, 213, 225)
        sh.line.width = Pt(1.0)
        tf = sh.text_frame
        for p in tf.paragraphs:
            p.font.name = "Arial"
            p.font.size = Pt(10.5)
            p.font.bold = True
            p.font.color.rgb = RGBColor(15, 23, 42)

# Polish 3 Top Solution Cards
s2_cards_data = {
    "Rounded Rectangle 15363": (
        "Detailed Proposed Solution",
        [
            ("Optical IQA Safety Gatekeeper:", " Autonomous 4-metric validation (Focus, Illumination, FOV, Centering) intercepts degraded captures before classifier."),
            ("5-Class ICDR Staging:", " Frozen EfficientNetB3 classifier evaluates exact severity from Grade 0 (Normal) to Grade 4 (PDR) with 81.15% Val Acc."),
            ("6-System Deep Biomarkers:", " Pixel segmentations for Optic Disc (0.986 Dice), Hard Exudates, Hemorrhages, Cotton Wool, Vessels & MAs."),
            ("Zero-Latency Vector PDF:", " In-browser clinical report with color badges, risk probabilities, CSME spatial flag & doctor legal sign-off block.")
        ]
    ),
    "Rounded Rectangle 15364": (
        "How It Addresses the Problem?",
        [
            ("Overcomes 1:100k Doctor Gap:", " Frontline ASHA workers perform complete clinical-grade triage in 15 seconds without specialist presence."),
            ("Zero Dilation Drops:", " Works seamlessly with commercial non-mydriatic smartphone/desktop cameras, eliminating diagnostic delay."),
            ("Decongests District Hospitals:", " Filters out 85% non-referable healthy population in the village; triages only high-risk vision threats."),
            ("Guaranteed Clinical Safety:", " Images with focus score <45 strictly bypass AI inference with instant audio-visual recapture guidance.")
        ]
    ),
    "Rounded Rectangle 15365": (
        "Innovation & Uniqueness",
        [
            ("Dual-Level Explainability (XAI):", " Macroscopic Grad-CAM heatmaps combined with microscopic pixel-accurate U-Net lesion contours."),
            ("Rural-Calibrated Sensitivity:", " Tuned operating point (t = 0.1181) delivering 99.27% referable sensitivity (zero missed PDR cases)."),
            ("MathWorks Certified Capacity:", " Discrete-event M/M/1 queue model proving 5.9M screenings/year (58x margin over 100k annual mandate)."),
            ("100% Offline Edge Inference:", " Runs entirely on standard field laptops or $100 embedded hardware (Jetson / RPi5) without internet.")
        ]
    )
}

for sh_name, (tab_title, bullets) in s2_cards_data.items():
    for sh in s2.shapes:
        if sh.name == sh_name:
            sh.fill.solid()
            sh.fill.fore_color.rgb = C_ICE_BLUE
            sh.line.color.rgb = C_BORDER_BLUE
            sh.line.width = Pt(1.5)
            tf = sh.text_frame
            tf.word_wrap = True
            
            # Header
            p0 = tf.paragraphs[0]
            p0.text = tab_title
            p0.font.name = "Arial"
            p0.font.size = Pt(13.5)
            p0.font.bold = True
            p0.font.color.rgb = C_NAVY
            p0.space_after = Pt(6)
            
            # Bullets
            for j, (bold_k, body_t) in enumerate(bullets):
                p = tf.add_paragraph() if j > 0 or len(tf.paragraphs) > 1 else tf.add_paragraph()
                p.space_after = Pt(3.5)
                
                r_dot = p.add_run()
                r_dot.text = "•  "
                r_dot.font.name = "Arial"
                r_dot.font.size = Pt(10.5)
                r_dot.font.bold = True
                r_dot.font.color.rgb = RGBColor(0, 0, 0)

                r_k = p.add_run()
                r_k.text = bold_k
                r_k.font.name = "Arial"
                r_k.font.size = Pt(10.5)
                r_k.font.bold = True
                r_k.font.color.rgb = C_NAVY

                r_b = p.add_run()
                r_b.text = body_t
                r_b.font.name = "Arial"
                r_b.font.size = Pt(10)
                r_b.font.color.rgb = C_TEXT_MUTED

# Polish Bottom Showcase Panels (Rounded Rectangle 15366 & 15370)
for sh in s2.shapes:
    if sh.name in ["Rounded Rectangle 15366", "Rounded Rectangle 15370"]:
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor(248, 250, 252)
        sh.line.color.rgb = RGBColor(203, 213, 225)
        sh.line.width = Pt(1.5)
        tf = sh.text_frame
        if tf.paragraphs:
            p = tf.paragraphs[0]
            p.font.name = "Arial"
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = C_NAVY

# ==========================================
# SLIDE 3: TECHNICAL APPROACH
# ==========================================
s3 = prs.slides[2]

# Replace dark architecture square with clean light-theme flowchart by swapping blob
FLOWCHART = os.path.join(ASSETS_DIR, "arch_flowchart_clean.png")
for sh in s3.shapes:
    if sh.name == "Picture 17410" and os.path.exists(FLOWCHART):
        with open(FLOWCHART, "rb") as f:
            new_blob = f.read()
        rId = sh._element.xpath('.//a:blip/@r:embed')[0]
        img_part = s3.part.related_part(rId)
        img_part._blob = new_blob

# Polish Methodology Card (Rounded Rectangle 17411)
for sh in s3.shapes:
    if sh.name == "Rounded Rectangle 17411":
        sh.fill.solid()
        sh.fill.fore_color.rgb = C_ICE_BLUE
        sh.line.color.rgb = C_BORDER_BLUE
        sh.line.width = Pt(1.5)
        tf = sh.text_frame
        for i, p in enumerate(tf.paragraphs):
            if i == 0:
                p.font.name = "Arial"
                p.font.size = Pt(13)
                p.font.bold = True
                p.font.color.rgb = C_NAVY
            else:
                p.font.name = "Arial"
                p.font.size = Pt(10)
                p.font.color.rgb = C_TEXT_DARK

# Polish Hardware Card (Rounded Rectangle 17412)
for sh in s3.shapes:
    if sh.name == "Rounded Rectangle 17412":
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor(254, 243, 199) # Warm light amber #FEF3C7
        sh.line.color.rgb = RGBColor(245, 158, 11)      # Amber border
        sh.line.width = Pt(1.5)
        tf = sh.text_frame
        for i, p in enumerate(tf.paragraphs):
            if i == 0:
                p.font.name = "Arial"
                p.font.size = Pt(12.5)
                p.font.bold = True
                p.font.color.rgb = RGBColor(146, 64, 14)
            else:
                p.font.name = "Arial"
                p.font.size = Pt(10)
                p.font.color.rgb = C_TEXT_DARK

# Polish Tech Stack Shape (Rectangle 17413) -> Clean single-bar text layout (NO overlapping icons)
for sh in s3.shapes:
    if sh.name == "Rectangle 17413":
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor(241, 245, 249) # #F1F5F9 clean card fill
        sh.line.color.rgb = RGBColor(203, 213, 225)     # subtle gray border
        sh.line.width = Pt(1.0)
        tf = sh.text_frame
        tf.word_wrap = False
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = ""
        p.alignment = PP_ALIGN.CENTER
        
        r1 = p.add_run()
        r1.text = "TECHNOLOGY STACK:  "
        r1.font.name = "Arial"
        r1.font.size = Pt(9.5)
        r1.font.bold = True
        r1.font.color.rgb = C_NAVY
        
        r2 = p.add_run()
        r2.text = "PyTorch  •  MathWorks Simulink (.slx)  •  FastAPI  •  Next.js 14  •  OpenCV  •  TensorRT  •  Docker"
        r2.font.name = "Arial"
        r2.font.size = Pt(9.0)
        r2.font.bold = True
        r2.font.color.rgb = RGBColor(51, 65, 85) # Slate 700

# ==========================================
# SLIDE 4: FEASIBILITY AND VIABILITY
# ==========================================
s4 = prs.slides[3]

# Polish Left 3 Cards
s4_cards = ["Rounded Rectangle 17410", "Rounded Rectangle 17411", "Rounded Rectangle 17412"]
for sh in s4.shapes:
    if sh.name in s4_cards:
        sh.fill.solid()
        sh.fill.fore_color.rgb = C_ICE_BLUE
        sh.line.color.rgb = C_BORDER_BLUE
        sh.line.width = Pt(1.5)
        tf = sh.text_frame
        for i, p in enumerate(tf.paragraphs):
            # Replace ₹ with INR
            if "₹" in p.text:
                for r in p.runs:
                    r.text = r.text.replace("₹", "INR ")
            if i == 0:
                p.font.name = "Arial"
                p.font.size = Pt(12.5)
                p.font.bold = True
                p.font.color.rgb = C_NAVY
            else:
                p.font.name = "Arial"
                p.font.size = Pt(10)
                p.font.color.rgb = C_TEXT_DARK

# Polish Right Simulink Card (Rounded Rectangle 17413)
for sh in s4.shapes:
    if sh.name == "Rounded Rectangle 17413":
        sh.fill.solid()
        sh.fill.fore_color.rgb = C_WHITE
        sh.line.color.rgb = RGBColor(14, 116, 144) # Teal border
        sh.line.width = Pt(1.5)
        tf = sh.text_frame
        for i, p in enumerate(tf.paragraphs):
            if i == 0:
                p.font.name = "Arial"
                p.font.size = Pt(12)
                p.font.bold = True
                p.font.color.rgb = C_NAVY
            else:
                p.font.name = "Arial"
                p.font.size = Pt(9.5)
                p.font.color.rgb = C_TEXT_MUTED

# ==========================================
# SLIDE 5: IMPACT AND USER STORY
# ==========================================
s5 = prs.slides[4]

# Polish Left 3 Beneficiary Cards
s5_cards = ["Rounded Rectangle 17410", "Rounded Rectangle 17411", "Rounded Rectangle 17412"]
for sh in s5.shapes:
    if sh.name in s5_cards:
        sh.fill.solid()
        sh.fill.fore_color.rgb = C_ICE_BLUE
        sh.line.color.rgb = C_BORDER_BLUE
        sh.line.width = Pt(1.5)
        tf = sh.text_frame
        for i, p in enumerate(tf.paragraphs):
            if "₹" in p.text:
                for r in p.runs:
                    r.text = r.text.replace("₹", "INR ")
            if i == 0:
                p.font.name = "Arial"
                p.font.size = Pt(12.5)
                p.font.bold = True
                p.font.color.rgb = C_NAVY
            else:
                p.font.name = "Arial"
                p.font.size = Pt(10)
                p.font.color.rgb = C_TEXT_DARK

# Polish Right User Story Card (Rounded Rectangle 17413)
for sh in s5.shapes:
    if sh.name == "Rounded Rectangle 17413":
        sh.fill.solid()
        sh.fill.fore_color.rgb = C_WHITE
        sh.line.color.rgb = RGBColor(16, 185, 129) # Emerald border
        sh.line.width = Pt(1.5)
        tf = sh.text_frame
        for i, p in enumerate(tf.paragraphs):
            if i == 0:
                p.font.name = "Arial"
                p.font.size = Pt(12.5)
                p.font.bold = True
                p.font.color.rgb = C_NAVY
            else:
                p.font.name = "Arial"
                p.font.size = Pt(10)
                p.font.color.rgb = C_TEXT_DARK

# ==========================================
# SLIDE 6: RESEARCH AND REFERENCES
# ==========================================
s6 = prs.slides[5]

# Polish 8 Reference Cards
s6_card_names = [f"Rounded Rectangle {i}" for i in range(17410, 17418)]
for sh in s6.shapes:
    if sh.name in s6_card_names:
        sh.fill.solid()
        sh.fill.fore_color.rgb = C_ICE_BLUE
        sh.line.color.rgb = C_BORDER_BLUE
        sh.line.width = Pt(1.5)
        tf = sh.text_frame
        for i, p in enumerate(tf.paragraphs):
            if i == 0:
                p.font.name = "Arial"
                p.font.size = Pt(12)
                p.font.bold = True
                p.font.color.rgb = C_LINK_BLUE
            elif i == 1:
                p.font.name = "Arial"
                p.font.size = Pt(10)
                p.font.bold = True
                p.font.color.rgb = C_NAVY
            else:
                p.font.name = "Arial"
                p.font.size = Pt(9.5)
                p.font.color.rgb = C_TEXT_MUTED

# Save updated presentation
prs.save(OUT_PPTX)
print("SUCCESS: Template preserved and polished to winner level:", OUT_PPTX)
