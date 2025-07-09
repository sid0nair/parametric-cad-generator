import subprocess
import shlex
import json
import re
from typing import Dict, Any, List, Optional

def run_ollama(prompt: str, model: str = "qwen2.5-coder:7b") -> str:
    """Runs the Ollama model with the provided prompt"""
    command = f'echo {shlex.quote(prompt)} | ollama run {model}'
    result = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.stderr:
        print("=== STDERR FROM OLLAMA ===")
        print(result.stderr.decode("utf-8"))
        print("==========================")
    return result.stdout.decode("utf-8")

def extract_json(text: str) -> List[Dict[str, Any]]:
    """
    Attempts to extract one or more JSON objects or arrays from a model's response.
    """
    try:
        # Remove Markdown formatting
        text = text.strip().replace("```json", "").replace("```", "")

        # Use regex to extract valid JSON object or array (non-greedy)
        json_matches = re.findall(r'(\{.*?\}|\[.*?\])', text, re.DOTALL)

        if not json_matches:
            raise ValueError("No valid JSON blocks found.")

        results = []
        for block in json_matches:
            try:
                parsed = json.loads(block)
                if isinstance(parsed, dict):
                    results.append(parsed)
                elif isinstance(parsed, list):
                    results.extend(parsed)
            except json.JSONDecodeError:
                continue

        return results
    except Exception as e:
        print("❌ JSON extraction failed:", e)
        return []

def validate_output(json_output: Dict[str, Any]) -> bool:
    """Validate JSON output with improved error messages"""

    # Check for error response first
    if "error" in json_output:
        print(f"⚠️ Model returned error: {json_output['error']}")
        return False

    required_base_fields = ["part", "feature", "parameter", "unit", "confidence"]

    # Check required fields
    missing_fields = [field for field in required_base_fields if field not in json_output]
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False

    # Validate unit
    if json_output["unit"].lower() != "mm":
        print(f"❌ Invalid unit '{json_output['unit']}' - must be 'mm'")
        return False

    # Validate confidence
    confidence = json_output["confidence"]
    if not isinstance(confidence, (float, int)) or not (0 <= confidence <= 1):
        print(f"❌ Invalid confidence '{confidence}' - must be float between 0 and 1")
        return False

    # Validate value fields
    has_new_value = "new_value" in json_output
    has_delta = "delta" in json_output

    if has_new_value and has_delta:
        print("❌ Both 'new_value' and 'delta' present — only one allowed")
        return False

    if not has_new_value and not has_delta:
        print("❌ Either 'new_value' or 'delta' must be present")
        return False

    if has_new_value:
        if not isinstance(json_output["new_value"], (int, float)):
            print(f"❌ 'new_value' must be numeric, got {type(json_output['new_value'])}")
            return False

    if has_delta:
        if not isinstance(json_output["delta"], (int, float)):
            print(f"❌ 'delta' must be numeric, got {type(json_output['delta'])}")
            return False

    # Enhanced feature validation with database compatibility
    allowed_features = [
        "Extrude1", "Revolve1", "Cut1", "Fillet1", "Chamfer1", "Shell1",
        "Sweep1", "Loft1", "Mirror1", "Pattern1", "Draft1", "Hole1",
        "Thicken1", "Wrap1"
    ]

    if json_output["feature"] not in allowed_features:
        print(f"❌ Invalid feature '{json_output['feature']}' - must be one of {allowed_features}")
        return False

    print("✅ JSON validation passed")
    return True

