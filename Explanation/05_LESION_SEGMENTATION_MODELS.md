# 05. IDRiD Pixel Lesion Segmentation Models & CSME Calculation

---

## What is This? (In Simple Words)
While the classifier looks at the whole eye and gives an overall stage (0 to 4), the **Lesion Segmentation Models** act like a microscopic magnifying glass. They scan every single pixel in the image to locate, measure, and highlight the exact physical signs of diabetes:
1. **Optic Disc (OD)**: The circular entry point of the optic nerve (the eye's natural blind spot).
2. **Hard Exudates (EX)**: Bright yellowish-white crusts of leaking fat and protein.
3. **Hemorrhages (HE)**: Red blood leaks from broken retinal capillaries.
4. **Soft Exudates / Cotton Wool Spots (SE)**: Fluffy white patches of nerve fiber swelling due to oxygen starvation.
5. **CSME (Clinically Significant Macular Edema)**: Swelling near the center of vision that threatens permanent blindness.

---

## Why Was It Needed? (The Real Problem It Solves)

1. **A Grade Number is Not Enough for a Surgeon**: If an AI just says *"Grade 3 DR"*, an eye surgeon cannot perform laser photocoagulation or anti-VEGF injections without knowing **which quadrant is leaking and how close the leaks are to the center of sight**.
2. **The "Optic Disc Confusion" Trap**: The normal human Optic Disc is bright, yellowish-orange with sharp borders. Under a microscope, it looks **almost identical to a giant hard exudate lesion!**
   - Basic AI models mistake the normal optic disc for severe disease (creating false alarms).
   - Our system segments the Optic Disc with a world-class **0.9859 Dice score**, allowing the AI to say: *"This yellow circle is the normal optic nerve, NOT a lesion."*
3. **CSME (Macular Edema) Can Happen at ANY Stage**: A patient can have early-stage DR (Grade 1), but if a lipid leak happens right in the middle of their macula (fovea), they will lose their central vision in weeks. The only way to diagnose CSME from a 2D fundus photo is by calculating the exact physical distance between exudates and the fovea.

---

## The Segmentation Models & Architectures

We trained dedicated **PyTorch U-Net / DeepLabV3+** semantic segmentation networks using the pixel-level ground truth masks from the **IDRiD (Indian Diabetic Retinopathy Image Dataset)** challenge:

```
                Input Retinal Image (512 x 512)
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
[Optic Disc Net]       [Hard Exudates Net]   [Hemorrhages Net]
(idrid_optic_disc.pth) (idrid_exudates.pth)  (idrid_hemorrhages.pth)
     Dice: 0.9859          Dice: 0.7580          Dice: 0.7482
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
            [Multi-Class Mask Fusion & CSME Engine]
                              │
                              ▼
             [Evidence Overlay + Quantitative Counts]
```

### Segmentation Performance on Real IDRiD Test Cohort

| Target Structure | Trained Checkpoint | Dice Score | IoU (Jaccard) | Clinical Significance |
| :--- | :--- | :---: | :---: | :--- |
| **Optic Disc** | `idrid_optic_disc_best.pth` | **0.9859** | **0.9721** | Anatomical reference & false-positive suppressor. |
| **Hard Exudates** | `idrid_exudates_best.pth` | **0.7580** | **0.6103** | Primary clinical biomarker for macular edema (CSME). |
| **Hemorrhages** | `idrid_hemorrhages_best.pth` | **0.7482** | **0.5977** | Capillary leakage marker for ICDR severity staging. |
| **Soft Exudates** | `idrid_soft_exudates_best.pth` | **0.7120** | **0.5528** | Micro-infarction & retinal ischemia indicator. |

---

## How CSME (Macular Edema) is Calculated

In clinical ophthalmology, **Clinically Significant Macular Edema (CSME)** is defined according to the landmark **ETDRS (Early Treatment Diabetic Retinopathy Study)** criteria:
- Any hard exudate within **500 microns (< 1/3 Disc Diameter)** from the foveal center.
- Or retinal thickening / hard exudates within **1 Disc Diameter (1 DD)** if associated with adjacent edema.

### Our Algorithmic Implementation (`evidence/detector.py`):
1. **Find the Optic Disc Diameter ($DD$)**: Using the segmented Optic Disc mask, compute the average diameter in pixels ($DD_{px} \approx 80-120 \text{ px}$ depending on image scale). In human biology, $1 DD \approx 1,500 \text{ microns}$.
2. **Locate the Fovea (Center of Sight)**: The fovea naturally lies approximately **2.5 Disc Diameters temporal** to the center of the optic disc, inside the dark macular avascular zone.
3. **Measure Euclidean Distance ($d_{min}$)**: Calculate the minimum Euclidean distance between the foveal center and the nearest hard exudate pixel:
   $$d_{min} = \min_{p \in \text{Exudates}} \| p - \text{Fovea} \|_2$$
4. **Trigger CSME Alert**:
   $$\text{If } d_{min} < 1.0 \times DD_{px} \implies \mathbf{CSME\ POSITIVE\ (Immediate\ Referral)}$$

---

## Judge Q&A Cheatsheet (Segmentation & CSME)

* **Q: "Why is your Optic Disc Dice score so high (0.9859) compared to exudates (0.7580)?"**
  * *A*: *"The Optic Disc is a large, contiguous, macro-anatomical structure with high contrast, making Dice scores near 0.99 standard. In contrast, hard exudates and hemorrhages are microscopic punctate lesions (often 3 to 10 pixels wide across a 2000x2000 image). A single-pixel boundary shift disproportionately penalizes the Dice metric on tiny lesions, meaning 0.7580 on IDRiD represents state-of-the-art clinical performance."*

* **Q: "Can you diagnose macular edema from a 2D photograph without an OCT scan?"**
  * *A*: *"While optical coherence tomography (OCT) measures cross-sectional fluid thickness directly, ETDRS established that hard exudates are the direct lipid residue left behind by macular edema fluid. Measuring hard exudate proximity to the foveal center in units of optic disc diameters is the globally accepted standard for 2D fundus screening triage."*
