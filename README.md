# Fusion 360 Parametric Build System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Fusion 360](https://img.shields.io/badge/Fusion%20360-API-orange.svg)](https://www.autodesk.com/products/fusion-360/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-green.svg)](https://www.trychroma.com/)

> A proof-of-concept system that demonstrates AI-assisted CAD modification by converting natural language instructions into parametric updates in Fusion 360 using LLMs and vector databases.

Developed during my internship at **Philips India Ltd.** under the guidance of Prof. Amber Srivastava (IIT Delhi) and Dr. Amar Banerjee (Philips India Ltd.).

---

## 🎯 Overview

This project explores how natural language processing can streamline CAD workflows by automating simple parametric changes. Instead of manually editing CAD models, users can provide text instructions that are automatically converted into executable Fusion 360 scripts.

### Key Capabilities

- 🗣️ **Natural Language to JSON**: Convert plain English instructions into structured JSON commands
- 🔍 **Semantic Code Search**: Retrieve relevant Fusion 360 API examples using ChromaDB vector database
- 🤖 **AI Code Generation**: Generate Python scripts using Qwen2.5-coder for Fusion 360 automation
- ⚙️ **Parametric Editing**: Support for basic geometric operations like cylinder creation and dimension modifications

---

## 🏗️ System Architecture

```
Text Instruction → JSON Parser → Vector Search → Code Generator → Fusion 360 Script
```

The system follows a modular pipeline:

1. **Natural Language Input**: User provides instruction (e.g., "create a cylinder diameter 40mm height 60mm")
2. **JSON Conversion**: Text is parsed into structured JSON format
3. **Vector Database Query**: Relevant Fusion API code examples are retrieved semantically
4. **Code Generation**: LLM generates executable Python code based on examples
5. **Execution**: Generated script runs in Fusion 360 to perform the CAD operation

### Current Scope

- ✅ Basic geometric edits (extrude, cut, simple parametric updates)
- ✅ Single-script execution per operation
- ⚠️ Limited to simple features (not optimized for complex assemblies)

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- [Autodesk Fusion 360](https://www.autodesk.com/products/fusion-360/) with Python scripting enabled
- [Ollama](https://ollama.ai/) for local LLM execution

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/fusion360-parametric-build.git
   cd fusion360-parametric-build
   ```

2. **Install Python dependencies**
   ```bash
   pip install chromadb requests
   ```

3. **Setup Ollama and pull required models**
   ```bash
   ollama serve
   ollama pull qwen2.5-coder:7b
   ollama pull gemma:4b
   ```

4. **Initialize the vector database**
   ```bash
   python vector_db_setup.py
   python add_code.py
   ```

---

## 🚀 Usage

### Running the Pipeline

```bash
python integrated_fusion_generator.py
```

### Example Workflow

**Input:**
```
"create a cylinder diameter 40mm height 60mm"
```

**Generated JSON:**
```json
{
  "part": "cylinder",
  "parameter": "diameter",
  "new_value": 40,
  "unit": "mm",
  "height": 60
}
```

**Result:** Fusion 360 executes the generated script and creates the specified cylinder.

### Supported Operations

- Creating basic geometric shapes (cylinders, boxes)
- Modifying parametric dimensions
- Simple hole creation and diameter changes

---

## 📁 Project Structure

```
parametric_build/
├── text_2_JSON.py                      # Natural language to JSON converter
├── updation_pipeline/
│   ├── database_builder/
│   │   ├── vector_db_setup.py         # Setup ChromaDB
│   │   ├── add_code.py                # Add examples to database
│   │   ├── quick_add.py               # Quick code addition utility
│   │   └── view_database.py           # Search and view database contents
│   └── qwen_bot/
│       ├── qwen_coder_bot.py          # JSON to Fusion code generation
│       ├── integrated_fusion_generator.py  # Combined pipeline
│       └── test.py                    # Basic validation tests
└── README.md
```

---

## 🔧 Core Components

### 1. Text-to-JSON Parser (`text_2_JSON.py`)

Converts natural language instructions into structured JSON format for downstream processing.

**Example:**
- Input: `"change cylinder diameter to 25mm"`
- Output: `{"part": "cylinder", "parameter": "diameter", "new_value": 25, "unit": "mm"}`

### 2. Vector Database (`database_builder/`)

ChromaDB-based storage system for Fusion 360 API code snippets, enabling semantic search for relevant examples.

**Files:**
- `vector_db_setup.py` - Initialize ChromaDB
- `add_code.py` - Add code examples to database
- `quick_add.py` - Quick utility for adding snippets
- `view_database.py` - Search and inspect database contents

### 3. Code Generator (`qwen_coder_bot.py`)

Uses Qwen2.5-coder LLM to convert JSON instructions into executable Fusion 360 Python API code with error handling and retry logic.

### 4. Integrated Pipeline (`integrated_fusion_generator.py`)

Combines all components into a single Fusion 360-compliant script that handles the complete workflow from natural language to CAD execution.

---

## ⚠️ Current Limitations

This is a **proof-of-concept prototype** with the following limitations:

- 🔸 Limited to basic geometric features (not suitable for complex assemblies)
- 🔸 Small vector database with manually added examples
- 🔸 Basic error handling (no advanced recovery mechanisms)
- 🔸 Single-script execution per operation due to Fusion 360 runtime restrictions
---

## 🔮 Future Enhancements

- [ ] Expand vector database with comprehensive Fusion API examples
- [ ] Support for complex assemblies and constraints
- [ ] Advanced error recovery and validation
- [ ] Multi-step operation support
- [ ] Integration with CAD file version control
- [ ] Web interface for easier interaction

---

## 🙏 Acknowledgements

This project was developed as part of my internship at **Philips India Ltd.** under the guidance of:

- **Prof. Amber Srivastava** - IIT Delhi
- **Dr. Amar Banerjee** - Scientist, AI Innovation, Philips India Ltd.

Inspired by **Adaptive RAG for CAD** (Neil Patel, 2025), this work explores its adaptation for real-world parametric CAD updates.

---

## 📄 License

This project is part of academic research conducted at IIT Delhi and Philips India Ltd.