def process_cad_instruction(instruction: str) -> Optional[List[Dict[str, Any]]]:
    """Process a single CAD instruction and return validated JSON"""
    
    prompt = f"""
You are an assistant that converts CAD instructions into structured JSON.
IMPORTANT: For multi-dimensional objects (like "50x40x20"), you MUST output multiple JSON objects - one for each dimension.

Use ONLY this schema:

{{
  "part": "<string>",
  "feature": "<see allowed features below>",
  "parameter": "<Length, Width, Diameter, etc.>",
  "new_value": <numeric_value>,
  "unit": "mm",
  "confidence": <float between 0 and 1>
}}

CRITICAL: For instructions with multiple dimensions (like "50x40x20"), output an ARRAY of JSON objects:
[
  {{"part": "block", "feature": "Extrude1", "parameter": "Length", "new_value": 50, "unit": "mm", "confidence": 0.95}},
  {{"part": "block", "feature": "Extrude1", "parameter": "Width", "new_value": 40, "unit": "mm", "confidence": 0.95}},
  {{"part": "block", "feature": "Extrude1", "parameter": "Height", "new_value": 20, "unit": "mm", "confidence": 0.95}}
]

ENHANCED FEATURE MAPPING FOR BETTER DATABASE MATCHING:
When determining the "part" and "feature", use these mappings to ensure compatibility with the code database:

For geometric shapes and basic operations:
- "cylinder", "tube", "pipe", "rod", "shaft" → use "cylinder" as part, "Extrude1" as feature
- "block", "box", "cube", "rectangle", "rectangular" → use "block" as part, "Extrude1" as feature  
- "hollow cylinder", "tube", "pipe" → use "hollow cylinder" as part, "Extrude1" as feature
- "sphere", "ball" → use "sphere" as part, "Revolve1" as feature

DIMENSION MAPPING FOR BLOCKS/RECTANGLES:
- First number (50 in "50x40x20") = Length
- Second number (40 in "50x40x20") = Width  
- Third number (20 in "50x40x20") = Height

RULES:
- For single dimensions: output single JSON object
- For multiple dimensions (XxYxZ format): output ARRAY of JSON objects, one per dimension
- Always use "new_value" for specified dimensions (never "delta")
- "parameter" must be: Length, Width, Height, Diameter, Radius, Thickness, or Angle
- "confidence" is a float between 0 and 1
- "feature" must be one of: Extrude1, Revolve1, Cut1, Fillet1, Chamfer1, Shell1, Sweep1, Loft1, Mirror1, Pattern1, Draft1, Hole1, Thicken1, Wrap1
- "new_value" must be a number
- "unit" must be 'mm'

EXAMPLES:

Instruction: "Change the cylinder diameter to 35 mm."
Output:
{{"part": "cylinder", "feature": "Extrude1", "parameter": "Diameter", "new_value": 35, "unit": "mm", "confidence": 0.95}}

Instruction: "Make a rectangular block 50x30x20mm."
Output:
[
  {{"part": "block", "feature": "Extrude1", "parameter": "Length", "new_value": 50, "unit": "mm", "confidence": 0.95}},
  {{"part": "block", "feature": "Extrude1", "parameter": "Width", "new_value": 30, "unit": "mm", "confidence": 0.95}},
  {{"part": "block", "feature": "Extrude1", "parameter": "Height", "new_value": 20, "unit": "mm", "confidence": 0.95}}
]

Instruction: "Create a cube 25x25x25."
Output:
[
  {{"part": "block", "feature": "Extrude1", "parameter": "Length", "new_value": 25, "unit": "mm", "confidence": 0.98}},
  {{"part": "block", "feature": "Extrude1", "parameter": "Width", "new_value": 25, "unit": "mm", "confidence": 0.98}},
  {{"part": "block", "feature": "Extrude1", "parameter": "Height", "new_value": 25, "unit": "mm", "confidence": 0.98}}
]

Instruction: "Make a cylinder diameter 40mm height 60mm."
Output:
[
  {{"part": "cylinder", "feature": "Extrude1", "parameter": "Diameter", "new_value": 40, "unit": "mm", "confidence": 0.92}},
  {{"part": "cylinder", "feature": "Extrude1", "parameter": "Height", "new_value": 60, "unit": "mm", "confidence": 0.92}}
]

Instruction: "{instruction}"
Output:
"""
    
    try:
        # Get model response
        model_output = run_ollama(prompt)
        if not model_output.strip():
            print("❌ Empty response from model")
            return None
        
        # Extract JSON
        responses = extract_json(model_output)
        if not responses:
            print("❌ No valid JSON found in response")
            print(f"Raw response: {model_output}")
            return None
        
        # Validate responses
        valid_responses = []
        for i, json_output in enumerate(responses):
            print(f"\n📋 Validating JSON #{i+1}:")
            print(json.dumps(json_output, indent=2))
            
            if validate_output(json_output):
                valid_responses.append(json_output)
            else:
                print(f"❌ JSON #{i+1} failed validation")
        
        # Return valid responses or None
        if valid_responses:
            return valid_responses
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error processing instruction: {e}")
        return None

def main():
    """Main interactive loop"""
    print("🔧 CAD Instruction to JSON Converter")
    print("Type your instruction (or 'exit' to quit):\n")

    while True:
        try:
            instruction = input("Instruction: ").strip()
            if instruction.lower() == "exit":
                print("👋 Goodbye!")
                break

            if not instruction:
                print("⚠️ Please enter an instruction")
                continue

            print(f"\n🔍 Processing: '{instruction}'")
            results = process_cad_instruction(instruction)

            if results:
                print(f"\n✅ Successfully parsed {len(results)} instruction(s)")
                for i, result in enumerate(results, 1):
                    print(f"\nResult #{i}:")
                    print(json.dumps(result, indent=2))
            else:
                print("\n❌ Failed to parse instruction")

            print("\n" + "="*50)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()