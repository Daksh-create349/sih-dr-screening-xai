import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas

SCRATCH_DIR = "/Users/dakshsrivastava/.gemini/antigravity-ide/brain/55ce27ec-16f4-45fe-9e80-3876e1585bb8/scratch"
BACKUP_ASSETS = os.path.join(SCRATCH_DIR, "backup_assets")
TECH_DIR = os.path.join(SCRATCH_DIR, "tech_logos")
SLIDES_OUT = os.path.join(SCRATCH_DIR, "upgraded_slides")
os.makedirs(SLIDES_OUT, exist_ok=True)

W, H = 2400, 1350  # 16:9 widescreen

# Fonts
f_title = ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf', 44)
f_huge = ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf', 58)
f_sub = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 24)
f_card_head = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 23)
f_body_bold = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
f_body = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 18)
f_meta_k = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 26)
f_meta_v = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 26)
f_small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
f_pill = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 22)

# Official Logo
SIH_LOGO_ORIG = Image.open(os.path.join(BACKUP_ASSETS, "s1_6_Picture_1.png")).convert("RGBA")
SIH_BULB = Image.open(os.path.join(SCRATCH_DIR, "sih_bulb_clean.png")).convert("RGBA")
FLOWCHART = Image.open(os.path.join(SCRATCH_DIR, "winner_assets", "arch_flowchart_clean.png")).convert("RGBA")

def draw_header_footer(im, draw, title_text, slide_num):
    # Top Left Oval Badge
    draw.rounded_rectangle([65, 45, 310, 175], radius=40, fill='#FFFFFF', outline='#7C3AED', width=3)
    draw.text((187, 110), 'selfNprove', fill='#0F294A', font=f_pill, anchor='mm')

    # Top Center Title
    draw.text((W/2, 110), title_text, fill='#0F294A', font=f_title, anchor='mm')

    # Top Right Official SIH 2026 Logo
    lw, lh = 380, 170
    im.paste(SIH_LOGO_ORIG.resize((lw, lh), Image.Resampling.LANCZOS), (W - lw - 65, 25), mask=SIH_LOGO_ORIG.resize((lw, lh)))

    # Blue Bottom Bar
    draw.rectangle([0, H - 75, W, H], fill='#0273B5')
    # Footer Placeholder
    draw.text((W/2, H - 38), '@SIH Idea submission- Template', fill='#FFFFFF', font=f_body_bold, anchor='mm')
    # Slide Number Placeholder
    draw.text((W - 75, H - 38), str(slide_num), fill='#FFFFFF', font=f_body_bold, anchor='mm')

# ==========================================
# SLIDE 1: COVER
# ==========================================
im1 = Image.new('RGBA', (W, H), '#FFFFFF')
d1 = ImageDraw.Draw(im1)

# SIH Logo Top Right
lw, lh = 450, 205
im1.paste(SIH_LOGO_ORIG.resize((lw, lh), Image.Resampling.LANCZOS), (W - lw - 90, 45), mask=SIH_LOGO_ORIG.resize((lw, lh)))

d1.text((120, 110), 'SMART INDIA HACKATHON 2026', fill='#1A4584', font=f_huge, anchor='lm')
d1.text((125, 175), 'AUTONOMOUS EXPLAINABLE TELE-SCREENING PLATFORM', fill='#0D9488', font=f_sub, anchor='lm')

meta_items = [
    ("Problem Statement ID", "26038"),
    ("Problem Statement Title", "Explainable AI for Diabetic Retinopathy Screening in Rural India"),
    ("Partner Organization", "MathWorks India"),
    ("Theme", "MedTech / Healthcare & Biomedical Devices"),
    ("PS Category", "Software"),
    ("Team Name", "selfNprove"),
    ("Team Leader", "Daksh Srivastava (dakshshrivastav56@gmail.com)"),
    ("Team Members", "Samarth Navale, Aaryan Kuchekar, Gaurav Patel, Aaditya Bhosale, Jiya Jana"),
    ("Registered Team ID", "")
]

my = 280
for k, v in meta_items:
    d1.text((125, my), '•  ', fill='#000000', font=f_meta_k, anchor='lm')
    d1.text((155, my), f'{k}: ', fill='#0F294A', font=f_meta_k, anchor='lm')
    kw_w = f_meta_k.getbbox(f'{k}: ')[2] - f_meta_k.getbbox(f'{k}: ')[0]
    d1.text((155 + kw_w + 5, my), v, fill='#1F2937', font=f_meta_v, anchor='lm')
    my += 82

