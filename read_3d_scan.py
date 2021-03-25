from pathlib import Path
import pywavefront
import pyvista as pv
import numpy as np
import logging

pywavefront.configure_logging(
    logging.DEBUG,
    formatter=logging.Formatter('%(name)s-%(levelname)s: %(message)s')
)



scan_3d_dir=Path(r"3dscan")
# obj_file="Prostaat_2_na_fixatie"
obj_file="Prostaat_2"


scan_3d_obj_file = scan_3d_dir.joinpath(obj_file+".obj")
if not  scan_3d_obj_file.is_file():
    raise FileNotFoundError("Where is my file?")

scene = pywavefront.Wavefront(scan_3d_obj_file, create_materials=True)


len(scene.vertices)
# print(scene.__dict__)
print(scene.parser.__dict__.keys())
# print(scene.parser.__dict__['file_name'])

# scene.parser.__dict__['mesh'].__dict__
# print(len(scene.vertices))
# print(len(scene.parser.__dict__['tex_coords']))
faces = np.array(scene.mesh_list[0].faces)
vertices = np.array(scene.vertices)

print(scene.mesh_list)

faces_triangle = np.hstack((3 * np.ones((faces.shape[0], 1)), faces)).astype(np.int32)

mesh_pv=pv.PolyData(vertices, faces_triangle)

print(f"len vt {len(scene.parser.__dict__['tex_coords'])}")
print(f"len vertices {len(vertices)}")
print(f"len faces {len(faces)}")





material=scene.parser.__dict__['material']

print(type(material.vertices))
print(len(material.vertices)/3)


# plotter = pv.Plotter()
# plotter.add_mesh(mesh_pv)
# plotter.show()