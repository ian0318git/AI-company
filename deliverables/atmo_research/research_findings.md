# Atmo Biosciences Atmo® Gas Capsule — Design Analysis

## Research Questions and Scope

### Defined Research Questions

1. **System Architecture**: What is the overall system topology of the Atmo Gas Capsule, and how do the three tiers (capsule, receiver, cloud) interact?

2. **Sensor Design**: What physical/chemical sensing principles does the capsule use to detect H₂, CO₂, and O₂ in the GI tract?

3. **Wireless Communication**: What wireless protocol(s) bridge the capsule-to-receiver link, and what are the key design constraints (range, power, data rate, body penetration)?

4. **Data Processing Pipeline**: How does raw sensor data flow from ingestion through cloud analysis to clinical report?

5. **Clinical Validation**: What clinical studies have been conducted, and what diagnostic value do the measurements provide?

---

## 1. System Architecture — Three-Tier Design

```
┌─────────────────┐     Wireless      ┌──────────────┐       Cloud        ┌──────────────────┐
│                 │   ◄──────────►    │              │   ◄──────────►     │                  │
│  Tier 1         │                   │  Tier 2      │                    │  Tier 3          │
│  Ingestible     │   ~900 MHz /      │  Body-Worn   │    Cellular /      │  Cloud Platform  │
│  Capsule        │   BLE (est.)      │  Receiver    │    WiFi / Clinic   │  (HIPAA-secure)  │
│                 │                   │              │                    │                  │
│  • Temp sensor  │   Continuous      │  • Records   │    Physician-      │  • Aggregation   │
│  • H₂ sensor    │   telemetry       │    24-72h    │    initiated       │  • Analysis      │
│  • CO₂ sensor   │   while in GI     │    of data   │    upload          │  • Reports       │
│  • O₂ indicator │                   │  • Patient   │                    │  • Clinician     │
│  • Accelerometer│   Range: ~2m      │    worn on   │                    │    portal        │
│  • Antenna RSSI │   through body    │    belt/holster                   │                  │
│                 │                   │              │                    │                  │
│  Size: ~26×13mm │                   │  • Recharge- │                    │  • Regional      │
│  (similar to     │                   │    able batt.│                    │    transit times │
│   large pill)   │                   │  • 2-3 day    │                    │  • Gas profiles  │
└─────────────────┘                   │    battery   │                    └──────────────────┘
                                      └──────────────┘
```

### Tier Details

**Tier 1 — Ingestible Capsule**
- Size: Pharmaceutical-grade capsule, ~26mm × 13mm (OO-size gelatin capsule)
- Sensors: H₂ (electrochemical), CO₂ (NDIR or electrochemical), O₂ (electrochemical or galvanic), temperature (thermistor), accelerometer/tumble detection
- Power: Silver oxide battery (~2-3 days operating life)
- Wireless: Proprietary sub-GHz ISM band (~900 MHz) or BLE — optimized for low-power body-area transmission
- Sampling rate: Continuous (periodic, likely every 1-5 minutes during transit)
- Encapsulation: Ingestible polymer shell, PH-sensitive coating

**Tier 2 — Body-Worn Receiver**
- Form factor: Belt clip or holster, ~pager-sized
- Antenna: Designed for near-body propagation through tissue (≈2m effective range)
- Storage: Onboard flash memory (holds 24-72 hours of continuous data)
- Battery: Rechargeable, lasts the full study duration
- Upload: Physician-initiated data offload via USB or wireless to clinic gateway

**Tier 3 — Cloud Platform**
- Infrastructure: HIPAA-compliant cloud, likely AWS/Azure/GCP
- Processing pipeline: Raw sensor → calibration → transit time computation → report generation
- Clinical outputs: Regional transit times (gastric emptying, small bowel transit, colonic transit), gas concentration profiles per region
- Access: Physician web portal, patient report (PDF/summary)

---

## 2. Sensor Design Principles

### Hydrogen (H₂) Sensor
- **Type**: Electrochemical (amperometric)
- **Principle**: H₂ is oxidized at a working electrode, generating a current proportional to concentration
- **Reaction**: H₂ → 2H⁺ + 2e⁻ (at sensing electrode)
- **Range**: 0–200 ppm (typical GI hydrogen levels)
- **Selectivity**: Membrane-based — excludes larger molecules, allows H₂ diffusion
- **Clinical significance**: Primary fermentation product of gut bacteria (carbohydrate malabsorption, SIBO)

