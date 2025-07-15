Title: "Fusion 360 Parametric Build System (Internship Project)"
Description: >
  A proof-of-concept system developed during my internship at Philips India Ltd.
  to explore AI-assisted CAD modification. This prototype demonstrates how
  natural language instructions can be converted into basic parametric updates
  in Fusion 360 using LLMs and a vector database.

Table_of_contents:
  - Overview
  - System Architecture
  - Core Components
  - Installation
  - Basic Usage
  - Current Limitations
  - File Structure
  - Acknowledgement

overview:
  objective: >
    Build a system to reduce manual CAD editing time by automating simple
    parametric changes via natural language prompts.
  key_capabilities:
    - Converts natural language to structured JSON instructions.
    - Retrieves relevant Fusion API code examples from a ChromaDB vector database.
    - Generates and executes basic Fusion 360 Python scripts.
    - Supports simple parametric edits such as cylinder creation and hole diameter modification.

system_architecture:
  workflow: "Text Instruction → JSON Parser → Vector Search → Code Generator → Fusion 360 Script"
  current_scope:
    - Limited to basic geometric edits only.
    - Single-script execution in Fusion 360 due to runtime restrictions.

core_components:
  text_to_json:
    file: "text_2_JSON.py"
    description: >
      Converts natural language to structured JSON instructions for CAD updates.
    example:
      input: "change cylinder diameter to 25mm"
      output_json:
        part: "cylinder"
        parameter: "diameter"
        new_value: 25
        unit: "mm"
  vector_database:
    files:
      - vector_db_setup.py
      - add_code.py
      - quick_add.py
      - view_database.py
    description: >
      ChromaDB-based storage for reusable Fusion API snippets and code patterns,
      enabling semantic search for relevant examples.
  code_generator:
    files:
      - qwen_coder_bot.py
    description: >
      Uses Qwen2.5-coder to convert JSON instructions into Fusion 360 Python API code,
      with basic error handling and retries.
  integrated_pipeline:
    file: "integrated_fusion_generator.py"
    description: >
      Combines JSON parsing, code generation, and execution into a single Fusion-compliant script.
      Currently supports creating and modifying basic geometric parts.

installation:
  prerequisites:
    - Python 3.8+
    - Autodesk Fusion 360 with Python scripting
    - Ollama for local LLM execution
  setup_commands:
    - "pip install chromadb requests"
    - "ollama serve"
    - "ollama pull qwen2.5-coder:7b"
    - "ollama pull gemma:4b"
  database_initialization:
    - "python vector_db_setup.py"
    - "python add_code.py"

basic_usage:
  run_pipeline: "python integrated_fusion_generator.py"
  example:
    instruction: "create a cylinder diameter 40mm height 60mm"
    result: "Fusion 360 executes generated code and performs the edit."

current_limitations:
  - Prototype stage, not optimized for complex assemblies.
  - Limited to basic geometric features (extrude, cut, simple parametric updates).
  - Vector database contains a small set of manually added examples.
  - Basic error handling; no advanced recovery or multi-part assembly support.

file_structure: |
  parametric_build/
  ├── text_2_JSON.py                  # Natural language to JSON converter
  ├── updation_pipeline/
  │   ├── database_builder/
  │   │   ├── vector_db_setup.py     # Setup ChromaDB
  │   │   ├── add_code.py            # Add examples to DB
  │   │   ├── quick_add.py           # Quick code addition utility
  │   │   └── view_database.py       # Search and view DB contents
  │   └── qwen_bot/
  │       ├── qwen_coder_bot.py      # JSON to Fusion code generation
  │       ├── integrated_fusion_generator.py  # Combined pipeline
  │       ├── test.py                # Basic validation tests

acknowledgement: >
  This project was developed as part of my internship at Philips India Ltd.
  under the guidance of Prof. Amber Srivastava (IIT Delhi) and Dr. Amar Banerjee
  (Scientist, AI Innovation, Philips India Ltd.). Inspired by Adaptive RAG for CAD
  (Neil Patel, 2025), this work explores its adaptation for real-world parametric CAD updates.
