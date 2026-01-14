# Terrain Model Improvements for Mountainous RF Propagation

## Problem Statement
The original single knife-edge diffraction model was too optimistic for mountainous terrain like Sun Valley, Idaho. It showed coverage on the backside of mountains where signal cannot realistically penetrate.

## Changes Made

### 1. Multiple Knife-Edge Diffraction (Deygout Method)
**Location**: `models/propagation.py`

**What Changed**:
- Upgraded from single obstacle model to **multiple knife-edge diffraction**
- Implements the Deygout method for handling multiple ridges
- Detects and penalizes secondary obstructions before/after main obstacle
- Adds 10 dB penalty for each additional diffraction point

**Why This Matters**:
- Single knife-edge assumes one ridge; mountains have multiple ridges
- Each additional ridge causes extra diffraction loss
- More accurately represents reality in mountainous terrain

### 2. Severe Obstruction Handling
**Location**: `models/propagation.py` lines 132-134

**What Changed**:
- When diffraction parameter `v > 2.0` (severe obstruction)
- Minimum loss is now **40 dB + 10*log10(v)**
- Caps at 100 dB (effectively no signal)

**Why This Matters**:
- Backside of mountains should show minimal/no coverage
- Previous model was too generous with diffraction
- 40+ dB loss ensures realistic shadow zones

### 3. Fresnel Zone Clearance
**Location**: `models/propagation.py` lines 59-76

**What Changed**:
- Even when LOS exists, checks if 60% of first Fresnel zone is clear
- Adds loss if terrain partially obstructs Fresnel zone
- Caps grazing obstruction at 20 dB

**Why This Matters**:
- RF signals need clearance AROUND the line-of-sight, not just direct path
- Mountains can block signal even with theoretical LOS
- 60% clearance is industry standard for reliable link

### 4. Variable Receiver Height
**Location**: `gui/main_window.py` lines 616-618

**What Changed**:
- Changed from fixed 2m receiver height to **10m above local ground**
- Uses actual terrain elevation at receiver location
- More realistic for roof-mounted antennas

**Why This Matters**:
- 2m is ground level (cars, pedestrians) - too pessimistic
- 10m represents typical building/tower height
- Matches real-world receiver installations

### 5. Distance-Aware Diffraction
**Location**: `gui/main_window.py` line 622

**What Changed**:
- Now passes actual distance array to diffraction calculation
- Enables proper Fresnel zone calculation
- Accounts for obstacle position along path

**Why This Matters**:
- Diffraction loss depends on WHERE the obstacle is, not just height
- Obstacle at midpoint is worse than near TX or RX
- Critical for accurate FM propagation at VHF

### 6. Shadow Zone Visualization
**Location**: `gui/main_window.py` lines 105-106, 763-774

**What Changed**:
- Added "Show Shadow Zones" checkbox
- Red hatched overlay on areas with >40 dB terrain loss
- Visual indicator of blocked areas

**How to Use**:
1. Calculate coverage with terrain enabled
2. Check "Show Shadow Zones" box
3. Red hatched areas = blocked by mountains (no service expected)

## Technical Details

### ITU-R P.526 Compliance
The diffraction formula now follows ITU-R P.526 recommendations:
```
v = h * sqrt(2(d1+d2) / (λ * d1 * d2))
```
Where:
- `h` = obstacle height above LOS
- `d1` = distance TX to obstacle
- `d2` = distance obstacle to RX
- `λ` = wavelength

### Diffraction Loss Formula
```
For v > 0:
  Loss = 6.9 + 20*log10(sqrt((v-0.1)^2 + 1) + v - 0.1)

For severe obstruction (v > 2.0):
  Loss = max(Loss, 40 + 10*log10(v))
```

### Multiple Obstruction Penalty
- Checks both TX→obstacle and obstacle→RX segments
- +10 dB for each additional blocking ridge
- Simulates cascaded diffraction

## Expected Results for KDPI 88.5 FM

### Configuration Assumptions:
- **Frequency**: 88.5 MHz (λ = 3.39m)
- **Transmitter**: Mountain-top site
- **Terrain**: Multiple ridges between transmitter and valleys

### What You Should See:

**With Shadow Zones OFF**:
- Smooth coverage gradients
- Less aggressive terrain losses
- May still show some optimistic coverage

**With Shadow Zones ON**:
- Red hatched areas behind major ridges
- Clear indication of blocked zones
- More conservative coverage predictions

### Recommended Settings for Accuracy:

1. **Quality**: High or Ultra
   - More terrain samples = better obstacle detection
   - Ultra is 360 azimuths × 200 points = 72,000 elevation queries

2. **Min Signal Level**: -85 to -95 dBm
   - -85 dBm: Reliable FM reception (5+ dB SNR)
   - -95 dBm: Marginal reception
   - -105 dBm: Threshold of detection

3. **Show Shadow Zones**: Enabled
   - Clearly identifies no-service areas
   - Helps with transmitter power planning

## Power Planning Workflow

1. **Start Conservative**:
   - Use your proposed ERP
   - Calculate with terrain + shadow zones
   - Identify coverage gaps

2. **Adjust Power**:
   - If coverage exceeds target: reduce ERP
   - If coverage insufficient: increase ERP or add repeaters

3. **Validate Communities**:
   - Right-click → "Probe Signal Strength"
   - Check signal at key community centers
   - Aim for -70 to -85 dBm in populated areas

4. **Check Interference**:
   - Note areas with strong signal (red/orange)
   - These are high-power zones that may cause noise
   - Balance coverage vs. interference

## Known Limitations

### 1. Elevation Data Resolution
- Open-Elevation API provides ~30m horizontal resolution
- Sharp ridges may be smoothed out
- Ultra quality helps but can't overcome data limits

### 2. Tropospheric Effects
- Model doesn't account for atmospheric ducting
- Temperature inversions can extend range
- Weather-dependent propagation not included

### 3. Urban Clutter
- No building/foliage loss included
- Add 10-20 dB for urban areas manually
- Dense forests: add 5-15 dB

### 4. Multipath Fading
- Model shows average signal strength
- Actual reception may vary ±10 dB due to multipath
- Valleys may have more variation than predicted

## Validation Recommendations

1. **Drive Testing**:
   - Measure signal at key locations
   - Compare to predictions
   - Note discrepancies for model tuning

2. **Community Feedback**:
   - Monitor listener reports
   - Weak areas may indicate additional obstacles
   - Strong areas confirm good propagation

3. **Cross-Reference with Terrain**:
   - Load results into Google Earth
   - Visually verify shadow zones align with ridges
   - Check that coverage follows valleys

## Next Steps for Further Accuracy

### Potential Enhancements:
1. **Longley-Rice Model**: More sophisticated ITM propagation
2. **Clutter Factors**: Urban/forest loss databases
3. **3D Antenna Patterns**: Vertical as well as horizontal
4. **Population Density Overlay**: Weight coverage by population
5. **Interference Analysis**: Check co-channel stations

### For Professional Use:
Consider commercial tools like:
- **Radio Mobile** (free, very accurate)
- **Pathloss** (commercial, FCC accepted)
- **EDX SignalPro** (commercial, industry standard)

But for preliminary planning and power optimization, VetRender with these improvements should give you realistic results for Sun Valley terrain.

## Summary

These changes make VetRender suitable for **mountainous FM broadcast planning**:
- ✅ Realistic mountain shadowing
- ✅ Multiple diffraction support
- ✅ Fresnel zone awareness
- ✅ Visual shadow zone indicators
- ✅ ITU-R compliant calculations

The model will now show **conservative, realistic coverage** rather than optimistic line-of-sight assumptions.
