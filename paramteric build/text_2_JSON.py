import subprocess
import json
import re
import shlex

## Runs the Ollama model with the provided prompt
def run_ollama(prompt, model="gemma3:4b"):
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

## Extracts JSON from the output text
import json
import re

def extract_json(text):
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


## validates the JSON output against the required schema
def validate_output(json_output):
    required_base_fields = ["part", "feature", "parameter", "unit", "confidence"]

    # Ensure all required fields are present
    for field in required_base_fields:
        if field not in json_output:
            print(f"❌ Missing field: {field}")
            return False

    # Ensure unit is "mm"
    if json_output["unit"].lower() != "mm":
        print("❌ 'unit' must be 'mm'.")
        return False

    # Validate confidence
    if not isinstance(json_output["confidence"], (float, int)) or not (0 <= json_output["confidence"] <= 1):
        print("❌ 'confidence' must be a float between 0 and 1.")
        return False

    # Ensure EITHER new_value OR delta is present (but not both)
    has_new_value = "new_value" in json_output
    has_delta = "delta" in json_output

    if has_new_value and has_delta:
        print("❌ Both 'new_value' and 'delta' present — only one is allowed.")
        return False

    if not has_new_value and not has_delta:
        print("❌ Either 'new_value' or 'delta' must be present.")
        return False

    if has_new_value and not isinstance(json_output["new_value"], (int, float)):
        print("❌ 'new_value' must be a number.")
        return False

    if has_delta and not isinstance(json_output["delta"], (int, float)):
        print("❌ 'delta' must be a number.")
        return False

    return True

print("CAD Instruction to JSON Converter")
print("Type your instruction (or 'exit' to quit):\n")

while True:
    instruction = input("Instruction: ").strip()
    if instruction.lower() == "exit":
        break

    prompt = f"""
You are an assistant that converts CAD instructions into structured JSON.
If multiple changes are described, output a list of JSON objects.
Use ONLY this schema:

{{
  "part": "<string>",
  "feature": "<see allowed features below>",
  "parameter": "<Length, Width, Diameter, etc.>",
  "new_value": <optional_numeric_value>,// Only include if the instruction specifies a final value (e.g. 200 in 'from 100 mm to 200 mm')
  "delta": <optional_numeric_value>,  // Only include if the instruction specifies a change from an existing value
  "unit": "mm",
  "confidence": <float between 0 and 1>  // Estimate a confidence score between 0 and 1 based on how certain you are that the output correctly represents the instruction. Ensure this is a float. Ensure the probability score is legit and not a random float.
}}

RULES:
- Strict adherence to the following steps:
Step 1: Assess if the instruction is valid and clearly refers to a CAD-related dimension or feature.
Step 2: If valid, convert to the JSON schema below.
Step 3: If invalid, return:  "error": "Invalid CAD instruction."
- If the instruction includes terms like "increase by", "decrease by", "change by", "add", "reduce by", or "modify by", use only "delta" (a numeric difference). Do NOT output "new_value" in such cases.
- Only use "new_value" if a final absolute value is clearly specified (e.g., "set length to 100 mm").
- If the instruction specifies the final value (e.g., "set to 100 mm", "make it 25 mm"), then use "new_value" and OMIT "delta".
- DO NOT INCLUDE both "new_value" and "delta" in the same output.
- If the instruction is ambiguous or does not clearly specify a dimension or feature, return: "
- Output only one flat JSON object.
- Use only ONE value as "new_value" — the target value (e.g. 200 in 'from 100 mm to 200 mm').
- Ignore original values unless needed to disambiguate.
- "parameter" is what is being modified (e.g. Length, Width, Diameter, Height, etc.).
- "confidence" is a float between 0 and 1, estimating how certain you are that the output correctly represents the instruction.
- "feature" must be one of the following:

  - Extrude1
  - Revolve1
  - Cut1
  - Fillet1
  - Chamfer1
  - Shell1
  - Sweep1
  - Loft1
  - Mirror1
  - Pattern1
  - Draft1
  - Hole1
  - Thicken1
  - Wrap1

- "new_value" must be a number.
- "unit" must be 'mm'.
- Do NOT output anything other than the final JSON.

Examples:

Instruction: "Change the shaft diameter to 35 mm."
Output:
{{"part": "shaft", "feature": "Extrude1", "parameter": "Diameter", "new_value": 35, "unit": "mm", "confidence": 0.95}}

Instruction: "Reduce the piston rod length from 150 mm to 125 mm."
Output:
{{"part": "piston rod", "feature": "Extrude1", "parameter": "Length", "new_value": 125, "unit": "mm", "confidence": 0.97}}

Instruction: "Make hole 8 mm."
Output:
{{"part": "hole", "feature": "Hole1", "parameter": "Diameter", "new_value": 8, "unit": "mm", "confidence": 0.98}}

Instruction: "Make the flange 40 mm wide and 15 mm thick."
Output:
[
  {{"part": "flange", "feature": "Extrude1", "parameter": "Width", "new_value": 40, "unit": "mm", "confidence": 0.92}},
  {{"part": "flange", "feature": "Thicken1", "parameter": "Thickness", "new_value": 15, "unit": "mm", "confidence": 0.91}}
]

Instruction: "{instruction}"
Output:
"""

    # Run model on the prompt
    model_output = run_ollama(prompt)

    # Extract and validate JSON from model output
    responses = extract_json(model_output)

    if not responses or len(responses) > 20:
        print("⚠️ Likely malformed response or runaway JSON generation.")
        continue

    for i, json_output in enumerate(responses):
        print(f"\nParsed JSON #{i+1}:")
        print(json.dumps(json_output, indent=2))

        if not validate_output(json_output):
            print("⚠️ Output does not match required schema.")
