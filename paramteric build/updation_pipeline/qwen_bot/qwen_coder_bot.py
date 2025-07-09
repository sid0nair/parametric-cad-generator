import chromadb
import json
import requests
import subprocess
import traceback
from typing import Dict, List, Any, Optional
import os
from pathlib import Path

class QwenCoderBot:
    """
    A bot that uses Qwen model to generate Fusion 360 code based on vector database retrieval
    """
    
    def __init__(self, 
                 db_path: str = "./chroma_cad_db",
                 collection_name: str = "fusion360_code_examples",
                 ollama_model: str = "qwen2.5-coder:7b"):
        """
        Initialize the Qwen Coder Bot
        
        Args:
            db_path: Path to ChromaDB database
            collection_name: Name of the collection in ChromaDB
            ollama_model: Ollama model to use for code generation
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.ollama_model = ollama_model
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection(name=collection_name)
        
        # Ollama API endpoint
        self.ollama_url = "http://localhost:11434/api/generate"
        
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
            print(f"Error searching database: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def format_search_results(self, results: Dict[str, Any]) -> str:
        """
        Format search results for the prompt
        
        Args:
            results: Search results from ChromaDB
            
        Returns:
            Formatted string with relevant code examples
        """
        formatted_examples = []
        
        if results["documents"] and results["documents"][0]:
            for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                example = f"""
Example {i+1}:
Title: {metadata.get('title', 'Unknown')}
Description: {metadata.get('description', 'No description')}
Category: {metadata.get('category', 'Unknown')}
Tags: {metadata.get('tags', 'No tags')}
Parameters: {metadata.get('parameters', 'None')}

Code:
```python
{doc}
```
"""
                formatted_examples.append(example)
        
        return "\n".join(formatted_examples) if formatted_examples else "No relevant examples found."
    
    def generate_code_with_qwen(self, instruction_json: Dict[str, Any], search_results: str) -> str:
        """
        Generate Fusion 360 code using Qwen model
        
        Args:
            instruction_json: Parsed instruction in JSON format
            search_results: Formatted search results from database
            
        Returns:
            Generated Python code for Fusion 360
        """
        
        # Create a comprehensive prompt for Qwen
        prompt = f"""You are an expert Fusion 360 API programmer. Based on the instruction and examples provided, generate complete, working Python code for Fusion 360.

INSTRUCTION TO IMPLEMENT:
{json.dumps(instruction_json, indent=2)}

RELEVANT CODE EXAMPLES FROM DATABASE:
{search_results}

REQUIREMENTS:
1. Generate complete, working Fusion 360 Python code
2. Use the adsk.core and adsk.fusion APIs correctly
3. Include proper error handling with try/except blocks
4. Force units to mm at the beginning
5. Use the standard run(context) and stop(context) function structure
6. Include user input dialogs for parameters when needed
7. Add success/failure message boxes
8. Follow the patterns shown in the examples above

SPECIFIC INSTRUCTION:
- Part: {instruction_json.get('part', 'Unknown')}
- Feature: {instruction_json.get('feature', 'Unknown')}
- Parameter: {instruction_json.get('parameter', 'Unknown')}
- New Value: {instruction_json.get('new_value', 'Unknown')}
- Unit: {instruction_json.get('unit', 'mm')}

Generate only the Python code, no explanations. Start with imports and include the complete implementation:"""

        try:
            # Call Ollama API
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Lower temperature for more consistent code
                        "top_p": 0.9,
                        "max_tokens": 2048
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                return f"Error calling Ollama: HTTP {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Ollama: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"
    
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
        
        # Ensure proper imports
        lines = raw_code.strip().split('\n')
        has_imports = any("import adsk" in line for line in lines[:5])
        
        if not has_imports:
            import_lines = [
                "import adsk.core, adsk.fusion, traceback",
                ""
            ]
            lines = import_lines + lines
        
        # Ensure proper function structure
        has_run_function = any("def run(context):" in line for line in lines)
        has_stop_function = any("def stop(context):" in line for line in lines)
        
        if not has_stop_function:
            lines.extend([
                "",
                "def stop(context):",
                "    pass"
            ])
        
        return '\n'.join(lines)
    
    def process_instruction(self, instruction_json: Dict[str, Any]) -> str:
        """
        Main method to process an instruction and generate code
        
        Args:
            instruction_json: Parsed instruction in JSON format
            
        Returns:
            Generated Fusion 360 Python code
        """
        print(f"🔍 Processing instruction: {instruction_json}")
        
        # Create search query from instruction
        search_query = f"{instruction_json.get('part', '')} {instruction_json.get('feature', '')} {instruction_json.get('parameter', '')}"
        print(f"🔎 Searching database with query: '{search_query}'")
        
        # Search database for relevant examples
        search_results = self.search_database(search_query, n_results=3)
        formatted_results = self.format_search_results(search_results)
        
        print(f"📚 Found {len(search_results['documents'][0]) if search_results['documents'] else 0} relevant examples")
        
        # Generate code using Qwen
        print("🤖 Generating code with Qwen...")
        raw_code = self.generate_code_with_qwen(instruction_json, formatted_results)
        
        # Refine the generated code
        refined_code = self.refine_generated_code(raw_code)
        
        return refined_code
    
    def save_generated_code(self, code: str, filename: str = "generated_fusion_code.py") -> str:
        """
        Save the generated code to a file
        
        Args:
            code: Generated code
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = Path(filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"💾 Code saved to: {output_path.absolute()}")
            return str(output_path.absolute())
            
        except Exception as e:
            print(f"❌ Error saving code: {e}")
            return ""

def main():
    """
    Main function to demonstrate the Qwen Coder Bot
    """
    print("🚀 Qwen Coder Bot for Fusion 360")
    print("=" * 50)
    
    # Initialize the bot
    try:
        bot = QwenCoderBot()
        print("✅ Bot initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing bot: {e}")
        return
    
    # Example usage
    while True:
        print("\n" + "=" * 50)
        print("Enter instruction JSON (or 'exit' to quit):")
        print("Example: {\"part\": \"cylinder\", \"feature\": \"Extrude1\", \"parameter\": \"Length\", \"new_value\": 100, \"unit\": \"mm\", \"confidence\": 0.95}")
        
        user_input = input("\nJSON: ").strip()
        
        if user_input.lower() == 'exit':
            break
        
        try:
            # Parse the JSON instruction
            instruction_json = json.loads(user_input)
            
            # Process the instruction
            generated_code = bot.process_instruction(instruction_json)
            
            if generated_code:
                print("\n🎉 Generated Code:")
                print("-" * 50)
                print(generated_code)
                print("-" * 50)
                
                # Ask if user wants to save the code
                save_choice = input("\n💾 Save code to file? (y/N): ").strip().lower()
                if save_choice == 'y':
                    filename = input("Enter filename (default: generated_fusion_code.py): ").strip()
                    if not filename:
                        filename = "generated_fusion_code.py"
                    
                    saved_path = bot.save_generated_code(generated_code, filename)
                    if saved_path:
                        print(f"✅ Code saved successfully!")
                        print(f"📁 Location: {saved_path}")
                        print("📋 You can now run this in Fusion 360's script environment")
            else:
                print("❌ Failed to generate code")
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"❌ Error processing instruction: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()