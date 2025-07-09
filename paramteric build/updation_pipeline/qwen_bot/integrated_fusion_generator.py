#!/usr/bin/env python3
"""
Integrated Fusion 360 Code Generator
Combines text-to-JSON conversion with vector database retrieval and Qwen code generation
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import chromadb
import traceback

class IntegratedFusionGenerator:
    """
    Complete pipeline: Text → JSON → Vector Search → Code Generation
    """
    
    def __init__(self, 
                 db_path: str = "./chroma_cad_db",
                 collection_name: str = "fusion360_code_examples",
                 ollama_model: str = "qwen2.5-coder:7b",
                 text_to_json_script: str = "text_2_JSON.py"):
        """
        Initialize the integrated generator
        
        Args:
            db_path: Path to ChromaDB database
            collection_name: Name of the collection in ChromaDB
            ollama_model: Ollama model to use for code generation
            text_to_json_script: Path to your existing text-to-JSON converter
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.ollama_model = ollama_model
        self.text_to_json_script = text_to_json_script
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✅ Connected to ChromaDB: {collection_name}")
        except Exception as e:
            print(f"❌ Error connecting to ChromaDB: {e}")
            raise
        
        # Ollama API endpoint
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Test Ollama connection
        self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test if Ollama is running and accessible"""
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama connection successful")
            else:
                print(f"Ollama responded with status: {response.status_code}")
        except Exception as e:
            print(f"Ollama connection test failed: {e}")
            print("Make sure Ollama is running with: ollama serve")
    
    def text_to_json(self, text_instruction: str) -> Optional[List[Dict[str, Any]]]:
        """
        Convert text instruction to JSON using your existing script
        
        Args:
            text_instruction: Natural language instruction
            
        Returns:
            List of parsed JSON instructions or None if failed
        """
        try:
            # Check if the text-to-JSON script exists
            if not os.path.exists(self.text_to_json_script):
                print(f"❌ Text-to-JSON script not found: {self.text_to_json_script}")
                return None
            
            # Run the text-to-JSON converter
            process = subprocess.run([
                sys.executable, self.text_to_json_script
            ], 
            input=text_instruction + "\nexit\n",
            text=True,
            capture_output=True,
            timeout=30
            )
            
            if process.returncode != 0:
                print(f"❌ Text-to-JSON conversion failed: {process.stderr}")
                return None
            
            # Parse the output to extract multiple JSON objects
            output_lines = process.stdout.split('\n')
            json_objects = []
            
            # Look for lines that contain complete JSON objects
            for line in output_lines:
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        parsed_obj = json.loads(line)
                        json_objects.append(parsed_obj)
                    except json.JSONDecodeError:
                        continue
            
            # If no individual objects found, try to find JSON blocks in the text
            if not json_objects:
                json_content = ""
                in_json = False
                
                for line in output_lines:
                    if '{' in line:
                        in_json = True
                        json_content = ""
                    if in_json:
                        json_content += line.strip()
                        if '}' in line:
                            try:
                                parsed_obj = json.loads(json_content)
                                json_objects.append(parsed_obj)
                                in_json = False
                            except json.JSONDecodeError:
                                in_json = False
                                continue
            
            if json_objects:
                print(f"✅ Parsed {len(json_objects)} JSON objects from text-to-JSON script")
                return json_objects
            else:
                print("❌ No valid JSON objects found in text-to-JSON output")
                return None
            
        except subprocess.TimeoutExpired:
            print("❌ Text-to-JSON conversion timed out")
            return None
        except Exception as e:
            print(f"❌ Error in text-to-JSON conversion: {e}")
            return None
    
    def manual_json_input(self, text_instruction: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fallback method for manual JSON input if automated conversion fails
        
        Args:
            text_instruction: Original text instruction
            
        Returns:
            List of manually entered JSON objects or None
        """
        print(f"\n🔄 Manual JSON input for: '{text_instruction}'")
        print("Please provide the JSON format manually:")
        print("Example: [{\"part\": \"block\", \"feature\": \"Extrude1\", \"parameter\": \"Length\", \"new_value\": 50, \"unit\": \"mm\", \"confidence\": 0.95}]")
        
        json_input = input("JSON: ").strip()
        
        try:
            parsed = json.loads(json_input)
            if isinstance(parsed, dict):
                return [parsed]
            elif isinstance(parsed, list):
                return parsed
            else:
                return None
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return None
    
    def create_enhanced_search_query(self, instruction_json: Dict[str, Any]) -> str:
        """
        Create an enhanced search query that maps text-to-JSON features to database terms
        
        Args:
            instruction_json: Parsed instruction in JSON format
            
        Returns:
            Enhanced search query string
        """
        # Feature to database search term mapping - more focused
        feature_mapping = {
            "Extrude1": ["extrude"],
            "Revolve1": ["revolve", "sphere"],
            "Cut1": ["cut"],
            "Fillet1": ["fillet"],
            "Chamfer1": ["chamfer"],
            "Shell1": ["shell", "hollow"],
            "Sweep1": ["sweep"],
            "Loft1": ["loft"],
            "Mirror1": ["mirror"],
            "Pattern1": ["pattern"],
            "Draft1": ["draft"],
            "Hole1": ["hole"],
            "Thicken1": ["thicken"],
            "Wrap1": ["wrap"]
        }
        
        # Parameter to search term mapping - more focused
        parameter_mapping = {
            "Length": ["length", "height"],
            "Width": ["width"],
            "Height": ["height", "length"],
            "Diameter": ["diameter", "circle"],
            "Radius": ["radius", "circle"],
            "Thickness": ["thickness"],
            "Angle": ["angle"]
        }
        
        # Start with the most important terms
        search_terms = []
        
        # Add part name (most important)
        part = instruction_json.get('part', '')
        if part:
            search_terms.append(part)
        
        # Add parameter first (what we're modifying)
        parameter = instruction_json.get('parameter', '')
        if parameter:
            search_terms.append(parameter.lower())
            # Add mapped parameter terms
            if parameter in parameter_mapping:
                search_terms.extend(parameter_mapping[parameter])
        
        # Add feature terms last
        feature = instruction_json.get('feature', '')
        if feature in feature_mapping:
            search_terms.extend(feature_mapping[feature])
        
        # Remove duplicates while preserving order
        unique_terms = []
        seen = set()
        for term in search_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        # Limit to most relevant terms (first 4-5)
        limited_terms = unique_terms[:5]
        
        return ' '.join(limited_terms)
    
    def search_database(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Search the vector database for relevant code examples
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            Dictionary containing search results
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            return results
        except Exception as e:
            print(f"❌ Error searching database: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def format_search_results(self, search_results: Dict[str, Any]) -> str:
        """
        Format search results for the prompt
        
        Args:
            search_results: Search results from ChromaDB
            
        Returns:
            Formatted string with relevant code examples
        """
        formatted_examples = []
        
        if search_results["documents"] and search_results["documents"][0]:
            for i, (doc, metadata) in enumerate(zip(search_results["documents"][0], search_results["metadatas"][0])):
                example = f"""
Example {i+1}:
Title: {metadata.get('title', 'Unknown')}
Description: {metadata.get('description', 'No description')}
Category: {metadata.get('category', 'Unknown')}
Tags: {metadata.get('tags', 'No tags')}
Parameters: {metadata.get('parameters', 'None')}
Distance: {search_results['distances'][0][i]:.3f}

Code:
```python
{doc}
```
"""
                formatted_examples.append(example)
        
        return "\n".join(formatted_examples) if formatted_examples else "No relevant examples found."
    
    def generate_fusion_code(self, instruction_list: List[Dict[str, Any]], search_results: str) -> str:
        """
        Generate Fusion 360 code using Qwen model for multiple instructions
        
        Args:
            instruction_list: List of parsed instructions in JSON format
            search_results: Formatted search results from database
            
        Returns:
            Generated Python code for Fusion 360
        """
        
        # Combine all instructions into a comprehensive description
        task_description = []
        all_values = {}
        
        for instruction in instruction_list:
            part = instruction.get('part', '')
            param = instruction.get('parameter', '')
            value = instruction.get('new_value', 0)
            unit = instruction.get('unit', 'mm')
            
            task_description.append(f"{param}: {value}{unit}")
            all_values[param.lower()] = float(value) / 10  # Divide by 10 for scaling
        
        main_part = instruction_list[0].get('part', 'object')
        task_summary = f"Create {main_part} with " + ", ".join(task_description)
        
        # Create a focused prompt for Qwen
        prompt = f"""Generate Fusion 360 Python code for this task:

TASK: {task_summary}

DIMENSIONS TO USE (ALREADY DIVIDED BY 10 FOR FUSION SCALING):
{chr(10).join([f"- {param}: {value}" for param, value in all_values.items()])}

CRITICAL REQUIREMENTS:
- Use the EXACT values specified above (already scaled for Fusion)
- Do NOT ask user for any input - use hardcoded values
- Do NOT include any unit conversion code
- Do NOT set units manager or defaultLengthUnits

EXAMPLES FROM DATABASE:
{search_results}

Generate working Fusion 360 Python code with:
- import adsk.core, adsk.fusion, traceback
- def run(context): with try/except
- def stop(context): pass
- NO units management code
- Use the exact scaled values shown above
- Create complete geometry as specified

Code only, no explanations:"""

        try:
            print(f"Calling Ollama with model: {self.ollama_model}")
            print(f"Task: {task_summary}")
            print(f"Values: {all_values}")
            
            # Call Ollama API with simpler options
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "max_tokens": 1500
                    }
                },
                timeout=60
            )
            
            print(f"Ollama response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                print(f"✅ Generated {len(generated_text)} characters")
                if generated_text:
                    return generated_text
                else:
                    print("❌ Empty response from Ollama")
                    return ""
            else:
                print(f"❌ Ollama API error: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    print(f"Raw error response: {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            print("❌ Ollama request timed out")
            return ""
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Ollama - is it running?")
            return ""
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama request error: {e}")
            return ""
        except Exception as e:
            print(f"❌ Unexpected error calling Ollama: {e}")
            traceback.print_exc()
            return ""
    
    def refine_generated_code(self, raw_code: str) -> str:
        """
        Clean and refine the generated code
        
        Args:
            raw_code: Raw code from Qwen
            
        Returns:
            Cleaned and properly formatted code
        """
        # Remove any markdown code blocks
        if "```python" in raw_code:
            raw_code = raw_code.split("```python")[1].split("```")[0]
        elif "```" in raw_code:
            raw_code = raw_code.split("```")[1].split("```")[0]
        
        # Clean up the code
        lines = raw_code.strip().split('\n')
        
        # Ensure proper imports
        has_imports = any("import adsk" in line for line in lines[:5])
        
        if not has_imports:
            import_lines = [
                "import adsk.core, adsk.fusion, traceback",
                ""
            ]
            lines = import_lines + lines
        
        # Ensure proper function structure
        has_stop_function = any("def stop(context):" in line for line in lines)
        
        if not has_stop_function:
            lines.extend([
                "",
                "def stop(context):",
                "    pass"
            ])
        
        return '\n'.join(lines)
    
    def process_text_instruction(self, text_instruction: str) -> Optional[str]:
        """
        Main method to process a text instruction and generate Fusion 360 code
        
        Args:
            text_instruction: Natural language instruction
            
        Returns:
            Generated Fusion 360 Python code or None if failed
        """
        print(f"\nProcessing: '{text_instruction}'")
        
        # Step 1: Convert text to JSON
        print("Converting text to JSON...")
        instruction_list = self.text_to_json(text_instruction)
        
        if not instruction_list:
            print("❌ Text-to-JSON conversion failed, trying manual input...")
            instruction_list = self.manual_json_input(text_instruction)
            
            if not instruction_list:
                print("❌ Failed to get JSON instruction")
                return None
        
        print(f"✅ JSON instructions ({len(instruction_list)} total):")
        for i, instruction in enumerate(instruction_list):
            print(f"  {i+1}. {json.dumps(instruction, indent=2)}")
        
        # Step 2: Create enhanced search query using first instruction
        enhanced_query = self.create_enhanced_search_query(instruction_list[0])
        print(f"🔎 Enhanced search query: '{enhanced_query}'")
        
        # Search vector database
        search_results = self.search_database(enhanced_query, n_results=5)
        formatted_results = self.format_search_results(search_results)
        
        num_results = len(search_results['documents'][0]) if search_results['documents'] else 0
        print(f"📚 Found {num_results} relevant examples")
        
        # Step 3: Generate code with Qwen
        print("🤖 Generating code with Qwen...")
        raw_code = self.generate_fusion_code(instruction_list, formatted_results)
        
        if not raw_code:
            print("❌ Failed to generate code")
            return None
        
        # Step 4: Refine the generated code
        refined_code = self.refine_generated_code(raw_code)
        
        print("✅ Code generation complete!")
        return refined_code
    
    def save_code(self, code: str, filename: str = None) -> str:
        """
        Save generated code to file
        
        Args:
            code: Generated code
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            import time
            timestamp = int(time.time())
            filename = f"fusion_generated_{timestamp}.py"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(code)
            
            full_path = os.path.abspath(filename)
            print(f"Code saved to: {full_path}")
            return full_path
            
        except Exception as e:
            print(f"❌ Error saving code: {e}")
            return ""

def main():
    """
    Main interactive loop
    """
    print("Integrated Fusion 360 Code Generator")
    print("=" * 60)
    print("Text → JSON → Vector Search → Code Generation")
    print("=" * 60)
    
    # Initialize the generator
    try:
        generator = IntegratedFusionGenerator()
        print("✅ Generator initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing generator: {e}")
        traceback.print_exc()
        return
    
    # Main loop
    while True:
        print("\n" + "=" * 60)
        print("Enter your instruction in natural language:")
        print("Examples:")
        print("  - 'change cylinder length to 100mm'")
        print("  - 'create a rectangular block 50x30x20mm'")
        print("  - 'modify the tube diameter to 25mm'")
        print("  - 'exit' to quit")
        
        user_input = input("\nInstruction: ").strip()
        
        if user_input.lower() == 'exit':
            print("END!")
            break
        
        if not user_input:
            print("❌ Please enter a valid instruction")
            continue
        
        try:
            # Process the instruction
            generated_code = generator.process_text_instruction(user_input)
            
            if generated_code:
                print("\nGenerated Fusion 360 Code:")
                print("-" * 60)
                print(generated_code)
                print("-" * 60)
                
                # Ask if user wants to save the code
                save_choice = input("\nSave code to file? (y/N): ").strip().lower()
                if save_choice == 'y':
                    filename = input("Enter filename (press Enter for auto-generated): ").strip()
                    if not filename:
                        filename = None
                    
                    saved_path = generator.save_code(generated_code, filename)
                    if saved_path:
                        print(f"✅ Ready to run in Fusion 360!")
                        print(f"Instructions:")
                        print(f"   1. Open Fusion 360")
                        print(f"   2. Go to Scripts and Add-ins")
                        print(f"   3. Select 'Run Script'")
                        print(f"   4. Choose the saved file: {saved_path}")
                        print(f"   5. Click 'Run'")
            else:
                print("❌ Failed to generate code")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            break
        except Exception as e:
            print(f"❌ Error processing instruction: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()