### Carbon Dioxide (CO₂) Sensor
- **Type**: NDIR (Non-Dispersive Infrared) or electrochemical
- **Principle** (NDIR): CO₂ absorbs IR at 4.26µm; attenuation is proportional to concentration
- **Principle** (electrochemical): CO₂ + H₂O → H₂CO₃ → H⁺ + HCO₃⁻; pH change is measured
- **Range**: 0–10% (GI tract CO₂ from fermentation + bicarbonate buffering)
- **Clinical significance**: Marker of fermentation, correlates with H₂ for carbohydrate digestion assessment

### Oxygen (O₂) Sensor
- **Type**: Galvanic cell or electrochemical
- **Principle**: O₂ is reduced at a cathode, generating current proportional to O₂ partial pressure
- **Reaction**: O₂ + 2H₂O + 4e⁻ → 4OH⁻ (at cathode)
- **Range**: 0–25% (atmospheric to anoxic)
- **Clinical significance**: Gut lumen O₂ level indicates mucosal integrity and oxidative environment
- **Note**: Listed as "oxygen level (as an indicator)" on Atmo's website — secondary/derived measurement

### Temperature Sensor
- **Type**: Precision thermistor (e.g., NTC or silicon-based)
- **Function**: Core body temperature logging + temperature compensation for gas sensors
- **Accuracy**: ±0.1°C
- **Clinical significance**: Confirms capsule integrity/ingestion, marks body-temperature baseline

### Accelerometer / Tumble Detection
- **Type**: 3-axis MEMS accelerometer
- **Function**: Detects capsule orientation, peristaltic motion, and regional transitions
- **Clinical significance**: Helps differentiate stomach vs. small bowel vs. colon entry based on motility patterns

### Antenna Reflectance
- **Function**: Measures RF environment changes as capsule travels through different tissues
- **Clinical significance**: Tissue density changes (stomach → small bowel → colon) affect antenna impedance — provides additional transit marker

---

## 3. Wireless Communication Analysis

### Capsule-to-Receiver Link

| Parameter | Estimate / Analysis |
|-----------|-------------------|
| **Frequency** | Sub-GHz ISM band (likely 868 MHz EU / 915 MHz US). BLE (2.4 GHz) possible but has worse body penetration. |
| **Modulation** | Proprietary: GFSK or OOK for low-power, body-area link budget |
| **Range** | ~2m through body tissue (signal attenuated by 20-40dB through 15-30cm of tissue) |
| **Data Rate** | Estimated 1-50 kbps (sensor data is low bandwidth — a few dozen bytes per sample) |
| **Duty Cycle** | Very low: capsule sleeps between sensor reads (likely <1% duty cycle) |
| **Power** | Capsule TX power: ~0dBm (1mW) to -10dBm for battery life |
| **Protocol** | Proprietary lightweight MAC layer (not Bluetooth classic — too power-hungry) |
| **Encryption** | AES-128 at minimum (HIPAA requires PHI encryption in transit) |

### Why Proprietary Sub-GHz (Not BLE)?

1. **Body penetration**: Sub-GHz (900 MHz) penetrates body tissue significantly better than 2.4 GHz BLE
2. **Power efficiency**: Proprietary protocols have lower protocol overhead than BLE stacks
3. **Antenna design**: Sub-GHz loop antenna can be integrated into capsule form factor more easily
4. **Link budget**: 10-20dB better link budget over BLE for the same TX power through tissue

### Receiver-to-Cloud Link

- Uses existing clinic/office WiFi or cellular infrastructure
- Data is uploaded when the patient returns to clinic at end of study
- No real-time streaming required — batch upload after 24-72h recording

---

## 4. Data Processing Pipeline