# Bottom Pill Badge
d1.rounded_rectangle([120, H - 160, 1250, H - 90], radius=20, fill='#0E7490', outline='#06B6D4', width=2)
d1.text((685, H - 125), 'MathWorks Simulink 8-Subsystem Architecture Verified (DR_screening_workflow.slx)', fill='#FFFFFF', font=f_sub, anchor='mm')

# SIH Bulb on Right
bh = 720
bw = int(bh * SIH_BULB.width / SIH_BULB.height)
bulb_x = W - bw - 180
bulb_y = int((H - bh) / 2) + 40
im1.paste(SIH_BULB.resize((bw, bh), Image.Resampling.LANCZOS), (bulb_x, bulb_y), mask=SIH_BULB.resize((bw, bh)))
im1.convert('RGB').save(os.path.join(SLIDES_OUT, 'slide_1.png'))
print('Slide 1 rendered')

# ==========================================
# SLIDE 2: PROPOSED SOLUTION
# ==========================================
im2 = Image.new('RGBA', (W, H), '#FFFFFF')
d2 = ImageDraw.Draw(im2)
draw_header_footer(im2, d2, 'PROPOSED SOLUTION: RETINASCAN-AI WORKSTATION', 2)

# Top Summary Banner
d2.rounded_rectangle([70, 200, W - 70, 265], radius=16, fill='#0F294A', outline='#1E40AF', width=2)
d2.text((W/2, 232), 'An autonomous tele-screening workstation for rural Primary Health Centres (PHCs) uniting Optical IQA, 5-Class ICDR Staging & Dual-Level XAI', fill='#FFFFFF', font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20), anchor='mm')

# 3 Solution Cards
cards_s2 = [
    (
        "Detailed Proposed Solution",
        [
            ("Optical IQA Gatekeeper:", " Autonomous 4-metric validation (Focus, Illum, FOV, Centering) intercepts bad captures before classifier."),
            ("5-Class ICDR Staging:", " Frozen EfficientNetB3 classifier evaluates severity from Grade 0 (Normal) to Grade 4 (PDR) with 81.15% Val Acc."),
            ("6 Deep Biomarkers:", " Pixel segmentations for Optic Disc (0.986 Dice), Hard Exudates, Hemorrhages, Soft Exudates, Vessels & MAs."),
            ("Zero-Latency Vector PDF:", " Clinical report with color badges, risk probabilities, CSME spatial flag & doctor legal sign-off block.")
        ]
    ),
    (
        "How It Addresses the Problem?",
        [
            ("Overcomes 1:100k Doctor Gap:", " Frontline ASHA workers perform complete clinical triage in 15 seconds without specialist presence."),
            ("Zero Dilation Drops:", " Operates seamlessly with non-mydriatic smartphone/desktop cameras, eliminating diagnostic delay."),
            ("Decongests District Hospitals:", " Filters out 85% non-referable population in village; triages only vision threats."),
            ("Guaranteed Clinical Safety:", " Focus score <45 strictly bypasses AI inference with instant audio-visual recapture guidance.")
        ]
    ),
    (
        "Innovation & Uniqueness",
        [
            ("Dual-Level Explainability (XAI):", " Macroscopic Grad-CAM heatmaps combined with microscopic pixel-accurate U-Net lesion contours."),
            ("Rural-Calibrated Sensitivity:", " Tuned operating point (t = 0.1181) delivering 99.27% referable sensitivity (zero missed PDR)."),
            ("MathWorks Certified Capacity:", " Discrete-event M/M/1 model proving 5.9M screenings/year (58x margin over 100k mandate)."),
            ("100% Offline Edge Inference:", " Runs entirely on field laptops or embedded hardware (Jetson / RPi5) without internet.")
        ]
    )
]

cw = 720
c_gap = 45
cx_start = 70
cy_top = 285

