import numpy as np  # type: ignore
import trimesh  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from scipy.spatial import Delaunay  # type: ignore
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def load_mesh(filepath):
    valid_extensions = {'.stl', '.obj'}
    ext = os.path.splitext(filepath)[-1].lower()
    if ext not in valid_extensions:
        raise ValueError(f"Unsupported file type: '{ext}'. Supported formats: .stl, .obj")

    mesh = trimesh.load_mesh(filepath, force='mesh')
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Loaded file is not a valid 3D mesh.")
    return mesh

def generate_mesh(mesh):
    points = mesh.vertices
    delaunay = Delaunay(points[:, :2])  # 2D triangulation (XY plane)
    return points, delaunay.simplices

def simulate_stress(points, elements):
    stress = np.abs(points[:, 1]) * 10  # Simulated stress based on Y-coordinate
    return stress

def plot_results(points, stress):
    plt.scatter(points[:, 1], points[:, 2], c=stress, cmap='jet')
    plt.colorbar(label='Simulated Stress')
    plt.title('Stress Distribution (XY Plane)')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.axis('equal')
    plt.show()

def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide root window

    file_path = filedialog.askopenfilename(
        title="Select a 3D Model File",
        filetypes=[("3D Model Files", "*.stl *.obj")]
    )

    if not file_path:
        messagebox.showinfo("No File", "No file was selected.")
        return

    try:
        mesh = load_mesh(file_path)
        points, elements = generate_mesh(mesh)
        stress = simulate_stress(points, elements)
        plot_results(points, stress)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")

def main():
    select_file()

if __name__ == "__main__":
    main()