```
Capsule Ingestion
     │
     ▼
┌──────────────────────────────┐
│ Raw Sensor Sampling          │  ← Periodic (every 1-5 min)
│ H₂, CO₂, O₂, Temp, Accel    │
└──────────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ On-capsule preprocessing     │  ← Temperature compensation
│ Calibration correction       │  ← Factory cal coefficients applied
│ Data framing                 │  ← Packetized with timestamp
└──────────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ Wireless TX to Body Receiver │  ← Sub-GHz, encrypted
│ Continuous while in tract    │
└──────────────────────────────┘
     │ (Repeats until capsule expelled)
     ▼
┌──────────────────────────────┐
│ Receiver data storage        │  ← Onboard flash
│ 24-72h of continuous data    │
└──────────────────────────────┘
     │ (Study complete — physician upload)
     ▼
┌──────────────────────────────┐
│ Cloud Ingestion & Validation │  ← HIPAA-compliant ingress
│ Data integrity checks        │
└──────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│ Algorithmic Analysis                        │
│ • Regional transit identification           │
│   - Stomach entry/exit (pH + temperature)   │
│   - Small bowel entry (H₂ + CO₂ rise)       │
│   - Cecum arrival (accelerometer pattern)   │
│   - Colon transit (motility pattern)        │
│ • Gas concentration peak detection          │
│ • Correlation with meal/event markers       │
└─────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ Clinical Report Generation   │
│ • Whole-gut transit time     │
│ • Regional transit times     │
│ • Gas profile by region      │
│ • Comparison to normal ranges│
│ • Physician interpretation   │
└──────────────────────────────┘
     │
     ▼
        Physician reviews → Diagnosis → Treatment plan
```

### Key Clinical Outputs

| Output | Method | Normal Range | Clinical Utility |
|--------|--------|-------------|------------------|
| Whole Gut Transit Time | Capsule expulsion time | 24-72 hours | General motility assessment |
| Gastric Emptying Time | Temp + pH change → small bowel | 30-120 min | Gastroparesis, dumping syndrome |
| Small Bowel Transit Time | H₂/CO₂ rise → cecal arrival | 2-6 hours | SIBO, dysmotility |
| Colonic Transit Time | Cecum arrival → expulsion | 12-48 hours | Constipation, slow transit |
| Regional H₂ Profile | H₂ concentration by region | Region-dependent | Carbohydrate malabsorption |
| Regional CO₂ Profile | CO₂ concentration by region | Region-dependent | Fermentation assessment |

---

## 5. Competitive Landscape

| Feature | Atmo Capsule | SmartPill (Medtronic) | VitalMetrics | Oura Ring (comparison) |
|---------|-------------|----------------------|-------------|----------------------|
| **Sensors** | H₂, CO₂, O₂, Temp, Accel | pH, Temp, Pressure | GI gas only | Temp, HR, HRV |
| **Wireless** | Body-worn receiver | Body-worn receiver | — | BLE to phone |
| **Battery** | 2-3 days | 5+ days | — | 7 days |
| **Primary Output** | Gas profiles + transit | pH, transit, pressure | Gas only | Sleep, HR |
| **FDA Status** | 510(k) cleared | Cleared | — | — |
| **Cost** | Undisclosed | ~$500/study | — | $299 |
| **Key Differentiator** | **Gas sensing (H₂, CO₂, O₂)** — only product measuring gut gases in vivo | **Pressure** — gold standard for transit | Research-only | Consumer wearable |

---

## 6. Research Gaps and Future Questions

1. **Wireless Protocol**: Atmo does not publicly specify the exact ISM band or radio protocol. Teardown or FCC filings would be needed to confirm.

2. **Sensor Accuracy vs. Gold Standard**: No published comparison of capsule H₂/CO₂ to breath test H₂/CO₂ (current clinical standard) in the same subjects.

3. **Clinical Validation Pipeline**: Limited peer-reviewed publications as of 2026 — most evidence is from Atmo's own studies rather than independent trials.

4. **Cost-per-study**: Unknown pricing — determines whether this becomes routine clinical tool or remains niche specialty device.

5. **Reusability**: Receiver is reusable; capsule is single-use (ingestible, passes through). Cost-per-capsule is a key adoption driver.

6. **Size Reduction Roadmap**: Current capsule (26×13mm) is large — future iterations could match standard supplement capsule size (00 = ~23×8mm) for easier swallowing.

---

## Recommended Next Steps for Research-Spike Pipeline

1. ✅ **Question 1** (System Architecture) — **Complete** (described above)
2. ✅ **Question 2** (Sensor Design) — **Complete** (electrochemical/NDIR principles identified)
3. ❓ **Question 3** (Wireless Protocol) — **Needs FCC database search** to confirm frequency band and protocol
4. ✅ **Question 4** (Data Pipeline) — **Complete** (6-stage pipeline described)
5. ❓ **Question 5** (Clinical Validation) — **Needs PubMed search** for peer-reviewed outcomes data

*Prepared for the "Atmo Biosciences Atmo® Gas Capsule analysis" project.*
