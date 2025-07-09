import chromadb
from chromadb.config import Settings
import uuid
import json
import os
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FusionVectorDB:
    def __init__(self, db_path: str = "./fusion_vector_db"):
        """Initialize the Fusion 360 Vector Database"""
        self.db_path = db_path
        self.client = None
        self.collection = None
        self.collection_name = "fusion360_code_examples"
        
    def setup_database(self, reset: bool = False):
        """Setup ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Reset database if requested
            if reset:
                logger.info("Resetting database...")
                self.client.reset()
                
            # Create or get collection
            try:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Fusion 360 API code examples and patterns"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            except Exception as e:
                if "already exists" in str(e):
                    self.collection = self.client.get_collection(name=self.collection_name)
                    logger.info(f"Using existing collection: {self.collection_name}")
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            raise
            
    def add_code_example(self, 
                        code: str, 
                        title: str, 
                        description: str, 
                        tags: List[str] = None, 
                        category: str = "general",
                        parameters: Dict[str, Any] = None):
        """Add a code example to the vector database"""
        try:
            if not self.collection:
                raise ValueError("Database not initialized. Call setup_database() first.")
                
            # Generate unique ID
            code_id = str(uuid.uuid4())
            
            # Prepare metadata
            metadata = {
                "title": title,
                "description": description,
                "category": category,
                "tags": json.dumps(tags or []),
                "parameters": json.dumps(parameters or {}),
                "code_length": len(code),
                "language": "python"
            }
            
            # Create document text for embedding (combines all searchable text)
            document_text = f"""
            Title: {title}
            Description: {description}
            Category: {category}
            Tags: {', '.join(tags or [])}
            Code:
            {code}
            """
            
            # Add to collection
            self.collection.add(
                documents=[document_text],
                metadatas=[metadata],
                ids=[code_id]
            )
            
            logger.info(f"Added code example: {title} (ID: {code_id})")
            return code_id
            
        except Exception as e:
            logger.error(f"Error adding code example: {e}")
            raise
            
    def search_code_examples(self, 
                           query: str, 
                           n_results: int = 5,
                           category: str = None,
                           tags: List[str] = None) -> List[Dict[str, Any]]:
        """Search for code examples using vector similarity"""
        try:
            if not self.collection:
                raise ValueError("Database not initialized. Call setup_database() first.")
                
            # Build where clause for filtering
            where_clause = {}
            if category:
                where_clause["category"] = category
                
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            if results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)
                    
            logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching code examples: {e}")
            raise
            
    def get_all_examples(self) -> List[Dict[str, Any]]:
        """Get all code examples from the database"""
        try:
            if not self.collection:
                raise ValueError("Database not initialized. Call setup_database() first.")
                
            results = self.collection.get()
            
            formatted_results = []
            if results['documents']:
                for i in range(len(results['documents'])):
                    result = {
                        'id': results['ids'][i],
                        'document': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    }
                    formatted_results.append(result)
                    
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting all examples: {e}")
            raise
            
    def delete_example(self, example_id: str):
        """Delete a code example by ID"""
        try:
            if not self.collection:
                raise ValueError("Database not initialized. Call setup_database() first.")
                
            self.collection.delete(ids=[example_id])
            logger.info(f"Deleted example with ID: {example_id}")
            
        except Exception as e:
            logger.error(f"Error deleting example: {e}")
            raise
            
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            if not self.collection:
                return {"total_examples": 0, "collection_exists": False}
                
            count = self.collection.count()
            
            # Get category distribution
            all_examples = self.get_all_examples()
            categories = {}
            for example in all_examples:
                category = example['metadata'].get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
            return {
                "total_examples": count,
                "collection_exists": True,
                "collection_name": self.collection_name,
                "categories": categories
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

# Initialize the database
def initialize_fusion_vector_db(reset: bool = False):
    """Initialize and setup the Fusion 360 Vector Database"""
    db = FusionVectorDB()
    db.setup_database(reset=reset)
    return db

# Add the initial skeletal code example
def add_initial_examples(db: FusionVectorDB):
    """Add the initial skeletal Fusion 360 code example"""
    
    skeletal_code = """import adsk.core, adsk.fusion, adsk.cam, traceback
# These will be populated by Fusion on load:
handlers = []
def run(context):
    ui = None
    try:
        app  = adsk.core.Application.get()
        ui   = app.userInterface
        ui.messageBox('Hello from Fusion 360 Master!')
        # → Your commands or automation go here.
    except:
        if ui:
            ui.messageBox('Failed:\\n{}'.format(traceback.format_exc()))
def stop(context):
    ui = adsk.core.Application.get().userInterface
    # → Clean up: remove UI elements, event handlers, etc.
    ui.messageBox('Goodbye from Fusion 360 Master!')"""
    
    db.add_code_example(
        code=skeletal_code,
        title="Fusion 360 Add-in Skeletal Template",
        description="Complete skeletal template for Fusion 360 add-ins with proper error handling, run and stop functions, and UI messaging",
        tags=["template", "skeleton", "addon", "basic", "error-handling", "ui", "messagebox"],
        category="template",
        parameters={
            "functions": ["run", "stop"],
            "imports": ["adsk.core", "adsk.fusion", "adsk.cam", "traceback"],
            "ui_elements": ["messageBox"],
            "error_handling": True,
            "global_variables": ["handlers"],
            "structure": "add-in-template"
        }
    )
    
    logger.info("Added Fusion 360 skeletal template code example")

if __name__ == "__main__":
    # Example usage - Building fresh database
    print("Building fresh Fusion 360 Vector Database...")
    
    db_path = "./chroma_cad_db"
    
    # Remove old database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database at {db_path}")
        import shutil
        shutil.rmtree(db_path)
        print("✓ Old database removed")
    
    # Initialize fresh database
    print("Creating new database...")
    db = FusionVectorDB(db_path=db_path)
    db.setup_database(reset=True)
    print("✓ Fresh database created")
    
    # Add skeletal template
    print("Adding skeletal template...")
    add_initial_examples(db)
    print("✓ Skeletal template added")
    
    # Show stats
    stats = db.get_stats()
    print(f"\n📊 Database Summary:")
    print(f"   Total examples: {stats['total_examples']}")
    print(f"   Categories: {stats['categories']}")
    print(f"   Collection: {stats['collection_name']}")
    
    print("\n🎉 Fresh database setup complete!")
    print(f"   Database location: {db_path}")
    print("   Ready to add more Fusion 360 code examples!")