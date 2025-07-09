#!/usr/bin/env python3
"""
Test script to verify the Qwen Coder Bot system is working correctly
"""

import json
import requests
import chromadb
import os
import sys
from pathlib import Path

def test_chromadb_connection():
    """Test ChromaDB connection and collection"""
    print("🔍 Testing ChromaDB connection...")
    
    try:
        client = chromadb.PersistentClient(path="./chroma_cad_db")
        
        # List collections
        collections = client.list_collections()
        print(f"✅ Found {len(collections)} collections")
        
        # Check specific collection
        try:
            collection = client.get_collection("fusion360_code_examples")
            count = collection.count()
            print(f"✅ Collection 'fusion360_code_examples' has {count} documents")
            
            # Test a sample query
            if count > 0:
                results = collection.query(
                    query_texts=["cylinder"],
                    n_results=min(2, count),
                    include=['documents', 'metadatas']
                )
                
                if results['documents'] and results['documents'][0]:
                    print(f"✅ Sample query returned {len(results['documents'][0])} results")
                    
                    # Show first result metadata
                    first_meta = results['metadatas'][0][0] if results['metadatas'][0] else {}
                    print(f"   First result: {first_meta.get('title', 'No title')}")
                else:
                    print("⚠️ Sample query returned no results")
            
            return True
            
        except Exception as e:
            print(f"❌ Error accessing collection: {e}")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False

def test_ollama_connection():
    """Test Ollama connection and model availability"""
    print("\n🤖 Testing Ollama connection...")
    
    try:
        # Test basic connection
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ Ollama is running (version: {version_info.get('version', 'unknown')})")
        else:
            print(f"⚠️ Ollama responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False
    
    # Test model availability
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()
            model_names = [model['name'] for model in models.get('models', [])]
            print(f"✅ Available models: {len(model_names)}")
            
            # Check for Qwen models
            qwen_models = [name for name in model_names if 'qwen' in name.lower()]
            if qwen_models:
                print(f"✅ Qwen models found: {qwen_models}")
                return True
            else:
                print("⚠️ No Qwen models found")
                print("   Install with: ollama pull qwen2.5-coder:7b")
                return False
        else:
            print(f"❌ Failed to get model list: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def test_simple_generation():
    """Test simple code generation"""
    print("\n🧪 Testing simple code generation...")
    
    try:
        # Import the bot
        sys.path.append('.')
        from qwen_coder_bot import QwenCoderBot
        
        # Create bot instance
        bot = QwenCoderBot()
        
        # Test with a simple instruction
        test_instruction = {
            "part": "cylinder",
            "feature": "Extrude1",
            "parameter": "Length", 
            "new_value": 100,
            "unit": "mm",
            "confidence": 0.95
        }
        
        print(f"   Testing instruction: {test_instruction}")
        
        # Generate code
        generated_code = bot.process_instruction(test_instruction)
        
        if generated_code and len(generated_code) > 100:
            print("✅ Code generation successful")
            print(f"   Generated {len(generated_code)} characters of code")
            
            # Check for basic Fusion 360 elements
            required_elements = [
                "import adsk.core",
                "import adsk.fusion", 
                "def run(context):",
                "def stop(context):"
            ]
            
            missing_elements = [elem for elem in required_elements if elem not in generated_code]
            
            if not missing_elements:
                print("✅ Generated code contains all required elements")
                return True
            else:
                print(f"⚠️ Generated code missing: {missing_elements}")
                return False
        else:
            print("❌ Code generation failed or produced insufficient output")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import QwenCoderBot: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in code generation test: {e}")
        return False

def test_file_dependencies():
    """Test if required files exist"""
    print("\n📁 Testing file dependencies...")
    
    required_files = [
        "qwen_coder_bot.py",
        "integrated_fusion_generator.py"
    ]
    
    optional_files = [
        "text_2_JSON.py",
        "requirements.txt"
    ]
    
    all_good = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} is missing (required)")
            all_good = False
    
    for file in optional_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"⚠️ {file} is missing (optional)")
    
    return all_good

def test_python_dependencies():
    """Test if required Python packages are installed"""
    print("\n🐍 Testing Python dependencies...")
    
    required_packages = [
        "chromadb",
        "requests"
    ]
    
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            all_good = False
    
    if not all_good:
        print("\n   Install missing packages with:")
        print("   pip install chromadb requests")
    
    return all_good

def main():
    """Run all tests"""
    print("🧪 Fusion 360 Qwen Coder Bot System Test")
    print("=" * 60)
    
    tests = [
        ("Python Dependencies", test_python_dependencies),
        ("File Dependencies", test_file_dependencies), 
        ("ChromaDB Connection", test_chromadb_connection),
        ("Ollama Connection", test_ollama_connection),
        ("Simple Code Generation", test_simple_generation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Running: {test_name}")
        print('=' * 60)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print('=' * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python integrated_fusion_generator.py")
        print("2. Enter a natural language instruction")
        print("3. Save and use the generated code in Fusion 360")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please fix the issues above.")
        
        # Provide specific guidance
        if not results.get("Python Dependencies", True):
            print("\n📦 Install Python dependencies:")
            print("   pip install chromadb requests")
        
        if not results.get("Ollama Connection", True):
            print("\n🤖 Start Ollama:")
            print("   ollama serve")
            print("   ollama pull qwen2.5-coder:7b")
        
        if not results.get("ChromaDB Connection", True):
            print("\n🗄️ Check ChromaDB setup:")
            print("   Ensure ./chroma_db directory exists")
            print("   Verify collection 'fusion360_code_examples' has data")

if __name__ == "__main__":
    main()