for i, (ctitle, bullets) in enumerate(cards_s2):
    cx = cx_start + i * (cw + c_gap)
    d2.rounded_rectangle([cx, cy_top, cx + cw, cy_top + 600], radius=18, fill='#F0F7FF', outline='#BAD7F2', width=2)
    # Header Tab
    d2.rounded_rectangle([cx, cy_top, cx + cw, cy_top + 60], radius=18, fill='#0B4F8A')
    d2.text((cx + cw/2, cy_top + 30), ctitle, fill='#FFFFFF', font=f_card_head, anchor='mm')

    by = cy_top + 85
    for bold_k, body_t in bullets:
        d2.text((cx + 25, by), '•  ', fill='#000000', font=f_body_bold, anchor='lm')
        d2.text((cx + 45, by), bold_k, fill='#0F294A', font=f_body_bold, anchor='lm')
        bw_k = f_body_bold.getbbox(bold_k)[2] - f_body_bold.getbbox(bold_k)[0]
        words = body_t.strip().split(' ')
        line = ""
        first = True
        cur_x = cx + 45 + bw_k + 8
        for w in words:
            test = line + (" " if line else "") + w
            tw = f_body.getbbox(test)[2]
            if (cur_x + tw) > (cx + cw - 25):
                if first:
                    d2.text((cur_x, by), line, fill='#374151', font=f_body, anchor='lm')
                    first = False
                else:
                    d2.text((cx + 45, by), line, fill='#374151', font=f_body, anchor='lm')
                by += 28
                line = w
                cur_x = cx + 45
            else:
                line = test
        if line:
            if first:
                d2.text((cur_x, by), line, fill='#374151', font=f_body, anchor='lm')
            else:
                d2.text((cx + 45, by), line, fill='#374151', font=f_body, anchor='lm')
            by += 28
        by += 16

# Bottom Showcase Panels
# Left: Clinical Biomarker Overlays
d2.rounded_rectangle([70, 910, 1150, 1240], radius=18, fill='#F8FAFC', outline='#CBD5E1', width=2)
d2.text((610, 940), 'Clinical Biomarker Overlays (Cyan Disc, Gold Exudates, Red Hemorrhages, Green Vessels, Orange MAs)', fill='#0F294A', font=f_body_bold, anchor='mm')

p15367 = Image.open(os.path.join(BACKUP_ASSETS, "s2_12_Picture_15367.png")).convert("RGBA")
p15368 = Image.open(os.path.join(BACKUP_ASSETS, "s2_13_Picture_15368.png")).convert("RGBA")
p15369 = Image.open(os.path.join(BACKUP_ASSETS, "s2_14_Picture_15369.png")).convert("RGBA")

pw, ph = 310, 245
im2.paste(p15367.resize((pw, ph), Image.Resampling.LANCZOS), (100, 975))
im2.paste(p15368.resize((pw, ph), Image.Resampling.LANCZOS), (445, 975))
im2.paste(p15369.resize((pw, ph), Image.Resampling.LANCZOS), (790, 975))

# Right: Frontline PACS Console
d2.rounded_rectangle([1210, 910, W - 70, 1240], radius=18, fill='#F8FAFC', outline='#CBD5E1', width=2)
d2.text((1775, 940), 'Frontline PACS Console: Real-Time Quality Audit, 5-Class Prediction & Doctor Sign-Off', fill='#0F294A', font=f_body_bold, anchor='mm')

p15371 = Image.open(os.path.join(BACKUP_ASSETS, "s2_16_Picture_15371.png")).convert("RGBA")
p15372 = Image.open(os.path.join(BACKUP_ASSETS, "s2_17_Picture_15372.png")).convert("RGBA")

pw_u, ph_u = 520, 245
im2.paste(p15371.resize((pw_u, ph_u), Image.Resampling.LANCZOS), (1240, 975))
im2.paste(p15372.resize((pw_u, ph_u), Image.Resampling.LANCZOS), (1780, 975))

im2.convert('RGB').save(os.path.join(SLIDES_OUT, 'slide_2.png'))
print('Slide 2 rendered')

# ==========================================
# SLIDE 3: TECHNICAL APPROACH
# ==========================================
im3 = Image.new('RGBA', (W, H), '#FFFFFF')
d3 = ImageDraw.Draw(im3)
draw_header_footer(im3, d3, 'TECHNICAL APPROACH & 8-SUBSYSTEM ARCHITECTURE', 3)

# Left Side Flowchart
fc_w, fc_h = 1080, 1020
im3.paste(FLOWCHART.resize((fc_w, fc_h), Image.Resampling.LANCZOS), (70, 205), mask=FLOWCHART.resize((fc_w, fc_h)))

# Right Top Card: Methodology
d3.rounded_rectangle([1190, 205, W - 70, 780], radius=18, fill='#F0F7FF', outline='#BAD7F2', width=2)
d3.text((1220, 245), 'DEEP LEARNING & BIOMARKER METHODOLOGY', fill='#0F294A', font=f_card_head, anchor='lm')

