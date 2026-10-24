# Weibo Phantom Vessel STL Inspection

## Asset

- Source: `VasselTree/Neurovascular model.stl`
- File size: 64,273,784 bytes
- Encoding: valid binary STL from Geomagic Studio
- Declared triangle count: 1,285,474; byte count matches the binary STL record layout
- Loaded mesh: 642,654 vertices and 1,285,474 triangular faces

## Native Geometry

The mesh native-coordinate bounds are:

| Axis | Minimum | Maximum | Extent |
| --- | ---: | ---: | ---: |
| x | -227.883 | 75.725 | 303.608 |
| y | -67.985 | 232.090 | 300.075 |
| z | -562.586 | -20.889 | 541.697 |

It is one connected surface component. It is not watertight (`is_manifold=false`,
six open edges). Open boundaries can be expected at vessel ends, but this does
not establish which opening is the procedural insertion inlet.

The dominant principal axis is oblique and has a substantial negative-z
component. Mesh orientation alone does not identify the intended guidewire
insertion direction or clinical coordinate frame.

## Comparison with the Packaged Original Vessel

The original training vessel coordinate extent is approximately
122.10 x 84.73 x 239.11 mm. The phantom native extent is approximately
303.61 x 300.08 x 541.70 native units, giving extent ratios of about 2.49,
3.54, and 2.27 respectively. This is compatible with several possibilities
(for example, a larger anatomy, a different physical unit, or a different
registration), so the STL alone does **not** establish millimetre scale.

## Required G13 Inputs

`kind: from_mesh` scenes require a radiused centerline YAML containing named
branches, each with `coordinates_mm` of shape N x 3 and positive `radii_mm`
of shape N. The same source frame must also supply:

- the insertion position and unit insertion direction;
- branch connectivity/name semantics for `centerline_random` targets, or a
  manually verified target inside the represented radiused lumen;
- an explicit scale, rotation, and translation registration;
- fluoroscopy/image-frame settings consistent with that registration.

The 22-D G13 geometry features query these radiused centerline branches for
signed clearance, local radius, distal curvature, and direction validity.

## Extraction Assessment and Stop Decision

The repository contains no supported STL-to-centerline/radius extraction tool.
Available local libraries include PyVista/VTK, SciPy, scikit-image, and
NetworkX; VMTK is not installed. A generic surface-mesh skeletonization would
not reliably establish the required branch topology, lumen centerline, local
radius, inlet, or scale without validated phantom metadata.

Therefore no `phantom_centerline` asset, scene config, validation target, or
training run was created. Required collaborator input before proceeding is:

1. measured/exported centerline branches with local radii in a declared mm
   frame;
2. declared insertion/inlet position and direction;
3. mesh-to-centerline registration and unit scale;
4. intended target branch or validated target coordinates.

This is a deliberate safety and reproducibility stop: a straight-line
centerline, constant radius, arbitrary target, or inferred scale would change
the meaning of the frozen 22-D observation and is not acceptable for G13
training.
