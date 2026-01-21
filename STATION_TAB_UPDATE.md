# Station Tab Implementation - Complete

## Changes Made

### 1. Added Tabbed Interface to Main Window
**File: gui/main_window.py**

- Replaced single-pane layout with ttk.Notebook (tabbed interface)
- Created two tabs:
  - **Coverage Tab**: Original map display and coverage calculation (existing functionality)
  - **Station Tab**: New RF chain builder interface

### 2. Built Station Tab with RF Chain Builder
**File: gui/main_window.py - setup_station_tab()**

The Station tab includes:

#### Component Search Section
- Type filter dropdown (all, cable, connector, isolator, etc.)
- Text search box (searches model, part number, description)
- **AI Search (Ollama) button** - NEW: Query AI for unknown components
- Results listbox showing matching components from catalogs and cache

#### RF Chain Display
- Treeview showing RF chain from transmitter to antenna
- Columns: Component | Type | Length (ft) | Loss (dB) | Gain (dB)
- Drag controls: Move Up, Move Down, Remove, Clear All
- Length input field for cables (in feet)
- Add to Chain button

#### System Totals
- Real-time calculation of:
  - Total Loss (dB) - red text
  - Total Gain (dB) - green text
  - Net Change (dB) - color-coded (red=loss, green=gain)
- Apply to Station button - saves RF chain to project config

### 3. Added Ollama AI Integration
**File: models/component_library.py - ollama_search_component()**

New AI-powered component lookup:
- Queries Ollama API (localhost:11434) with llama3.2 model
- Constructs detailed prompt requesting component specifications
- Parses JSON response with full component details:
  - Cable loss curves at multiple frequencies
  - Insertion loss for passive components
  - Gain for amplifiers/antennas
  - Power ratings, connectors, frequency ranges
- Auto-caches results for future searches
- Error handling for connection issues, timeouts, invalid responses

### 4. Component Library Integration

Pre-loaded catalogs (11 manufacturers):
- Andrew/CommScope (Heliax coax)
- Times Microwave (LMR flexible coax)
- PolyPhaser (lightning protection)
- Decibel Products (VHF/UHF antennas)
- Bird Technologies (isolators, combiners)
- BW Broadcast (transmitters)
- Harris Broadcast (transmitters)
- Jampro (antennas)
- RELL (antennas)
- Shively Labs (antennas)
- Manufacturers database

### 5. RF Chain Calculation Methods

New methods in gui/main_window.py:
- `_search_components()` - Search catalog and cache
- `_ollama_search()` - AI-powered component lookup with progress dialog
- `_add_to_chain()` - Add component to RF chain
- `_remove_component()` - Remove selected component
- `_move_up()` / `_move_down()` - Reorder chain
- `_clear_chain()` - Clear entire chain
- `_update_chain_display()` - Refresh treeview
- `_calculate_totals()` - Calculate system loss/gain
- `_apply_station_changes()` - Save RF chain to project config

## How It Works

### Local Catalog Search
1. User types component name (e.g., "LMR-400")
2. Search runs through all catalogs and cache
3. Results populate instantly (no internet required)
4. Click component and "Add to Chain"

### AI Component Lookup
1. User enters unknown component (e.g., "Belden 9913")
2. Clicks "AI Search (Ollama)" button
3. Progress dialog shows while querying Ollama
4. Ollama returns component specifications in JSON format
5. Component auto-added to cache for future searches
6. Search results refresh to show new component

### RF Chain Building
1. Add components in sequence: TX → Cable → Connector → Isolator → Combiner → Cable → Antenna
2. Specify cable lengths in feet
3. System auto-calculates:
   - Cable loss (interpolated at operating frequency)
   - Insertion losses from connectors, isolators, etc.
   - Antenna gain
   - Net system change (gain - loss)
4. Click "Apply to Station" to update project ERP
5. RF chain saves to .vetrender_config.json

## Technical Details

### Frequency Interpolation
Cable loss is stored at specific frequencies (50, 150, 220, 450 MHz, etc.)
VetRender interpolates linearly for your exact frequency.

Example for LMR-400 at 156 MHz:
- Known: 150 MHz = 1.8 dB/100ft, 220 MHz = 2.2 dB/100ft
- Interpolated: 156 MHz ≈ 1.84 dB/100ft
- 200ft run = 3.68 dB loss

### Ollama API Integration
- Endpoint: http://localhost:11434/api/generate
- Model: llama3.2 (can be configured)
- Timeout: 30 seconds
- Format: JSON response enforced
- Background threading prevents GUI freeze

### Cache System
Component cache at: `components/cache/component_cache.json`
- All Ollama lookups auto-saved
- Persists between sessions
- Manual components can be added
- Searchable alongside manufacturer catalogs

## Usage Example

### Building a Station RF Chain

1. **Navigate to Station Tab**
   - Click "Station" tab at top

2. **Add Transmitter to Cable**
   - Search: "LMR-400"
   - Select "LMR-400 - Low loss flexible coax (Times Microwave)"
   - Length: 200 ft
   - Click "Add to Chain"
   - Shows: 3.68 dB loss @ 156 MHz

3. **Add Lightning Arrestor**
   - Search: "IS-B50LN"
   - Select "IS-B50LN-C0 - Bulkhead lightning arrestor (PolyPhaser)"
   - Click "Add to Chain"
   - Shows: 0.2 dB insertion loss

4. **Add Antenna**
   - Search: "DB224"
   - Select "DB224 - VHF high gain antenna (Decibel Products)"
   - Click "Add to Chain"
   - Shows: 10 dBi gain

5. **Review System Totals**
   - Total Loss: 3.88 dB
   - Total Gain: 10.00 dB
   - Net Change: +6.12 dB

6. **Apply to Station**
   - Click "Apply to Station"
   - ERP updated with +6.12 dB system change
   - RF chain saved to project

### Using AI Search (Ollama)

If component not in catalogs:
1. Search: "Belden 9913"
2. Click "AI Search (Ollama)"
3. Wait for Ollama to query (5-30 seconds)
4. Component specifications returned and cached
5. Now searchable like any catalog component

## Requirements

- **Ollama** must be installed and running for AI search
  - Install: https://ollama.com
  - Run: `ollama serve`
  - Pull model: `ollama pull llama3.2`
- **requests** library (already in requirements.txt)
- No changes needed to existing code - fully backward compatible

## Benefits

1. **Accurate System Loss Budget** - Real component specs at your frequency
2. **Fast Component Lookup** - 50+ components pre-loaded, searchable instantly
3. **AI-Powered Unknown Components** - Ollama fills gaps in catalog
4. **Persistent Cache** - Ollama results saved for future use
5. **Visual RF Chain** - See entire TX→Antenna path at a glance
6. **Frequency-Specific** - Cable loss interpolated to your exact frequency
7. **Auto-Save** - RF chain saved to project config
8. **Tab Interface** - Clean separation of Coverage vs Station configuration

## Next Steps

User can now:
- ✅ Add Station tab (COMPLETE)
- ✅ Enable Ollama integration (COMPLETE)
- ✅ Make components clickable/addable (COMPLETE)
- Build complete RF chains with real component specs
- Get accurate ERP calculations including feedline losses
- Use AI to find unknown components
- Save station configurations to projects
