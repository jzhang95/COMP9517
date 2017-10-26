import os
import sys
import subprocess
from bell2014.input import IntrinsicInput
from bell2014.params import IntrinsicParameters
from bell2014.solver import IntrinsicSolver
from bell2014 import image_util

OMVG_BIN = ""
OMVS_BIN = ""
INPUT_DIR = ""
OUTPUT_DIR = ""
MATCHES_DIR = ""
RECONSTRUCT_DIR = ""
MVS_DIR = ""
CAMERA_PARAMS = ""

if not os.path.exists(matches_dir):
  os.mkdir(matches_dir)

print("----------/nINTRINSIC DECOMPOSITION")
in_name = raw_input("Image filename: ")
base, _ = os.path.splitext(in_name)
r_name = base + "-R.png"
s_name = base + "-S.png"

in_img = IntrinsicInput.from_file(os.path.join(INPUT_DIR, in_name))
params = IntrinsicParameters()
solver = IntrinsicSolver(in_img, params)
reflect, shading, decomp = solver.solve()

image_util.save(r_name, reflect, mask_nz=in_img.mask_nz, rescale=True, srgb=True)
image_util.save(s_name, shading, mask_nz=in_img.mask_nz, rescale=True, srgb=True)

print("----------/n3D RECONSTRUCTION")
print("Getting Intrinsics")
proc_intrinsics = subprocess.Popen( [os.path.join(OMVG_BIN, "openMVG_main_SfMInit_ImageListing"),
                                     "-i", INPUT_DIR,
                                     "-o", MATCHES_DIR,
                                     "-d", CAMERA_PARAMS] )
proc_intrisics.wait()

print("Computing features")
proc_features = subprocess.Popen( [os.path.join(OMVG_BIN, "openMVG_main_ComputeFeatures"),
                                   "-i", MATCHES_DIR + "/sfm_data.json",
                                   "-o", MATCHES_DIR,
                                   "-m", "SIFT",
                                   "-n", "4"] )
proc_features.wait()

print("Computing matches")
proc_matches = subprocess.Popen( [os.path.join(OMVG_BIN, "openMVG_main_ComputeMatches"),
                                  "-i", MATCHES_DIR + "/sfm_data.json",
                                  "-o", MATCHES_DIR] )
proc_matches.wait()

print("Generating sparse point cloud")
proc_reconstruct = subprocess.Popen( [os.path.join(OMVG_BIN, "openMVG_main_IncrementalSfM"),
                                      "-i", MATCHES_DIR + "/sfm_data.json",
                                      "-m", MATCHES_DIR,
                                      "-o", RECONSTRUCT_DIR] )
proc_reconstruct.wait()

print("Switching to OpenMVS")
proc_convert = subprocess.Popen( [os.path.join(OMVG_BIN, "openMVG_main_openMVG2openMVS"),
                                  "-i", RECONSTRUCT_DIR + "/sfm_data.bin",
                                  "-o", MVS_DIR + "/scene.mvs",
                                  "-d", MVS_DIR] )
proc_convert.wait()

print("Generating dense point cloud")
proc_densify = subprocess.Popen( [os.path.join(OMVS_BIN, "DensifyPointCloud"),
                                  "scene.mvs",
                                  "-w", MVS_DIR] )
proc_densify.wait()

print("Constructing coarse mesh")
proc_mesh = subprocess.Popen( [os.path.join(OMVS_BIN, "ReconstructMesh"),
                               "scene_dense.mvs",
                               "-w", MVS_DIR] )
proc_mesh.wait()

print("Refining mesh")
proc_refine = subprocess.Popen( [os.path.join(OMVS_BIN, "RefineMesh"),
                                 "scene_dense_mesh.mvs",
                                 "-w", MVS_DIR] )
proc_refine.wait()

print("Applying texture to model")
proc_texture = subprocess.Popen( [os.path.join(OMVS_BIN, "TextureMesh"),
                                  "scene_dense_mesh_refine.mvs",
                                  "-w", MVS_DIR] )
proc_texture.wait()
