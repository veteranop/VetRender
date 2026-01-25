#!/usr/bin/env python3
"""
RF Component Training Data Collector

This script helps collect and validate training data for fine-tuning
Ollama models to better recognize RF component specifications from
PDFs and webpages.

Usage:
    python training_data_collector.py --mode collect
    python training_data_collector.py --mode validate
    python training_data_collector.py --mode export
    python training_data_collector.py --mode test
"""

import json
import os
import sys
import hashlib
import datetime
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("Warning: PyMuPDF not installed. PDF extraction will be limited.")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests not installed. Web fetching will be limited.")


class TrainingDataCollector:
    """Collect and manage training data for RF component extraction"""

    def __init__(self, data_dir: str = None):
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = Path(data_dir) if data_dir else self.base_dir / "training_data"
        self.data_dir.mkdir(exist_ok=True)

        # Sub-directories
        self.pdfs_dir = self.data_dir / "pdfs"
        self.pdfs_dir.mkdir(exist_ok=True)
        self.extracts_dir = self.data_dir / "extracts"
        self.extracts_dir.mkdir(exist_ok=True)
        self.validated_dir = self.data_dir / "validated"
        self.validated_dir.mkdir(exist_ok=True)

        # Training data file
        self.training_file = self.data_dir / "training_pairs.jsonl"
        self.index_file = self.data_dir / "index.json"

        # Load or create index
        self.index = self._load_index()

        # Component types we support
        self.component_types = [
            "cable", "antenna", "transmitter", "lightning_arrestor",
            "isolator", "combiner", "filter", "connector", "amplifier", "attenuator"
        ]

        # Load enhanced prompts
        self.prompts = self._load_prompts()

    def _load_index(self) -> Dict:
        """Load or create the training data index"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created": datetime.datetime.now().isoformat(),
            "entries": [],
            "stats": {
                "total": 0,
                "validated": 0,
                "by_type": {}
            }
        }

    def _save_index(self):
        """Save the index file"""
        self.index["updated"] = datetime.datetime.now().isoformat()
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _load_prompts(self) -> Dict:
        """Load the enhanced prompts file"""
        prompts_file = self.base_dir / "components" / "scripts" / "enhanced_prompts.json"
        if prompts_file.exists():
            with open(prompts_file, 'r') as f:
                return json.load(f)
        return {}

    def _hash_content(self, content: str) -> str:
        """Create a hash of content for deduplication"""
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file"""
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF required for PDF extraction")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()

        return text.strip()

    def fetch_webpage_text(self, url: str) -> str:
        """Fetch and extract text from a webpage"""
        if not HAS_REQUESTS:
            raise ImportError("requests required for web fetching")

        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip_tags = {'script', 'style', 'nav', 'footer', 'header'}
                self.current_tag = None

            def handle_starttag(self, tag, attrs):
                self.current_tag = tag

            def handle_data(self, data):
                if self.current_tag not in self.skip_tags:
                    text = data.strip()
                    if text:
                        self.text.append(text)

            def get_text(self):
                return '\n'.join(self.text)

        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (RF Component Data Collector)'
        })
        response.raise_for_status()

        parser = TextExtractor()
        parser.feed(response.text)
        return parser.get_text()

    def add_training_example(self,
                            source_text: str,
                            expected_json: Dict,
                            source_type: str = "pdf",
                            source_path: str = None,
                            notes: str = None) -> str:
        """Add a new training example

        Args:
            source_text: The raw text from the datasheet/webpage
            expected_json: The correctly extracted JSON
            source_type: "pdf" or "webpage"
            source_path: Path or URL to source
            notes: Optional notes about this example

        Returns:
            Entry ID
        """
        # Validate expected JSON has required fields
        if "component_type" not in expected_json:
            raise ValueError("expected_json must have 'component_type' field")
        if "model" not in expected_json:
            raise ValueError("expected_json must have 'model' field")

        component_type = expected_json["component_type"]
        if component_type not in self.component_types:
            print(f"Warning: Unknown component type '{component_type}'")

        # Create entry
        entry_id = self._hash_content(source_text + json.dumps(expected_json))

        entry = {
            "id": entry_id,
            "source_type": source_type,
            "source_path": source_path,
            "component_type": component_type,
            "model": expected_json.get("model", "unknown"),
            "manufacturer": expected_json.get("manufacturer", "unknown"),
            "validated": False,
            "created": datetime.datetime.now().isoformat(),
            "notes": notes
        }

        # Save the extract
        extract_file = self.extracts_dir / f"{entry_id}.json"
        with open(extract_file, 'w') as f:
            json.dump({
                "entry": entry,
                "source_text": source_text[:10000],  # Limit text size
                "expected_json": expected_json
            }, f, indent=2)

        # Update index
        self.index["entries"].append(entry)
        self.index["stats"]["total"] += 1
        self.index["stats"]["by_type"][component_type] = \
            self.index["stats"]["by_type"].get(component_type, 0) + 1
        self._save_index()

        return entry_id

    def validate_example(self, entry_id: str, is_valid: bool = True, corrections: Dict = None):
        """Mark an example as validated (or corrected)

        Args:
            entry_id: The entry ID to validate
            is_valid: Whether the extraction is correct
            corrections: If not valid, provide corrected JSON
        """
        extract_file = self.extracts_dir / f"{entry_id}.json"
        if not extract_file.exists():
            raise FileNotFoundError(f"Entry not found: {entry_id}")

        with open(extract_file, 'r') as f:
            data = json.load(f)

        if not is_valid and corrections:
            data["expected_json"] = corrections

        data["entry"]["validated"] = True
        data["entry"]["validated_date"] = datetime.datetime.now().isoformat()

        # Save to validated directory
        validated_file = self.validated_dir / f"{entry_id}.json"
        with open(validated_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Update index
        for entry in self.index["entries"]:
            if entry["id"] == entry_id:
                entry["validated"] = True
                break
        self.index["stats"]["validated"] += 1
        self._save_index()

    def export_training_data(self, format: str = "jsonl") -> str:
        """Export validated training data for fine-tuning

        Args:
            format: "jsonl" for JSONL format, "alpaca" for Alpaca format

        Returns:
            Path to exported file
        """
        output_file = self.data_dir / f"training_data.{format}"

        validated_files = list(self.validated_dir.glob("*.json"))
        if not validated_files:
            print("No validated examples found. Validate some examples first.")
            return None

        training_pairs = []

        for vfile in validated_files:
            with open(vfile, 'r') as f:
                data = json.load(f)

            source_text = data["source_text"]
            expected = data["expected_json"]
            component_type = expected.get("component_type", "generic")

            # Get the appropriate prompt template
            prompt_template = self.prompts.get("prompts", {}).get(
                component_type,
                self.prompts.get("prompts", {}).get("generic", {})
            )

            system_prompt = prompt_template.get("system_prompt",
                "You are an RF component specification extraction expert.")

            if format == "jsonl":
                # Standard chat format for Ollama fine-tuning
                training_pairs.append({
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Extract specifications from this datasheet:\n\n{source_text[:4000]}"},
                        {"role": "assistant", "content": json.dumps(expected)}
                    ]
                })
            elif format == "alpaca":
                # Alpaca format
                training_pairs.append({
                    "instruction": system_prompt,
                    "input": f"Extract specifications from this datasheet:\n\n{source_text[:4000]}",
                    "output": json.dumps(expected)
                })

        with open(output_file, 'w') as f:
            for pair in training_pairs:
                f.write(json.dumps(pair) + '\n')

        print(f"Exported {len(training_pairs)} training examples to {output_file}")
        return str(output_file)

    def test_extraction(self, source_text: str, component_type: str = "generic") -> Dict:
        """Test Ollama extraction on source text

        Args:
            source_text: Text to extract from
            component_type: Type of component for prompt selection

        Returns:
            Extracted JSON from Ollama
        """
        if not HAS_REQUESTS:
            raise ImportError("requests required for Ollama API")

        prompt_template = self.prompts.get("prompts", {}).get(
            component_type,
            self.prompts.get("prompts", {}).get("generic", {})
        )

        system_prompt = prompt_template.get("system_prompt",
            "You are an RF component specification extraction expert.")
        user_prompt = prompt_template.get("user_prompt",
            "Extract specifications from this datasheet:\n{datasheet_text}")

        full_prompt = user_prompt.replace("{datasheet_text}", source_text[:6000])

        # Use the recommended model
        model = self.prompts.get("model_recommendation", "llama3.2:3b")

        try:
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': model,
                    'system': system_prompt,
                    'prompt': full_prompt,
                    'stream': False,
                    'format': 'json'
                },
                timeout=120
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API returned status {response.status_code}")

            result = response.json()
            response_text = result.get('response', '').strip()

            return json.loads(response_text)

        except Exception as e:
            return {"error": str(e)}

    def list_examples(self, validated_only: bool = False) -> List[Dict]:
        """List all training examples

        Args:
            validated_only: Only show validated examples

        Returns:
            List of entry summaries
        """
        entries = self.index.get("entries", [])
        if validated_only:
            entries = [e for e in entries if e.get("validated")]
        return entries

    def get_stats(self) -> Dict:
        """Get training data statistics"""
        return {
            "total_examples": self.index["stats"]["total"],
            "validated_examples": self.index["stats"]["validated"],
            "by_component_type": self.index["stats"]["by_type"],
            "data_directory": str(self.data_dir)
        }

    def import_from_catalog(self, catalog_path: str):
        """Import existing catalog entries as training examples

        This uses your existing validated catalog data to bootstrap
        the training dataset.
        """
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)

        manufacturer = catalog.get("manufacturer", "Unknown")
        components = catalog.get("components", [])

        imported = 0
        for component in components:
            # Create a synthetic "source text" that represents what a datasheet might contain
            component_type = component.get("component_type", "unknown")
            model = component.get("model", "unknown")

            # Build synthetic datasheet text
            text_parts = [
                f"{manufacturer} {model}",
                f"Model: {model}",
                f"Type: {component_type}",
            ]

            if "description" in component:
                text_parts.append(component["description"])

            # Add specs based on component type
            if component_type == "cable":
                if "impedance_ohms" in component:
                    text_parts.append(f"Impedance: {component['impedance_ohms']} ohms")
                if "velocity_factor" in component:
                    text_parts.append(f"Velocity: {component['velocity_factor'] * 100}%")
                if "loss_db_per_100ft" in component:
                    for freq, loss in component["loss_db_per_100ft"].items():
                        text_parts.append(f"Attenuation at {freq} MHz: {loss} dB/100ft")

            elif component_type == "antenna":
                if "gain_dbi" in component:
                    text_parts.append(f"Gain: {component['gain_dbi']} dBi")
                if "frequency_range_mhz" in component:
                    text_parts.append(f"Frequency: {component['frequency_range_mhz'][0]}-{component['frequency_range_mhz'][1]} MHz")
                if "polarization" in component:
                    text_parts.append(f"Polarization: {component['polarization']}")
                if "vswr" in component:
                    text_parts.append(f"VSWR: {component['vswr']}:1")

            elif component_type == "lightning_arrestor":
                if "insertion_loss_db" in component:
                    text_parts.append(f"Insertion Loss: {component['insertion_loss_db']} dB")
                if "voltage_rating_kv" in component:
                    text_parts.append(f"Surge Voltage: {component['voltage_rating_kv']} kV")
                if "dc_pass" in component:
                    text_parts.append(f"DC: {'Pass' if component['dc_pass'] else 'Block'}")

            source_text = '\n'.join(text_parts)

            try:
                entry_id = self.add_training_example(
                    source_text=source_text,
                    expected_json=component,
                    source_type="catalog",
                    source_path=catalog_path,
                    notes=f"Imported from {manufacturer} catalog"
                )
                # Auto-validate catalog entries since they're already verified
                self.validate_example(entry_id, is_valid=True)
                imported += 1
            except Exception as e:
                print(f"Error importing {model}: {e}")

        print(f"Imported {imported} examples from {catalog_path}")
        return imported


