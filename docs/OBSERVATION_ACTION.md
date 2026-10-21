# Observation and action contract

The frozen model requires exactly 22 float32 values, in the order below.
The first 12 are normalized with stEVE's **episode-specific 2-D tracking
bounds** as `2(x-low)/(high-low)-1`, then clipped to `[-1,1]`. Physical
deployment must reproduce that reference convention or validate an explicit
replacement before using the frozen model. `p0` is the distal-most sampled
tracking point. The last eight features use current, not future, geometry.

| Index | Name | Units/status | Simulation source | Physical interpretation / reconstruction |
|---:|---|---|---|---|
| 0 | `p0_x` | normalized | Tracking2D point 0 | distal tip projection x |
| 1 | `p0_y` | normalized | Tracking2D point 0 | distal tip projection y |
| 2 | `p1_x` | normalized | Tracking2D point 1 | next tracked point x |
| 3 | `p1_y` | normalized | Tracking2D point 1 | next tracked point y |
| 4 | `p2_x` | normalized | Tracking2D point 2 | tracked point x |
| 5 | `p2_y` | normalized | Tracking2D point 2 | tracked point y |
| 6 | `p3_x` | normalized | Tracking2D point 3 | tracked point x |
| 7 | `p3_y` | normalized | Tracking2D point 3 | tracked point y |
| 8 | `p4_x` | normalized | Tracking2D point 4 | proximal tracked point x |
| 9 | `p4_y` | normalized | Tracking2D point 4 | proximal tracked point y |
| 10 | `target_x` | normalized | Target2D | target projection x |
| 11 | `target_y` | normalized | Target2D | target projection y |
| 12 | `sin_device_rotation` | unitless | Rotations | sine of device angle |
| 13 | `cos_device_rotation` | unitless | Rotations | cosine of device angle |
| 14 | `d0_normalized` | tanh(mm/20) | 3-D tracking/lumen model | distal point signed centerline-radius clearance proxy |
| 15 | `d1_normalized` | tanh(mm/20) | 3-D tracking/lumen model | second point signed clearance proxy |
| 16 | `d2_normalized` | tanh(mm/20) | 3-D tracking/lumen model | third point signed clearance proxy |
| 17 | `sin_delta_theta` | unitless | projected wire/lumen tangent | signed heading difference sine |
| 18 | `cos_delta_theta` | unitless | projected wire/lumen tangent | heading difference cosine |
| 19 | `kappa_distal_normalized` | angle/pi | first 3 2-D points | distal bend-angle proxy |
| 20 | `r_local_normalized` | tanh(mm/20) | nearest lumen radius | local radius proxy |
| 21 | `direction_valid` | 0 or 1 | tangent validity | whether heading is measurable |

All fields must be reconstructed from the physical platform. In particular,
the simulator's `d0/d1/d2` are signed centerline-radius *lumen-clearance
proxies*, **not** exact collision-mesh distances. They require tracked 3-D
wire points registered to a vessel centerline and local radius model. The
simulation extractor samples the first three points about 1 mm apart along
the tracked wire, pairs 2-D and 3-D samples, and checks projection alignment.
If those signals cannot be reproduced and validated, the frozen model is not
ready for physical use.

Action is normalized float32 `[a_v, a_omega]` in `[-1,1]^2`. The frozen
JShaped simulation maps it linearly to insertion velocity in `[-50,50]` mm/s
and rotation velocity in `[-3.14,3.14]` rad/s. The physical robot adapter
must implement its own calibrated, bounded mapping, watchdog, and interlocks;
do not assume these simulator limits are safe hardware limits.