m_bullets = [
    ("Upstream Optical IQA:", " 4-metric gate (Laplacian Focus + Shannon Illumination + Circular FOV + Centering). Ungradeable captures strictly bypass classifier."),
    ("5-Class ICDR Classifier:", " EfficientNetB3 (384x384), 81.15% validation accuracy, Quadratic Weighted Kappa 0.842, cryptographically frozen checkpoint."),
    ("Dual Explainability Suite:", " Macroscopic Grad-CAM heatmaps across 9 anatomical sectors + 4x PyTorch ResNet34 U-Nets (Optic Disc Dice 0.986, Exudates 0.758, Hemorrhages 0.748, Soft Exudates 0.760)."),
    ("Vascular & Microaneurysms:", " Multiscale Frangi Hessian filter (sigma 1.0-2.0) + inverted green-channel Top-Hat mathematical morphology (2-45 px pinpoint)."),
    ("Referable Triage Gate:", " High-sensitivity calibration (t = 0.1181) delivering 99.27% Sensitivity (0.73% False Negative Rate; <1 in 135 missed).")
]

my = 295
for bold_k, body_t in m_bullets:
    d3.text((1225, my), '•  ', fill='#000000', font=f_body_bold, anchor='lm')
    d3.text((1250, my), bold_k, fill='#0F294A', font=f_body_bold, anchor='lm')
    bw_k = f_body_bold.getbbox(bold_k)[2] - f_body_bold.getbbox(bold_k)[0]
    words = body_t.strip().split(' ')
    line = ""
    first = True
    cur_x = 1250 + bw_k + 8
    for w in words:
        test = line + (" " if line else "") + w
        tw = f_body.getbbox(test)[2]
        if (cur_x + tw) > (W - 100):
            if first:
                d3.text((cur_x, my), line, fill='#374151', font=f_body, anchor='lm')
                first = False
            else:
                d3.text((1250, my), line, fill='#374151', font=f_body, anchor='lm')
            my += 28
            line = w
            cur_x = 1250
        else:
            line = test
    if line:
        if first:
            d3.text((cur_x, my), line, fill='#374151', font=f_body, anchor='lm')
        else:
            d3.text((1250, my), line, fill='#374151', font=f_body, anchor='lm')
        my += 28
    my += 14

# Right Mid Card: Hardware Profile & Simulink Capacity
d3.rounded_rectangle([1190, 805, W - 70, 1050], radius=18, fill='#FEF3C7', outline='#F59E0B', width=2)
d3.text((1220, 840), 'HARDWARE PROFILE & SIMULINK CAPACITY', fill='#92400E', font=f_card_head, anchor='lm')

h_bullets = [
    ("Edge Inference Latency:", " 680 ms on NVIDIA Jetson Orin Nano (TensorRT INT8) | 1.10 s on clinical laptop | 2.40 s on Raspberry Pi 5."),
    ("Memory & Power Profile:", " 1.4 GB RAM overhead, 7–15W power consumption (battery/solar-van compatible)."),
    ("Simulink M/M/1 Capacity:", " Ts = 1.22s -> 5.9M screenings/yr capacity (58x margin over 100k annual mandate; rho = 0.017).")
]

hy = 885
for bold_k, body_t in h_bullets:
    d3.text((1225, hy), '•  ', fill='#000000', font=f_body_bold, anchor='lm')
    d3.text((1250, hy), bold_k, fill='#92400E', font=f_body_bold, anchor='lm')
    bw_k = f_body_bold.getbbox(bold_k)[2] - f_body_bold.getbbox(bold_k)[0]
    words = body_t.strip().split(' ')
    line = ""
    first = True
    cur_x = 1250 + bw_k + 8
    for w in words:
        test = line + (" " if line else "") + w
        tw = f_body.getbbox(test)[2]
        if (cur_x + tw) > (W - 100):
            if first:
                d3.text((cur_x, hy), line, fill='#374151', font=f_body, anchor='lm')
                first = False
            else:
                d3.text((1250, hy), line, fill='#374151', font=f_body, anchor='lm')
            hy += 28
            line = w
            cur_x = 1250
        else:
            line = test
    if line:
        if first:
            d3.text((cur_x, hy), line, fill='#374151', font=f_body, anchor='lm')
        else:
            d3.text((1250, hy), line, fill='#374151', font=f_body, anchor='lm')
        hy += 28
    hy += 12

