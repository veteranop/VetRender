#!/usr/bin/env python3
"""
Ollama Fine-tuning Script for RF Component Recognition

This script creates a custom Ollama model fine-tuned on RF component
specification extraction using your training data.

Usage:
    python finetune_ollama.py --create    # Create the fine-tuned model
    python finetune_ollama.py --test      # Test the model
    python finetune_ollama.py --compare   # Compare base vs fine-tuned
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
TRAINING_DATA = BASE_DIR / "training_data" / "training_data.jsonl"
MODELFILE = BASE_DIR / "training_data" / "Modelfile"


def create_modelfile():
    """Create an Ollama Modelfile for the fine-tuned model"""

    # Load a few training examples for the system prompt
    examples = []
    if TRAINING_DATA.exists():
        with open(TRAINING_DATA, 'r') as f:
            for i, line in enumerate(f):
                if i >= 5:  # Just use first 5 examples
                    break
                data = json.loads(line)
                messages = data.get('messages', [])
                for msg in messages:
                    if msg['role'] == 'assistant':
                        try:
                            parsed = json.loads(msg['content'])
                            examples.append(parsed)
                        except:
                            pass

    # Build example strings
    example_strings = []
    for ex in examples[:3]:
        ctype = ex.get('component_type', 'unknown')
        model = ex.get('model', 'unknown')
        example_strings.append(f"- {ctype}: {model}")

    modelfile_content = f'''# RF Component Extraction Model
# Fine-tuned from llama3.2:3b for extracting RF component specifications

FROM llama3.2:3b

# Set parameters for extraction tasks
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_predict 2048

# System prompt optimized for RF component extraction
SYSTEM """You are an expert RF engineer specializing in extracting technical specifications from datasheets.

Your task is to analyze datasheet text and extract component specifications as valid JSON.

You are trained to recognize these RF component types:
- cable: Coaxial cables (LMR, Heliax, etc.)
- antenna: Broadcast and communications antennas
- transmitter: RF transmitters and exciters
- lightning_arrestor: Surge protectors and arrestors
- isolator: RF isolators and circulators
- combiner: RF combiners
- filter: Bandpass, notch, and harmonic filters
- connector: RF connectors and adapters
- amplifier: RF amplifiers
- attenuator: Fixed and variable attenuators

Key specifications to extract by type:
- Cables: loss_db_per_100ft (at multiple frequencies), impedance_ohms, velocity_factor
- Antennas: gain_dbi, frequency_range_mhz, polarization, vswr, power_rating_watts
- Transmitters: power_output_watts, frequency_range_mhz, efficiency_percent
- Lightning arrestors: insertion_loss_db, voltage_rating_kv, dc_pass (true/false)
- Isolators: insertion_loss_db, isolation_db, frequency_range_mhz

Important conversion: dBi = dBd + 2.15

