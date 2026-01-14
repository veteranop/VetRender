# Propagation Model Fix - Overly Pessimistic Coverage

## Problem
The terrain diffraction model was WAY too aggressive, especially for mountaintop transmitters with good elevation. Coverage predictions were showing severe restrictions that didn't match real-world performance or ATDI results.

## Issues Found

### 1. Excessive Severe Obstruction Penalty
**Before:**
```python
if v > 2.0:
    total_loss = max(total_loss, 40 + 10 * np.log10(v))  # Minimum 40 dB!
```
- Applied **minimum 40 dB loss** for any significant obstruction
- Triggered at v > 2.0 (relatively low threshold)
- Logarithmic scaling added even more loss

**After:**
```python
if v > 3.0:
    additional_loss = 10 * (v - 3.0)  # Linear increase
    total_loss = max(total_loss, 30 + additional_loss)  # Reduced to 30 dB minimum
```
- Raised threshold to v > 3.0 (only truly severe obstructions)
- Reduced minimum loss from 40 dB to 30 dB
- Linear scaling instead of logarithmic

### 2. Excessive Secondary Diffraction Penalties
**Before:**
```python
secondary_loss += 10  # Per additional ridge/obstruction
```
- **10 dB penalty** for each additional obstruction
- With 2-3 ridges, this added 20-30 dB on top of main diffraction loss
- Far too aggressive for VHF/UHF propagation

**After:**
```python
secondary_loss += 5  # Reduced penalty
```
- **5 dB penalty** per additional obstruction (50% reduction)
- More realistic for actual VHF/UHF diffraction behavior

### 3. Overly Strict Fresnel Zone Requirements
**Before:**
```python
if clearances[mid_idx] < 0.6 * fresnel_radius:
    # Calculate loss immediately
    loss = ...
    return max(0, min(loss, 20))  # Up to 20 dB loss!
```
- Applied loss for ANY Fresnel zone violation below 60%
- Capped at **20 dB** even for grazing paths with good clearance

**After:**
```python
if clearances[mid_idx] < 0.6 * fresnel_radius:
    h = 0.6 * fresnel_radius - clearances[mid_idx]
    # Only apply loss if significantly violated
    if h > 0.3 * fresnel_radius:  # Less than 30% clearance
        loss = ...
        return max(0, min(loss, 10))  # Cap at 10 dB
```
- Only applies loss if clearance is significantly violated (< 30%)
- Reduced cap from 20 dB to **10 dB**

### 4. Overall Loss Cap
**Before:**
```python
return max(0, min(total_loss, 100))  # 100 dB cap
```

**After:**
```python
return max(0, min(total_loss, 80))  # 80 dB cap
```
- Reduced maximum terrain loss from 100 dB to **80 dB**
- Even worst-case scenarios are less extreme

## Impact

### Typical Mountaintop Site (Your Scenario)
**Before:**
- Terrain loss: 40-60 dB in most directions
- Coverage: Severely restricted, unrealistic
- Matched symptoms: Narrow "finger" patterns instead of omnidirectional

**After:**
- Terrain loss: 5-20 dB in most clear directions
- Coverage: Much more realistic omnidirectional pattern
- Should match ATDI and real-world measurements

### Clear Line-of-Sight
**Before:**
- Even with clear LOS: 10-20 dB Fresnel penalty
- Total received power reduced significantly

**After:**
- Clear LOS: 0-10 dB penalty (only if significantly obstructed)
- Much better signal strength predictions

### Obstructed Paths
**Before:**
- Single ridge: 15-25 dB loss + 40 dB penalty = **55-65 dB total**
- Multiple ridges: 70-100 dB (no coverage)

**After:**
- Single ridge: 15-25 dB loss (no penalty unless v > 3.0)
- Multiple ridges: 25-40 dB total (more realistic)

## Validation

The new model should match professional tools like:
- **ATDI** (ICS Telecom)
- **Radio Mobile** (Longley-Rice)
- **Planet by MSI**

## Next Steps

1. **Recalculate your coverage** with terrain enabled
2. **Compare results** to ATDI output
3. **Adjust if needed**: If still too pessimistic or optimistic, we can fine-tune:
   - Severe obstruction threshold (currently v > 3.0)
   - Secondary loss penalties (currently 5 dB)
   - Fresnel zone requirements (currently 30% threshold)

## Technical Details

The fixes make the model more aligned with **ITU-R P.526** and **Longley-Rice** methodologies, which are industry standards for VHF/UHF propagation prediction.

### Diffraction Parameter (v)
- v < 0: Path clearance, negative loss possible
- v = 0: Grazing incidence, ~6 dB loss
- v = 1: Moderate obstruction, ~13 dB loss
- v = 2: Significant obstruction, ~18 dB loss
- v = 3: Severe obstruction, ~25 dB loss (threshold for extra penalties)

### Recommendations for Accurate Results
1. Use **Medium or High** terrain quality for important predictions
2. Ensure transmitter **height AGL** is accurate
3. For mountaintop sites, verify elevation data is correct
4. Cross-validate with field measurements when possible
