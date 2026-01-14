# KDPI 88.5 FM - Quick Start Guide

## Your Setup
- **Station**: KDPI 88.5 FM
- **Location**: Mountain near Sun Valley, Idaho
- **Goal**: Minimum power for community coverage, reduce noise on hill
- **Challenge**: Mountainous terrain with multiple ridges

## Step-by-Step Workflow

### 1. Initial Setup
```
Location: 43.661474, -114.403802 (your mountain site)
Frequency: 88.5 MHz
Antenna Height: [your tower height in meters]
Starting ERP: [your current power in dBm]
```

### 2. First Coverage Calculation
**Settings**:
- Quality: **High** (good balance of speed vs. accuracy)
- Use Terrain: ✅ **Enabled**
- Show Shadow Zones: ✅ **Enabled**
- Min Signal Level: **-85 dBm** (reliable FM reception)
- Max Distance: **50-75 km** (adjust for your service area)

**Click**: "Calculate Coverage"

### 3. Interpret Results

#### Color Zones:
- 🔴 **Red**: Strong signal (-50 to -70 dBm) - may cause noise issues
- 🟡 **Yellow/Orange**: Good signal (-70 to -85 dBm) - target for communities
- 🟢 **Green**: Fair signal (-85 to -95 dBm) - marginal coverage
- 🔵 **Blue/Cyan**: Weak signal (-95 to -110 dBm) - unreliable
- ⬜ **White/Missing**: No coverage (< min signal level)

#### Shadow Zones:
- **Red Hatching (///)**: Blocked by mountains (>40 dB terrain loss)
- These areas will NOT receive signal regardless of power
- Don't waste power trying to reach them - consider repeaters instead

### 4. Check Target Communities

**For each community**:
1. Right-click on the town center
2. Select "Probe Signal Strength Here"
3. Note the signal level

**Target Values**:
- **Ideal**: -70 to -80 dBm (excellent reception)
- **Acceptable**: -80 to -90 dBm (good reception)
- **Marginal**: -90 to -95 dBm (weak but usable)
- **Poor**: < -95 dBm (unreliable)

### 5. Power Optimization

#### If Coverage is Too Large:
- Strong signal on the populated hill? **Reduce ERP**
- Right-click → "Edit Transmitter Configuration"
- Lower ERP by 3 dB steps
- Recalculate and check communities again

#### If Coverage is Too Small:
- Communities not reaching -90 dBm? **Increase ERP**
- Raise ERP by 3 dB steps
- Watch for shadow zones - power won't help there

#### Power vs. Coverage Rules:
```
+3 dB ERP = ~1.4x coverage radius = 2x power consumption
+6 dB ERP = ~2x coverage radius = 4x power consumption
+10 dB ERP = ~3x coverage radius = 10x power consumption
```

### 6. Noise Reduction on Hill

**Problem**: Strong signal on populated mountain area

**Solution**:
1. Check signal levels near your transmitter site
2. If showing -50 to -60 dBm in residential areas:
   - This may cause interference with electronics
   - Consider directional antenna pointing AWAY from hill
   - Or reduce ERP and add valley-fill repeater

**Antenna Pattern Options**:
- **Omnidirectional**: Covers all directions equally (current default)
- **Directional**: Focus power toward valleys, reduce toward hill
- Load XML antenna pattern file with your actual pattern

### 7. Advanced Optimization

#### Ultra Quality Calculation:
- Use for final verification
- 360 azimuths × 200 points = very slow but very accurate
- Run overnight if needed

#### Min Signal Level Tuning:
- **-80 dBm**: Show only strong coverage (regulatory minimum)
- **-90 dBm**: Show good service area (typical planning)
- **-100 dBm**: Show all detectable signal (interference analysis)

#### Zoom for Detail:
- Calculate coverage
- **Scroll wheel** to zoom on specific towns
- Verify signal gradients
- Plot stays aligned with map

### 8. Documentation for FCC

**Export Your Analysis**:
1. Take screenshots with:
   - Shadow zones visible
   - Key communities labeled
   - Signal strength color bar

2. Note for each target community:
   - Lat/Lon (from probe tool)
   - Distance from transmitter
   - Predicted signal strength
   - Terrain loss

3. **Print to Console**:
   - All calculations logged to terminal
   - Copy/paste for records
   - Shows exact parameters used

## Typical Sun Valley Scenario

### Expected Results:
```
Transmitter: Mountain peak
ERP: 40 dBm (10W) typical for LPFM

Target Communities:
- Ketchum/Sun Valley: -75 dBm (good)
- Hailey: -85 dBm (acceptable)
- Bellevue: -90 dBm (marginal)

Shadow Zones:
- East of mountain: blocked by ridge
- Specific valleys: need repeater
```

### Power Recommendations:
- **Start**: 40 dBm (10W ERP)
- **If Ketchum too weak**: 43 dBm (20W ERP)
- **If hill noise issue**: 37 dBm (5W ERP) + directional

## Troubleshooting

### "Coverage looks too optimistic"
✅ **Enable**: Show Shadow Zones
✅ **Increase**: Quality to High or Ultra
✅ **Lower**: Min Signal Level to -85 dBm (realistic threshold)

### "Coverage looks too pessimistic"
❌ **Check**: Is terrain enabled? (should be)
❌ **Check**: Antenna height correct? (add tower height)
❌ **Check**: ERP in dBm not watts (40 dBm = 10W)

### "Shadow zones not showing"
- Only visible after terrain calculation completes
- Must check "Show Shadow Zones" checkbox
- Need terrain loss >40 dB to display

### "Calculation is slow"
- **High quality**: ~2-5 minutes (72 azimuths × 50 points = 3,600 queries)
- **Ultra quality**: ~10-30 minutes (360 azimuths × 200 points = 72,000 queries)
- Uses cached terrain data after first run
- Worth the wait for accuracy

## Quick Keyboard Reference
- **Right-click**: Context menu (set TX, probe signal, config)
- **Scroll wheel**: Zoom in/out on map
- **Calculate Coverage**: Run propagation model
- **Reset Location**: Start over with new area

## Questions to Answer

Before finalizing your power:

1. ✅ Are all target communities above -90 dBm?
2. ✅ Are residential areas near TX below -60 dBm?
3. ✅ Are shadow zones documented and acceptable?
4. ✅ Can you reduce power without losing coverage?
5. ✅ Do you need directional antenna to reduce hill noise?

## Final Checklist

- [ ] Correct frequency (88.5 MHz)
- [ ] Correct location (verified on map)
- [ ] Correct antenna height (meters above ground)
- [ ] Terrain enabled
- [ ] Shadow zones shown
- [ ] High or Ultra quality
- [ ] Min signal level = -85 to -90 dBm
- [ ] All communities checked with probe tool
- [ ] ERP optimized (lowest power for coverage)
- [ ] Screenshots saved
- [ ] Console output copied for records

## Need Help?
Check these files:
- `TERRAIN_IMPROVEMENTS.md` - Technical details on diffraction model
- `CHANGES.md` - All recent feature updates
- Console output - Shows all calculation parameters

Good luck with KDPI! The improved terrain model should give you realistic coverage predictions for your power planning.