# Right Bottom: Tech Stack with Brand Logos
d3.rounded_rectangle([1190, 1075, W - 70, 1225], radius=18, fill='#FFFFFF', outline='#CBD5E1', width=2)
d3.text((1220, 1150), 'TECHNOLOGY\nSTACK', fill='#0F294A', font=f_body_bold, anchor='lm')

logos_info = [
    ("FastAPI", os.path.join(TECH_DIR, "fastapi.png")),
    ("PyTorch", os.path.join(TECH_DIR, "pytorch.svg.png")),
    ("MathWorks", os.path.join(TECH_DIR, "matlab.svg.png")),
    ("OpenCV", os.path.join(TECH_DIR, "opencv.svg.png")),
    ("React", os.path.join(TECH_DIR, "react.svg.png")),
    ("Docker", os.path.join(TECH_DIR, "docker.svg.png")),
    ("Keras", os.path.join(TECH_DIR, "keras.svg.png")),
    ("Python", os.path.join(TECH_DIR, "python.svg.png"))
]

gx_base = 1430
col_w = 110
for idx, (lname, lpath) in enumerate(logos_info):
    lx = gx_base + idx * col_w
    if os.path.exists(lpath):
        lim = Image.open(lpath).convert('RGBA')
        lim_thumb = lim.resize((65, 65), Image.Resampling.LANCZOS)
        im3.paste(lim_thumb, (lx, 1100), mask=lim_thumb)
    d3.text((lx + 32, 1185), lname, fill='#0F294A', font=f_small, anchor='mm')

im3.convert('RGB').save(os.path.join(SLIDES_OUT, 'slide_3.png'))
print('Slide 3 rendered')

# ==========================================
# SLIDE 4: FEASIBILITY AND VIABILITY
# ==========================================
im4 = Image.new('RGBA', (W, H), '#FFFFFF')
d4 = ImageDraw.Draw(im4)
draw_header_footer(im4, d4, 'FEASIBILITY AND VIABILITY ANALYSIS', 4)

cards_s4 = [
    (
        "ANALYSIS OF THE FEASIBILITY OF THE IDEA",
        [
            ("Technical Feasibility:", " Complete working prototype built and validated; frozen weights, 15 unit tests, 8 integration tests, 100% zero synthetic data."),
            ("Operational Feasibility:", " Non-mydriatic handheld mobile fundus lenses (Remidio/Volk INR 15k–35k); ASHA workers operate after 15-minute standard training."),
            ("Financial & Social Feasibility:", " Zero-cost village screening; saves rural families INR 2,000 in travel/wage loss while cutting government hospital crowding.")
        ]
    ),
    (
        "POTENTIAL CHALLENGES AND CLINICAL RISKS",
        [
            ("Optical Degradation in the Field:", " Motion blur, eyelid tremors, and cataract opacity in rural elders cause severe fundus image artifacts."),
            ("Clinician Distrust of Black-Box AI:", " Ophthalmologists legally reject AI predictions without visible, measurable anatomical proof."),
            ("Intermittent Rural Connectivity:", " Primary Health Centres in remote tribal districts lack reliable broadband internet.")
        ]
    ),
    (
        "STRATEGIES FOR OVERCOMING CHALLENGES",
        [
            ("Automated Hardware Safety Interlock:", " Composite IQA score <45 strictly halts inference, giving instant voice/text guidance ('Steady lens / re-align pupil')."),
            ("Epistemic Integrity & Biomarker Suite:", " Every annotation is declared with provenance (GROUND_TRUTH vs DETECTED vs ESTIMATED) + CSME geometry."),
            ("100% Offline Edge Processing:", " FastAPI + ONNX executes fully offline on local laptops; syncs encrypted reports only when network is present.")
        ]
    )
]

c4_w = 1380
c4_h = 310
c4_y = [205, 545, 885]

for i, (htitle, bullets) in enumerate(cards_s4):
    cy = c4_y[i]
    d4.rounded_rectangle([70, cy, 70 + c4_w, cy + c4_h], radius=18, fill='#F0F7FF', outline='#BAD7F2', width=2)
    d4.text((70 + c4_w/2, cy + 35), htitle, fill='#0F294A', font=f_card_head, anchor='mm')
    
    by = cy + 85
    for bold_k, body_t in bullets:
        d4.text((105, by), '•  ', fill='#000000', font=f_body_bold, anchor='lm')
        d4.text((130, by), bold_k, fill='#0F294A', font=f_body_bold, anchor='lm')
        bw_k = f_body_bold.getbbox(bold_k)[2] - f_body_bold.getbbox(bold_k)[0]
        words = body_t.strip().split(' ')
        line = ""
        first = True
        cur_x = 130 + bw_k + 8
        for w in words:
            test = line + (" " if line else "") + w
            tw = f_body.getbbox(test)[2]
            if (cur_x + tw) > (70 + c4_w - 35):
                if first:
                    d4.text((cur_x, by), line, fill='#374151', font=f_body, anchor='lm')
                    first = False
                else:
                    d4.text((130, by), line, fill='#374151', font=f_body, anchor='lm')
                by += 28
                line = w
                cur_x = 130
            else:
                line = test
        if line:
            if first:
                d4.text((cur_x, by), line, fill='#374151', font=f_body, anchor='lm')
            else:
                d4.text((130, by), line, fill='#374151', font=f_body, anchor='lm')
            by += 28
        by += 14

