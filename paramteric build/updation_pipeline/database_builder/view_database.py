from vector_db_setup import FusionVectorDB
import json
from datetime import datetime

def view_database_contents():
    """View all contents of the Fusion 360 vector database"""
    
    try:
        # Connect to database
        db = FusionVectorDB(db_path="./chroma_cad_db")
        db.setup_database(reset=False)
        
        print("=" * 60)
        print("🗃️  FUSION 360 VECTOR DATABASE CONTENTS")
        print("=" * 60)
        
        # Get statistics
        stats = db.get_stats()
        print(f"📊 Database Statistics:")
        print(f"   Total Examples: {stats['total_examples']}")
        print(f"   Collection: {stats['collection_name']}")
        print(f"   Categories: {stats['categories']}")
        print()
        
        if stats['total_examples'] == 0:
            print("❌ Database is empty!")
            return
            
        # Get all examples
        all_examples = db.get_all_examples()
        
        for i, example in enumerate(all_examples, 1):
            print(f"📝 Example #{i}")
            print("-" * 40)
            
            metadata = example['metadata']
            
            # Basic info
            print(f"🏷️  Title: {metadata.get('title', 'N/A')}")
            print(f"📁 Category: {metadata.get('category', 'N/A')}")
            print(f"📝 Description: {metadata.get('description', 'N/A')}")
            
            # Tags
            tags = json.loads(metadata.get('tags', '[]'))
            if tags:
                print(f"🏷️  Tags: {', '.join(tags)}")
            
            # Parameters
            params = json.loads(metadata.get('parameters', '{}'))
            if params:
                print("⚙️  Parameters:")
                for key, value in params.items():
                    if isinstance(value, list):
                        print(f"   {key}: {', '.join(map(str, value))}")
                    else:
                        print(f"   {key}: {value}")
            
            # Code preview
            code_lines = example['document'].split('\n')
            code_start = None
            for j, line in enumerate(code_lines):
                if 'import adsk' in line or 'def ' in line:
                    code_start = j
                    break
            
            if code_start is not None:
                preview_lines = code_lines[code_start:code_start+5]
                print("💻 Code Preview:")
                for line in preview_lines:
                    if line.strip():
                        print(f"   {line}")
                print("   ...")
            
            print(f"📏 Code Length: {metadata.get('code_length', 'N/A')} characters")
            print(f"🆔 ID: {example['id']}")
            print()
        
    except Exception as e:
        print(f"❌ Error viewing database: {e}")

def search_database(query):
    """Search the database with a query"""
    
    try:
        db = FusionVectorDB(db_path="./chroma_cad_db")
        db.setup_database(reset=False)
        
        print(f"🔍 Searching for: '{query}'")
        print("=" * 50)
        
        results = db.search_code_examples(query, n_results=5)
        
        if not results:
            print("❌ No results found!")
            return
            
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            distance = result.get('distance', 'N/A')
            
            print(f"🎯 Result #{i} (Distance: {distance:.3f})" if distance != 'N/A' else f"🎯 Result #{i}")
            print(f"   Title: {metadata.get('title', 'N/A')}")
            print(f"   Category: {metadata.get('category', 'N/A')}")
            print(f"   Tags: {', '.join(json.loads(metadata.get('tags', '[]')))}")
            print()
            
    except Exception as e:
        print(f"❌ Search error: {e}")

def view_by_category(category):
    """View examples by category"""
    
    try:
        db = FusionVectorDB(db_path="./chroma_cad_db")
        db.setup_database(reset=False)
        
        print(f"📁 Category: '{category}'")
        print("=" * 40)
        
        results = db.search_code_examples("", category=category, n_results=10)
        
        if not results:
            print(f"❌ No examples found in category '{category}'!")
            return
            
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            print(f"{i}. {metadata.get('title', 'N/A')}")
            print(f"   {metadata.get('description', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"❌ Error viewing category: {e}")

def interactive_explorer():
    """Interactive database explorer"""
    
    while True:
        print("\n" + "=" * 50)
        print("🔍 FUSION 360 DATABASE EXPLORER")
        print("=" * 50)
        print("1. View all contents")
        print("2. Search database")
        print("3. View by category")
        print("4. Database statistics")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            view_database_contents()
        elif choice == '2':
            query = input("Enter search query: ").strip()
            if query:
                search_database(query)
        elif choice == '3':
            category = input("Enter category (geometry/ui/template/utility): ").strip()
            if category:
                view_by_category(category)
        elif choice == '4':
            db = FusionVectorDB(db_path="./chroma_cad_db")
            db.setup_database(reset=False)
            stats = db.get_stats()
            print(f"\n📊 Statistics:")
            print(f"   Total: {stats['total_examples']}")
            print(f"   Categories: {stats['categories']}")
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # Default: show all contents
        view_database_contents()
    elif sys.argv[1] == "interactive":
        interactive_explorer()
    elif sys.argv[1] == "search":
        if len(sys.argv) > 2:
            search_database(" ".join(sys.argv[2:]))
        else:
            query = input("Enter search query: ")
            search_database(query)
    elif sys.argv[1] == "category":
        if len(sys.argv) > 2:
            view_by_category(sys.argv[2])
        else:
            category = input("Enter category: ")
            view_by_category(category)
    else:
        print("Usage:")
        print("  python view_database.py                    # View all contents")
        print("  python view_database.py interactive        # Interactive mode")
        print("  python view_database.py search <query>     # Search database")
        print("  python view_database.py category <name>    # View by category")