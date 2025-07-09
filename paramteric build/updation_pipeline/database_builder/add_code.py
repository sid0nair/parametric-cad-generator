from database.vector_db_setup import FusionVectorDB

def add_new_code():
    """Add new code examples to the database"""
    
    # Connect to existing database
    db = FusionVectorDB(db_path="./chroma_cad_db")
    db.setup_database(reset=False)  # Don't reset, just connect
    
    # Add your complete hollow cylinder code
    hollow_cylinder_code = """# Database ID: fusion360_hollow_cylinder_complete_working_code
import adsk.core, adsk.fusion, traceback
handlers = []
def run(context):
    ui = None
    try:
        # ——— Setup ———
        app    = adsk.core.Application.get()
        ui     = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root   = design.rootComponent
        # ——— User Inputs (mm → cm) ———
        outer_mm = float(ui.inputBox('Outer diameter (mm)', 'Tube Dimensions', '50')[0])
        inner_mm = float(ui.inputBox('Inner diameter (mm)', 'Tube Dimensions', '30')[0])
        height_mm= float(ui.inputBox('Height (mm)',        'Tube Dimensions', '20')[0])
        outer_cm = outer_mm / 10.0
        inner_cm = inner_mm / 10.0
        height_cm= height_mm/ 10.0
        # ——— Sketch two concentric circles ———
        sketches = root.sketches
        plane    = root.xYConstructionPlane
        sketch   = sketches.add(plane)
        circles  = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0),
            outer_cm/2
        )
        circles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0),
            inner_cm/2
        )
        # ——— Select the annular profile (one with 2 loops) ———
        targetProfile = None
        for prof in sketch.profiles:
            # profileLoops.count == 2 means an outer loop minus inner loop
            if prof.profileLoops.count == 2:
                targetProfile = prof
                break
        if not targetProfile:
            ui.messageBox('Could not find the hollow profile.')
            return
        # ——— Extrude the tube ———
        extrudes  = root.features.extrudeFeatures
        extInput  = extrudes.createInput(
                      targetProfile,
                      adsk.fusion.FeatureOperations.NewBodyFeatureOperation
                    )
        distance  = adsk.core.ValueInput.createByReal(height_cm)
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)
        ui.messageBox(
            'Hollow cylinder created: Ø{:.1f}×Ø{:.1f}×{:.1f} mm'.format(
                outer_mm, inner_mm, height_mm
            )
        )
    except:
        if ui:
            ui.messageBox('Failed:\\n{}'.format(traceback.format_exc()))
def stop(context):
    # Nothing to clean up
    pass"""
    
    db.add_code_example(
        code=hollow_cylinder_code,
        title="Complete Hollow Cylinder with User Input",
        description="Complete working Fusion 360 add-in that creates a hollow cylinder with user input dialogs for outer diameter, inner diameter, and height. Handles unit conversion (mm to cm) and proper profile selection.",
        tags=["cylinder", "hollow", "tube", "user-input", "dialog", "sketch", "extrude", "parametric", "complete", "working", "addon", "concentric-circles", "annular", "profile"],
        category="geometry",
        parameters={
            "outer_diameter": "float - outer diameter in mm (user input)",
            "inner_diameter": "float - inner diameter in mm (user input)", 
            "height": "float - height in mm (user input)",
            "unit_conversion": "mm to cm automatic conversion",
            "user_interaction": ["inputBox dialogs", "messageBox confirmation"],
            "operations": ["sketch", "concentric circles", "profile selection", "extrude"],
            "features_used": ["sketches", "sketchCircles", "profiles", "extrudeFeatures"],
            "profile_logic": "searches for profile with 2 loops (annular)",
            "structure": "complete add-in with run/stop functions",
            "database_id": "fusion360_hollow_cylinder_complete_working_code"
        }
    )
    
    print("✓ Added complete hollow cylinder code with user input")
    
    # Show updated stats
    stats = db.get_stats()
    print(f"Database now has {stats['total_examples']} examples")
    print(f"Categories: {stats['categories']}")

# Function to add any custom code
def add_custom_code(code, title, description, tags=None, category="general", parameters=None):
    """Add custom code to the database"""
    
    db = FusionVectorDB(db_path="./chroma_cad_db")
    db.setup_database(reset=False)
    
    code_id = db.add_code_example(
        code=code,
        title=title,
        description=description,
        tags=tags or [],
        category=category,
        parameters=parameters or {}
    )
    
    print(f"✓ Added code: {title} (ID: {code_id})")
    return code_id

# Interactive mode
def interactive_add():
    """Interactive mode to add code"""
    
    print("=== Add Code to Fusion 360 Vector Database ===")
    
    # Get code input
    print("\nPaste your code (press Ctrl+D when done):")
    code_lines = []
    try:
        while True:
            line = input()
            code_lines.append(line)
    except EOFError:
        pass
    
    code = '\n'.join(code_lines)
    
    if not code.strip():
        print("No code provided. Exiting.")
        return
    
    # Get metadata
    title = input("\nTitle: ")
    description = input("Description: ")
    category = input("Category (geometry/ui/template/utility): ") or "general"
    tags_input = input("Tags (comma-separated): ")
    tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
    
    # Add to database
    add_custom_code(code, title, description, tags, category)
    
    print("\n✅ Code added successfully!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_add()
    else:
        # Add example hollow cylinder code
        add_new_code()
        
        print("\nTo add code interactively:")
        print("python add_code.py interactive")