# Right Side: MathWorks Simulink Architecture & Verification
d4.rounded_rectangle([1490, 205, W - 70, 1195], radius=18, fill='#FFFFFF', outline='#0E7490', width=2)
d4.text((1915, 245), 'MATHWORKS SIMULINK ARCHITECTURE & VERIFICATION', fill='#0E7490', font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20), anchor='mm')
d4.text((1915, 275), 'Formal 8-Subsystem Model (DR_screening_workflow.slx)', fill='#4B5563', font=f_small, anchor='mm')

# Simulink Model Screenshot
p_sim = Image.open(os.path.join(BACKUP_ASSETS, "s4_11_Picture_17414.png")).convert("RGBA")
sw, sh = 780, 520
im4.paste(p_sim.resize((sw, sh), Image.Resampling.LANCZOS), (1520, 310))

# 3 Metrics Badges below Simulink screenshot
sim_points = [
    ("Strict Bypass Interlock:", " Ungradeable quality automatically routes to recapture queue without executing neural weights."),
    ("Borderline Feedback Loop:", " CLAHE contrast enhancement dynamically evaluated before granting inference clearance."),
    ("M/M/1 Capacity Proof:", " 5.9M peak screenings/year; steady-state queue length remains near zero over 100,000 requests.")
]
sy = 865
for bold_k, body_t in sim_points:
    d4.text((1520, sy), '•  ', fill='#000000', font=f_body_bold, anchor='lm')
    d4.text((1545, sy), bold_k, fill='#0E7490', font=f_body_bold, anchor='lm')
    bw_k = f_body_bold.getbbox(bold_k)[2] - f_body_bold.getbbox(bold_k)[0]
    words = body_t.strip().split(' ')
    line = ""
    first = True
    cur_x = 1545 + bw_k + 8
    for w in words:
        test = line + (" " if line else "") + w
        tw = f_body.getbbox(test)[2]
        if (cur_x + tw) > (W - 95):
            if first:
                d4.text((cur_x, sy), line, fill='#374151', font=f_body, anchor='lm')
                first = False
            else:
                d4.text((1545, sy), line, fill='#374151', font=f_body, anchor='lm')
            sy += 28
            line = w
            cur_x = 1545
        else:
            line = test
    if line:
        if first:
            d4.text((cur_x, sy), line, fill='#374151', font=f_body, anchor='lm')
        else:
            d4.text((1545, sy), line, fill='#374151', font=f_body, anchor='lm')
        sy += 28
    sy += 16

im4.convert('RGB').save(os.path.join(SLIDES_OUT, 'slide_4.png'))
print('Slide 4 rendered')

# ==========================================
# SLIDE 5: IMPACT AND USER STORY
# ==========================================
im5 = Image.new('RGBA', (W, H), '#FFFFFF')
d5 = ImageDraw.Draw(im5)
draw_header_footer(im5, d5, 'IMPACT, SOCIOECONOMIC BENEFITS & USER STORY', 5)

cards_s5 = [
    (
        "FOR RURAL CITIZENS & FAMILIES",
        [
            ("Vision Preservation:", " Detects asymptomatic microvascular breakdown 12–24 months before vision impairment occurs."),
            ("Financial Protection:", " Saves INR 1,500–3,000 in transit and 2 days of lost daily agricultural wages for 85% normal citizens.")
        ]
    ),
    (
        "FOR FRONTLINE ASHA & ANM WORKERS",
        [
            ("Zero-Risk Mobile Screening:", " Non-mydriatic 15-second operation without chemical dilation drops or specialized expertise."),
            ("Instant Optical Feedback:", " Automated focus/illumination prompts empower workers to capture clinical-grade fundus images.")
        ]
    ),
    (
        "FOR OPHTHALMOLOGISTS & PUBLIC HEALTH",
        [
            ("District Hospital Decongestion:", " Pre-filters healthy population, routing only high-priority referable cases (Grade 2–4)."),
            ("Auditable Evidence:", " Generates quantitative lesion contours, CSME clearance, and legal blocks in vector PDF reports.")
        ]
    )
]