def main():
    parser = argparse.ArgumentParser(description="RF Component Training Data Collector")
    parser.add_argument("--mode", choices=["collect", "validate", "export", "test", "stats", "import"],
                       default="stats", help="Operation mode")
    parser.add_argument("--file", help="PDF file or URL to process")
    parser.add_argument("--type", default="generic", help="Component type for testing")
    parser.add_argument("--format", default="jsonl", choices=["jsonl", "alpaca"],
                       help="Export format")
    parser.add_argument("--catalog", help="Catalog file to import from")

    args = parser.parse_args()

    collector = TrainingDataCollector()

    if args.mode == "stats":
        stats = collector.get_stats()
        print("\n=== Training Data Statistics ===")
        print(f"Total examples: {stats['total_examples']}")
        print(f"Validated: {stats['validated_examples']}")
        print(f"Data directory: {stats['data_directory']}")
        print("\nBy component type:")
        for ctype, count in stats['by_component_type'].items():
            print(f"  {ctype}: {count}")

    elif args.mode == "collect":
        if not args.file:
            print("Error: --file required for collect mode")
            return

        if args.file.startswith("http"):
            text = collector.fetch_webpage_text(args.file)
        else:
            text = collector.extract_text_from_pdf(args.file)

        print(f"\nExtracted {len(text)} characters")
        print("\nPreview:")
        print(text[:500])
        print("\n...")

        # Test extraction
        print("\n=== Testing Ollama Extraction ===")
        result = collector.test_extraction(text, args.type)
        print(json.dumps(result, indent=2))

        # Ask if user wants to save
        save = input("\nSave this as a training example? (y/n): ").lower()
        if save == 'y':
            # Get corrections if needed
            correct = input("Is the extraction correct? (y/n): ").lower()
            if correct == 'y':
                expected = result
            else:
                print("Enter the correct JSON (or paste and press Enter twice):")
                lines = []
                while True:
                    line = input()
                    if line == "":
                        break
                    lines.append(line)
                expected = json.loads('\n'.join(lines))

            entry_id = collector.add_training_example(
                source_text=text,
                expected_json=expected,
                source_type="pdf" if not args.file.startswith("http") else "webpage",
                source_path=args.file
            )
            collector.validate_example(entry_id, is_valid=True)
            print(f"Saved as entry: {entry_id}")

    elif args.mode == "export":
        output = collector.export_training_data(args.format)
        if output:
            print(f"Training data exported to: {output}")

    elif args.mode == "test":
        if not args.file:
            print("Error: --file required for test mode")
            return

        if args.file.startswith("http"):
            text = collector.fetch_webpage_text(args.file)
        else:
            text = collector.extract_text_from_pdf(args.file)

        print(f"Testing extraction on {len(text)} characters...")
        result = collector.test_extraction(text, args.type)
        print(json.dumps(result, indent=2))

    elif args.mode == "import":
        if not args.catalog:
            # Import all catalogs
            catalog_dir = Path(__file__).parent.parent / "catalogs"
            for catalog_file in catalog_dir.glob("*.json"):
                if catalog_file.name != "manufacturers.json":
                    collector.import_from_catalog(str(catalog_file))
        else:
            collector.import_from_catalog(args.catalog)

        stats = collector.get_stats()
        print(f"\nTotal training examples: {stats['total_examples']}")


if __name__ == "__main__":
    main()
