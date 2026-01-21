# Datasheet Ingestion System

Automatically extract RF component specifications from datasheets using Ollama AI.

## Overview

Upload a PDF datasheet or provide a URL, and VetRender will:
1. Download/process the datasheet
2. Send it to Ollama with component-specific extraction prompts
3. Return structured JSON with extracted specifications
4. Allow you to review/edit before saving
5. Store the component in your local library

## Supported Component Types

- **Cables**: Coaxial transmission line (loss tables, power ratings, VF)
- **Transmitters**: FM/AM/VHF/UHF transmitters (power, efficiency, harmonics)
- **Antennas**: Gain, pattern, polarization, VSWR
- **Lightning Arrestors**: Insertion loss, voltage rating, DC pass/block
- **Isolators/Circulators**: Insertion loss, isolation, power rating
- **Combiners**: Multi-port, isolation, insertion loss
- **Filters**: Passband, stopband, rejection, insertion loss
- **Connectors**: Insertion loss, VSWR, mating types
- **Generic**: Any RF component (auto-detects type)

## Usage (Future UI)

### Option 1: Upload PDF
```
1. Click "Add Component" → "Import from Datasheet"
2. Select PDF file from computer
3. Ollama processes and extracts specs
4. Review extracted data in form
5. Edit any incorrect/missing fields
6. Click "Save to Library"
```

### Option 2: URL
```
1. Click "Add Component" → "Import from URL"
2. Paste datasheet URL (manufacturer website, etc.)
3. VetRender downloads PDF
4. Ollama extracts specs
5. Review and save
```

### Option 3: Drag & Drop
```
1. Drag PDF file onto component library window
2. Auto-detect component type
3. Extract and present for review
4. Save to library
```

## How It Works

### Step 1: Component Type Detection
Ollama analyzes the first page to determine component type:
- "FM Transmitter" → use transmitter prompt
- "Coaxial Cable" → use cable prompt
- "Antenna" → use antenna prompt
- Unknown → use generic prompt

### Step 2: Specification Extraction
Component-specific prompt sent to Ollama:
```python
prompt = load_prompt("cable")  # or transmitter, antenna, etc.
datasheet_text = extract_text_from_pdf(pdf_file)
response = ollama.generate(
    model="llama3.2",  # or your preferred model
    system=prompt["system_prompt"],
    prompt=prompt["user_prompt"] + "\n\nDatasheet content:\n" + datasheet_text
)
component_json = parse_json(response)
```

### Step 3: Validation & Unit Conversion
```python
# Validate extracted data
if component_json["component_type"] == "cable":
    assert 0.6 <= component_json["velocity_factor"] <= 0.95
    assert component_json["impedance_ohms"] in [50, 75]

# Convert units if needed
if "db_per_meter" in datasheet:
    db_per_100ft = db_per_meter * 30.48
```

### Step 4: User Review
Present extracted data in editable form:
```
┌─────────────────────────────────────────┐
│ Extracted Component Specifications      │
├─────────────────────────────────────────┤
│ Component Type: [Cable            ▼]    │
│ Manufacturer:   [Andrew/CommScope  ]    │
│ Model:          [LDF4-50A          ]    │
│ Part Number:    [LDF4-50A          ]    │
│                                          │
│ ✓ Impedance:    50 ohms                 │
│ ✓ VF:           0.88                    │
│ ⚠ Loss @ 150MHz: [0.51] dB/100ft       │
│ ✗ Bend Radius:  [      ] (not found)   │
│                                          │
│ [Edit All Fields] [Save] [Discard]      │
└─────────────────────────────────────────┘
```

### Step 5: Save to Library
```python
component_data = {
    "source": "datasheet_ingestion",
    "datasheet_file": "path/to/LDF4-50A_datasheet.pdf",
    "date_added": "2026-01-19",
    "extracted_by": "ollama:llama3.2",
    "user_verified": True,
    ...component_specs
}

save_to_cache(component_data)
```

## Ollama Model Recommendations

### Best Models for Datasheet Extraction:

1. **llama3.2** (Recommended)
   - Good balance of speed and accuracy
   - Handles technical documents well
   - Fast enough for real-time processing

2. **llama3.1:70b** (High accuracy)
   - Best accuracy for complex datasheets
   - Slower but more reliable extraction
   - Use for critical components

3. **mistral** (Fast)
   - Quick processing
   - Good for simple datasheets
   - May miss subtle details

4. **qwen2.5:14b** (Technical)
   - Strong with technical/engineering docs
   - Good number recognition
   - Handles tables well

## Example: Cable Datasheet Extraction

**Input PDF:** Andrew LDF4-50A datasheet