c5_w = 1000
c5_h = 310
c5_y = [205, 545, 885]

for i, (htitle, bullets) in enumerate(cards_s5):
    cy = c5_y[i]
    d5.rounded_rectangle([70, cy, 70 + c5_w, cy + c5_h], radius=18, fill='#F0F7FF', outline='#BAD7F2', width=2)
    d5.text((70 + c5_w/2, cy + 35), htitle, fill='#0F294A', font=f_card_head, anchor='mm')
    
    by = cy + 85
    for bold_k, body_t in bullets:
        d5.text((105, by), '•  ', fill='#000000', font=f_body_bold, anchor='lm')
        d5.text((130, by), bold_k, fill='#0F294A', font=f_body_bold, anchor='lm')
        bw_k = f_body_bold.getbbox(bold_k)[2] - f_body_bold.getbbox(bold_k)[0]
        words = body_t.strip().split(' ')
        line = ""
        first = True
        cur_x = 130 + bw_k + 8
        for w in words:
            test = line + (" " if line else "") + w
            tw = f_body.getbbox(test)[2]
            if (cur_x + tw) > (70 + c5_w - 35):
                if first:
                    d5.text((cur_x, by), line, fill='#374151', font=f_body, anchor='lm')
                    first = False
                else:
                    d5.text((130, by), line, fill='#374151', font=f_body, anchor='lm')
                by += 28
                line = w
                cur_x = 130
            else:
                line = test
        if line:
            if first:
                d5.text((cur_x, by), line, fill='#374151', font=f_body, anchor='lm')
            else:
                d5.text((130, by), line, fill='#374151', font=f_body, anchor='lm')
            by += 28
        by += 16

# Right Side: Clinical User Story
d5.rounded_rectangle([1110, 205, W - 70, 1195], radius=18, fill='#FFFFFF', outline='#059669', width=2)
d5.text((1720, 245), 'CLINICAL USER STORY: SITAPUR PHC VALIDATION', fill='#059669', font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 21), anchor='mm')

# Real Clinical Report Screenshot
p_rep = Image.open(os.path.join(BACKUP_ASSETS, "s5_11_Picture_17414.png")).convert("RGBA")
rw, rh = 1150, 560
im5.paste(p_rep.resize((rw, rh), Image.Resampling.LANCZOS), (1145, 280))

# Narrative Text below Report
story_points = [
    ("Patient Scenario:", " Ramesh Kumar (Age 58, Farmer) presented at village PHC with 10-year history of diabetes and zero visual symptoms. ASHA worker captured 45° non-mydriatic fundus in 15 seconds."),
    ("Automated Diagnostic Output:", " IQA Score: 83.5 (GOOD) -> EfficientNetB3 classified Grade 2 Moderate NPDR (79.2% conf) -> Deep U-Net detected 46 Hard Exudate clusters within 0.8 DD of Fovea (HIGH CSME BLINDNESS THREAT)."),
    ("Clinical Outcome:", " High-priority referral triggered to District Eye Hospital within 14 days for anti-VEGF therapy. Irreversible macular edema prevented months before vision loss!")
]

sy = 875
for bold_k, body_t in story_points:
    d5.text((1145, sy), '•  ', fill='#000000', font=f_body_bold, anchor='lm')
    d5.text((1170, sy), bold_k, fill='#059669', font=f_body_bold, anchor='lm')
    bw_k = f_body_bold.getbbox(bold_k)[2] - f_body_bold.getbbox(bold_k)[0]
    words = body_t.strip().split(' ')
    line = ""
    first = True
    cur_x = 1170 + bw_k + 8
    for w in words:
        test = line + (" " if line else "") + w
        tw = f_body.getbbox(test)[2]
        if (cur_x + tw) > (W - 95):
            if first:
                d5.text((cur_x, sy), line, fill='#374151', font=f_body, anchor='lm')
                first = False
            else:
                d5.text((1170, sy), line, fill='#374151', font=f_body, anchor='lm')
            sy += 28
            line = w
            cur_x = 1170
        else:
            line = test
    if line:
        if first:
            d5.text((cur_x, sy), line, fill='#374151', font=f_body, anchor='lm')
        else:
            d5.text((1170, sy), line, fill='#374151', font=f_body, anchor='lm')
        sy += 28
    sy += 16

