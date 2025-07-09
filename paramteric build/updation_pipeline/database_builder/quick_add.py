"""
Quick script to add any code to the Fusion 360 vector database
"""

from vector_db_setup import FusionVectorDB
import sys
import json

def quick_add_from_file(filepath):
    """Add code from a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print(f"📁 Reading code from: {filepath}")
        print(f"📏 Code length: {len(code)} characters")
        
        return add_code_interactive(code)
        
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def add_code_interactive(code=None):
    """Interactive code addition"""
    
    print("\n" + "="*50)
    print("🚀 QUICK ADD CODE TO FUSION 360 DATABASE")
    print("="*50)
    
    # Get code if not provided
    if not code:
        print("📝 Enter your code (paste and press Ctrl+Z on Windows or Ctrl+D on Unix when done):")
        print("-" * 30)
        
        code_lines = []
        try:
            while True:
                line = input()
                code_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        
        code = '\n'.join(code_lines).strip()
    
    if not code:
        print("❌ No code provided!")
        return False
    
    # Show code preview
    preview_lines = code.split('\n')[:5]
    print(f"\n📋 Code Preview ({len(code)} chars):")
    for line in preview_lines:
        if line.strip():
            print(f"   {line}")
    if len(code.split('\n')) > 5:
        print("   ...")
    
    # Get metadata
    print("\n📝 Enter metadata:")
    title = input("Title: ").strip()
    if not title:
        print("❌ Title is required!")
        return False
    
    description = input("Description: ").strip()
    if not description:
        description = "Fusion 360 code example"
    
    # Category selection
    print("\n📁 Select category:")
    categories = [
        "geometry", "sketch", "feature", "modify", "transform", "resize",
        "ui", "template", "utility", "material", "assembly", "simulation",
        "export", "io", "cam", "drawing", "parameters", "add-in", "automation"
    ]
    for i, cat in enumerate(categories, 1):
        print(f"   {i}. {cat}")
    try:
        cat_choice = input("Category (number or name): ").strip()
        if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(categories):
            category = categories[int(cat_choice) - 1]
        else:
            category = cat_choice if cat_choice in categories else "general"
    except (ValueError, IndexError):
        category = "general"
    
    # Tags
    print("\n🏷️  Enter tags (comma-separated, or press Enter for auto-generated):")
    tags_input = input("Tags: ").strip()
    
    if tags_input:
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
    else:
        tags = auto_generate_tags(code, title, description)
        print(f"   Auto-generated tags: {', '.join(tags)}")
    
    # Parameters (optional)
    print("\n⚙️  Add parameters? (y/N): ", end="")
    add_params = input().strip().lower() in ['y', 'yes']
    
    parameters = {}
    if add_params:
        print("Enter parameters (key: value), empty line to finish:")
        while True:
            param_input = input("   ").strip()
            if not param_input:
                break
            if ':' in param_input:
                key, value = param_input.split(':', 1)
                parameters[key.strip()] = value.strip()
    
    # Add database ID if found in code
    if "Database ID:" in code:
        for line in code.split('\n'):
            if "Database ID:" in line:
                db_id = line.split("Database ID:")[-1].strip().lstrip('#').strip()
                parameters["database_id"] = db_id
                break
    
    # Connect to database and add
    try:
        db = FusionVectorDB(db_path="./chroma_cad_db")
        db.setup_database(reset=False)
        
        code_id = db.add_code_example(
            code=code,
            title=title,
            description=description,
            tags=tags,
            category=category,
            parameters=parameters
        )
        
        print(f"\n✅ Code added successfully!")
        print(f"   ID: {code_id}")
        print(f"   Title: {title}")
        print(f"   Category: {category}")
        print(f"   Tags: {', '.join(tags)}")
        
        # Show updated stats
        stats = db.get_stats()
        print(f"\n📊 Database now has {stats['total_examples']} examples")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding to database: {e}")
        return False

def auto_generate_tags(code, title, description):
    """Auto-generate tags based on code content"""
    tags = set()
    
    # From title and description
    title_words = title.lower().replace('-', ' ').replace('_', ' ').split()
    desc_words = description.lower().replace('-', ' ').replace('_', ' ').split()
    
    fusion_keywords = {
        'cylinder': 'cylinder',
        'sphere': 'sphere',
        'box': 'box',
        'extrude': 'extrude',
        'revolve': 'revolve',
        'sweep': 'sweep',
        'loft': 'loft',
        'hollow': 'hollow',
        'solid': 'solid',
        'sketch': 'sketch',
        'circle': 'circle',
        'rectangle': 'rectangle',
        'line': 'line',
        'arc': 'arc',
        'spline': 'spline',
        'fillet': 'fillet',
        'chamfer': 'chamfer',
        'pattern': 'pattern',
        'mirror': 'mirror',
        'joint': 'joint',
        'sheet metal': 'sheetmetal',
        'sheetmetal': 'sheetmetal',
        'user': 'user-input',
        'input': 'user-input',
        'dialog': 'dialog',
        'ui': 'ui',
        'interface': 'ui',
        'parametric': 'parametric',
        'parameter': 'parameters',
        'units': 'parameters',
        'modify': 'modify',
        'resize': 'resize',
        'scale': 'scale',
        'transform': 'transform',
        'component': 'component',
        'assembly': 'assembly',
        'material': 'material',
        'appearance': 'appearance',
        'export': 'export',
        'dxf': 'export',
        'bom': 'bom',
        'csv': 'io',
        'excel': 'io',
        'file': 'io',
        'cam': 'cam',
        'gcode': 'cam',
        'drawing': 'drawing',
        'add-in': 'add-in',
        'command': 'add-in',
        'automation': 'automation',
        'database': 'database',
        'vector': 'vector-db'
    }
    
    code_lower = code.lower()
    for keyword, tag in fusion_keywords.items():
        if (keyword in title_words or keyword in desc_words or keyword in code_lower):
            tags.add(tag)
    
    # API-specific tags
    if 'inputbox' in code_lower: tags.add('user-input')
    if 'messagebox' in code_lower: tags.add('dialog')
    if 'extrudefeatures' in code_lower: tags.add('extrude')
    if 'revolvefeatures' in code_lower: tags.add('revolve')
    if 'sweepfeatures' in code_lower: tags.add('sweep')
    if 'loftfeatures' in code_lower: tags.add('loft')
    if 'patternfeatures' in code_lower: tags.add('pattern')
    if 'mirrorfeatures' in code_lower: tags.add('mirror')
    if 'filletfeatures' in code_lower: tags.add('fillet')
    if 'chamferfeatures' in code_lower: tags.add('chamfer')
    if 'jointfeatures' in code_lower: tags.add('joint')
    if 'sheetmetalfeatures' in code_lower: tags.add('sheetmetal')
    if 'scalefeatures' in code_lower: tags.add('scale')
    if 'movefeatures' in code_lower: tags.add('transform')
    if 'transform' in code_lower: tags.add('transform')
    if 'scale' in code_lower: tags.add('scale')
    if 'modify' in code_lower: tags.add('modify')
    if 'offset' in code_lower: tags.add('modify')
    
    return list(tags) if tags else ['fusion360', 'code']

def main():
    """Main function"""
    if len(sys.argv) > 1:
        quick_add_from_file(sys.argv[1])
    else:
        add_code_interactive()

if __name__ == "__main__":
    main()