**Ollama Extraction:**
```json
{
  "component_type": "cable",
  "manufacturer": "Andrew / CommScope",
  "model": "LDF4-50A",
  "part_number": "LDF4-50A",
  "description": "1/2\" HELIAX foam dielectric coaxial cable",
  "impedance_ohms": 50,
  "velocity_factor": 0.88,
  "outer_diameter_inches": 0.630,
  "loss_db_per_100ft": {
    "50": 0.27,
    "150": 0.51,
    "450": 0.93,
    "900": 1.36,
    "1800": 2.00
  },
  "power_rating_watts": {
    "50_mhz": 3800,
    "150_mhz": 3200,
    "450_mhz": 2000,
    "900_mhz": 1400
  },
  "weight_lbs_per_100ft": 13.6,
  "minimum_bend_radius_inches": 5.0,
  "datasheet_url": null,
  "common_uses": [
    "VHF/UHF repeater feedline",
    "Base station",
    "Tower runs"
  ],
  "notes": "Industry standard 1/2\" coax, good balance of loss and flexibility"
}
```

**User reviews, confirms, saves to library.**

## Technical Implementation

### PDF Text Extraction
```python
import PyPDF2

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text
```

### Ollama API Call
```python
import requests

def extract_specs_from_datasheet(pdf_path, component_type="generic"):
    # Load appropriate prompt
    with open("datasheet_ingestion_prompts.json") as f:
        prompts = json.load(f)

    prompt_config = prompts["prompts"].get(component_type, prompts["prompts"]["generic"])

    # Extract text from PDF
    datasheet_text = extract_text_from_pdf(pdf_path)

    # Call Ollama
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3.2",
        "prompt": prompt_config["user_prompt"] + "\n\nDatasheet:\n" + datasheet_text,
        "system": prompt_config["system_prompt"],
        "stream": False,
        "format": "json"  # Force JSON output
    })

    result = response.json()
    component_specs = json.loads(result["response"])

    return component_specs
```

### Validation
```python
def validate_component(component_data):
    component_type = component_data["component_type"]

    if component_type == "cable":
        assert 0.6 <= component_data.get("velocity_factor", 0.8) <= 0.95
        assert component_data.get("impedance_ohms") in [50, 75]
        # Check loss increases with frequency
        losses = component_data.get("loss_db_per_100ft", {})
        freqs = sorted([int(f) for f in losses.keys()])
        for i in range(len(freqs)-1):
            assert losses[str(freqs[i])] <= losses[str(freqs[i+1])]

    elif component_type == "transmitter":
        assert component_data.get("power_output_watts", 0) > 0
        efficiency = component_data.get("efficiency_percent", 50)
        assert 30 <= efficiency <= 85

    return True
```

## Error Handling

### Common Issues:

1. **Poor PDF quality** → OCR may fail
   - Solution: Use higher quality datasheets

2. **Table extraction errors** → Numbers misread
   - Solution: User reviews and corrects

3. **Missing specifications** → Not in datasheet
   - Solution: Fields left null, user can fill manually

4. **Wrong component type** → Auto-detection failed
   - Solution: User selects correct type, re-process

## Future Enhancements

1. **Batch Processing**: Upload multiple datasheets at once
2. **OCR for Scanned PDFs**: Handle image-based PDFs
3. **Web Scraping**: Auto-find datasheets from manufacturer websites
4. **Community Database**: Share extracted components with other users
5. **Confidence Scoring**: Ollama reports confidence in extracted values
6. **Auto-Update**: Re-scan datasheets when new versions released

## File Storage

```
components/
├── datasheets/
│   ├── cables/
│   │   ├── LDF4-50A_datasheet.pdf
│   │   └── LMR-400_datasheet.pdf
│   ├── transmitters/
│   │   ├── TX1000_V5_datasheet.pdf
│   │   └── FAX250_datasheet.pdf
│   └── pending/
│       └── unknown_component.pdf
│
└── cache/
    └── component_cache.json  # Extracted components stored here
```

## Performance

**Typical extraction times:**
- Small datasheet (2-5 pages): 5-15 seconds
- Medium datasheet (10-20 pages): 20-40 seconds
- Large datasheet (50+ pages): 60-120 seconds

**Accuracy:**
- Simple specs (model, manufacturer): 95%+
- Numeric specs (power, loss): 85-90%
- Complex tables: 70-80%
- **Always requires user review**

## Privacy & Security

- All processing happens **locally** (Ollama runs on your machine)
- Datasheets stored **locally** in components/datasheets/
- No data sent to cloud services
- No manufacturer API calls
- Complete privacy for proprietary/NDA'd components