im5.convert('RGB').save(os.path.join(SLIDES_OUT, 'slide_5.png'))
print('Slide 5 rendered')

# ==========================================
# SLIDE 6: RESEARCH AND REFERENCES
# ==========================================
im6 = Image.new('RGBA', (W, H), '#FFFFFF')
d6 = ImageDraw.Draw(im6)
draw_header_footer(im6, d6, 'RESEARCH, CLINICAL BENCHMARKS & REFERENCES', 6)

refs_data = [
    ("[1] IDRiD Benchmark Dataset", "Indian Diabetic Retinopathy Image Dataset (IEEE Dataport)", "Certified ground-truth pixel segmentations for microaneurysms, hemorrhages, hard/soft exudates, and optic discs."),
    ("[2] APTOS 2019 Blindness Detection", "Asia Pacific Tele-Ophthalmology Society Dataset", "Multicenter clinical fundus cohorts used for fine-tuning and evaluating the 5-class ICDR severity classification model."),
    ("[3] ICDR Clinical Grading Standards", "International Council of Ophthalmology (ICO) Guidelines", "Established the '4-2-1' clinical rule for Severe NPDR classification based on quadrant hemorrhage distributions."),
    ("[4] ETDRS Macular Edema Criteria", "Early Treatment Diabetic Retinopathy Study Protocol", "Geometric ground-truth standards governing Clinically Significant Macular Edema (CSME) based on foveal lipid distance."),
    ("[5] MathWorks Simulink Modeling", "Discrete-Event Architecture & M/M/1 Queue Simulation", "Verified 8-subsystem screening workflow (DR_screening_workflow.slx) establishing 5.9M annual throughput capacity."),
    ("[6] Frangi Multiscale Hessian Filter", "IEEE Transactions on Medical Imaging (TMI)", "Vesselness filter algorithm used to isolate retinal microvasculature calibers, arcade topology, and neovascular loops."),
    ("[7] Grad-CAM Explainability", "Selvaraju et al., IEEE ICCV Framework", "Convolutional feature attribution technique extracting gradient heatmaps across a 9-sector anatomical coordinate grid."),
    ("[8] EfficientNet & U-Net Architectures", "Tan & Le (ICML 2019) | Ronneberger et al. (MICCAI 2015)", "Foundational deep neural architectures powering 5-class severity classification and multi-lesion pixel segmentation.")
]

card_w6 = 1100
card_h6 = 225
c6_x = [70, 1230]
c6_y = [205, 465, 725, 985]

for idx, (rtitle, rsub, rdesc) in enumerate(refs_data):
    col = idx % 2
    row = idx // 2
    rx = c6_x[col]
    ry = c6_y[row]

    d6.rounded_rectangle([rx, ry, rx + card_w6, ry + card_h6], radius=18, fill='#F0F7FF', outline='#BAD7F2', width=2)
    d6.text((rx + 30, ry + 35), rtitle, fill='#1E40AF', font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 22), anchor='lm')
    d6.text((rx + 30, ry + 75), rsub, fill='#0F294A', font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 17), anchor='lm')

    words = rdesc.strip().split(' ')
    line = ""
    dy = ry + 120
    for w in words:
        test = line + (" " if line else "") + w
        tw = f_body.getbbox(test)[2]
        if (rx + 30 + tw) > (rx + card_w6 - 30):
            d6.text((rx + 30, dy), line, fill='#374151', font=f_body, anchor='lm')
            dy += 28
            line = w
        else:
            line = test
    if line:
        d6.text((rx + 30, dy), line, fill='#374151', font=f_body, anchor='lm')

im6.convert('RGB').save(os.path.join(SLIDES_OUT, 'slide_6.png'))
print('Slide 6 rendered')

# Compile PDF
pdf_path = "/Users/dakshsrivastava/Desktop/DR /SIH2026_Idea_Presentation_RetinaScanAI.pdf"
pw, ph = 960, 540
c = canvas.Canvas(pdf_path, pagesize=(pw, ph))

for i in range(1, 7):
    img_path = os.path.join(SLIDES_OUT, f'slide_{i}.png')
    c.drawImage(img_path, 0, 0, width=pw, height=ph)
    c.showPage()

c.save()
print('SUCCESS: Rendered exact upgraded PDF to:', pdf_path)