ALWAYS return valid JSON only. No markdown, no explanations.
"""

# Template for consistent output format
TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>

{{ .Response }}<|eot_id|>"""
'''

    MODELFILE.parent.mkdir(exist_ok=True)
    with open(MODELFILE, 'w') as f:
        f.write(modelfile_content)

    print(f"Created Modelfile at: {MODELFILE}")
    return MODELFILE


def create_model():
    """Create the fine-tuned Ollama model"""

    # First create the Modelfile
    modelfile_path = create_modelfile()

    print("\n=== Creating Fine-tuned Ollama Model ===")
    print("Model name: rf-component-extractor")
    print(f"Base model: llama3.2:3b")
    print(f"Modelfile: {modelfile_path}")

    # Create the model using Ollama
    try:
        result = subprocess.run(
            ['ollama', 'create', 'rf-component-extractor', '-f', str(modelfile_path)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print("\nModel created successfully!")
            print(result.stdout)
        else:
            print(f"\nError creating model:")
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("Error: Ollama not found. Make sure Ollama is installed and in PATH.")
        return False
    except subprocess.TimeoutExpired:
        print("Error: Model creation timed out.")
        return False

    # Verify model exists
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
    if 'rf-component-extractor' in result.stdout:
        print("\nModel 'rf-component-extractor' is now available!")
        print("\nTo use in your application, update the model name to 'rf-component-extractor'")
        return True
    else:
        print("\nWarning: Model may not have been created properly.")
        return False


def test_model(model_name: str = "rf-component-extractor"):
    """Test the model with sample input"""
    import requests

    test_input = """Times Microwave LMR-400 Coaxial Cable
50 Ohm Flexible Low Loss
Velocity of Propagation: 85%
Outer Diameter: 0.405 inches
Attenuation:
  150 MHz: 0.7 dB/100ft
  450 MHz: 1.3 dB/100ft
  900 MHz: 1.9 dB/100ft
  1500 MHz: 2.5 dB/100ft
Power Rating:
  150 MHz: 1800W
  900 MHz: 750W
Connectors: N-type, SMA available"""

    print(f"\n=== Testing Model: {model_name} ===")
    print(f"\nInput text:\n{test_input[:200]}...")

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model_name,
                'prompt': f"Extract specifications from this datasheet:\n\n{test_input}",
                'stream': False,
                'format': 'json'
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            output = result.get('response', '')
            print(f"\nExtracted JSON:")
            try:
                parsed = json.loads(output)
                print(json.dumps(parsed, indent=2))
            except:
                print(output)
        else:
            print(f"Error: API returned {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to Ollama. Is it running?")
    except Exception as e:
        print(f"Error: {e}")


def compare_models():
    """Compare base model vs fine-tuned model"""
    import requests

    test_cases = [
        {
            "name": "Cable extraction",
            "text": "Andrew LDF4-50A HELIAX 1/2\" corrugated copper, 50 ohm, 88% velocity, Loss: 0.32dB@100MHz, 0.68dB@450MHz, 1.18dB@1GHz"
        },
        {
            "name": "Antenna extraction",
            "text": "Jampro JCPV-2 FM Broadcast, 88-108MHz, Gain 3.0dBi, Circular pol, VSWR 1.08:1, 30kW, EIA 1-5/8 flange"
        },
        {
            "name": "Lightning arrestor",
            "text": "PolyPhaser IS-B50LN-C0, Bulkhead mount, N-Female both sides, 0.2dB insertion loss, DC-1000MHz, 5kV surge, DC Pass"
        }
    ]

    models = ["llama3.2:3b", "rf-component-extractor"]

    print("\n=== Model Comparison ===\n")

    for test in test_cases:
        print(f"\n--- {test['name']} ---")
        print(f"Input: {test['text'][:80]}...")

        for model in models:
            try:
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': model,
                        'prompt': f"Extract RF component specifications as JSON:\n\n{test['text']}\n\nReturn ONLY valid JSON, no markdown or explanation.",
                        'stream': False
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    output = result.get('response', '')
                    print(f"\n{model}:")
                    try:
                        # Try to extract JSON from markdown code blocks
                        import re
                        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', output)
                        if json_match:
                            json_str = json_match.group(1).strip()
                        else:
                            json_str = output.strip()
                        parsed = json.loads(json_str)
                        # Show key fields
                        keys_to_show = ['component_type', 'type', 'model', 'manufacturer']
                        summary = {k: parsed.get(k) for k in keys_to_show if k in parsed}
                        print(f"  {summary}")
                    except Exception as e:
                        print(f"  Raw: {output[:150]}...")

            except Exception as e:
                print(f"\n{model}: Error - {e}")


def main():
    parser = argparse.ArgumentParser(description="Ollama Fine-tuning for RF Components")
    parser.add_argument("--create", action="store_true", help="Create the fine-tuned model")
    parser.add_argument("--test", action="store_true", help="Test the fine-tuned model")
    parser.add_argument("--compare", action="store_true", help="Compare base vs fine-tuned")
    parser.add_argument("--model", default="rf-component-extractor", help="Model name to test")

    args = parser.parse_args()

    if args.create:
        create_model()
    elif args.test:
        test_model(args.model)
    elif args.compare:
        compare_models()
    else:
        parser.print_help()
        print("\n\nQuick start:")
        print("  1. python finetune_ollama.py --create    # Create model")
        print("  2. python finetune_ollama.py --test      # Test it")
        print("  3. python finetune_ollama.py --compare   # Compare with base")


if __name__ == "__main__":
    main()
