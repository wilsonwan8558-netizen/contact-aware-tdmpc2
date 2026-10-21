# Repository file tree

Tracked release files (generated before the initial local commit; `.git/` and ignored caches are omitted):

```text
contact-aware-tdmpc2/
├── .gitattributes
├── .gitignore
├── checkpoints/
│   ├── .gitkeep
│   └── README.md
├── COLLABORATOR_HANDOFF.md
├── configs/
│   ├── fuzzy_safety.yaml
│   ├── simulation.yaml
│   └── tdmpc2.yaml
├── contact_aware_tdmpc2/
│   ├── __init__.py
│   ├── configs/
│   │   ├── __init__.py
│   │   ├── fuzzy_safety.yaml
│   │   ├── simulation.yaml
│   │   └── tdmpc2.yaml
│   ├── controller.py
│   ├── demo.py
│   ├── env/
│   │   ├── __init__.py
│   │   ├── action_adapter.py
│   │   ├── force_extraction.py
│   │   ├── force_reconstruction.py
│   │   ├── g13_env.py
│   │   ├── observation.py
│   │   ├── scene_check.py
│   │   └── steve_env.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── force_interface.py
│   │   ├── observation_adapter.py
│   │   ├── robot_interface.py
│   │   └── simulator_interface.py
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── fuzzy_inference.py
│   │   └── safety_filter.py
│   └── tdmpc2/
│       ├── __init__.py
│       ├── agent.py
│       ├── checkpoint.py
│       ├── geometry_force.py
│       └── world_model.py
├── docs/
│   ├── DESIGN_RATIONALE.md
│   ├── FORCE_EXTRACTION.md
│   ├── FUZZY_SAFETY_FILTER.md
│   ├── METHOD.md
│   ├── OBSERVATION_ACTION.md
│   ├── PHYSICAL_DEPLOYMENT.md
│   ├── REPOSITORY_TREE.md
│   ├── SHARING_AUDIT.md
│   └── SOURCE_CODE_AUDIT.md
├── environment.yml
├── eve/
│   ├── __init__.py
│   ├── env.py
│   ├── info/
│   │   ├── __init__.py
│   │   ├── avgtranslationspeed.py
│   │   ├── combination.py
│   │   ├── dummy.py
│   │   ├── info.py
│   │   ├── pathratio.py
│   │   ├── reward.py
│   │   ├── steps.py
│   │   ├── targetreached.py
│   │   ├── terminal.py
│   │   ├── trajectorylength.py
│   │   └── wrapper/
│   │       ├── __init__.py
│   │       ├── averageepisodeslaststep.py
│   │       └── averagesteps.py
│   ├── interimtarget/
│   │   ├── __init__.py
│   │   ├── branching.py
│   │   ├── dummy.py
│   │   ├── even.py
│   │   └── interimtarget.py
│   ├── intervention/
│   │   ├── __init__.py
│   │   ├── device/
│   │   │   ├── __init__.py
│   │   │   ├── device.py
│   │   │   ├── jshaped.py
│   │   │   ├── simmons.py
│   │   │   ├── sofadevice.py
│   │   │   └── straight.py
│   │   ├── dummy.py
│   │   ├── fluoroscopy/
│   │   │   ├── __init__.py
│   │   │   ├── dummy.py
│   │   │   ├── fluoroscopy.py
│   │   │   ├── pillow.py
│   │   │   └── trackingonly.py
│   │   ├── intervention.py
│   │   ├── monoplanestatic.py
│   │   ├── simulation/
│   │   │   ├── __init__.py
│   │   │   ├── simulation.py
│   │   │   ├── simulationmp.py
│   │   │   ├── sofabeamadapter.py
│   │   │   └── util/
│   │   │       └── unit_sphere.stl
│   │   ├── target/
│   │   │   ├── __init__.py
│   │   │   ├── branchend.py
│   │   │   ├── branchindex.py
│   │   │   ├── centerlinerandom.py
│   │   │   ├── dummy.py
│   │   │   ├── manual.py
│   │   │   └── target.py
│   │   └── vesseltree/
│   │       ├── __init__.py
│   │       ├── aorticarch.py
│   │       ├── aorticarcharteries/
│   │       │   ├── __init__.py
│   │       │   ├── aorta.py
│   │       │   ├── brachiocephalictrunk.py
│   │       │   ├── commonorigin.py
│   │       │   ├── leftcommoncarotid.py
│   │       │   ├── leftsubclavian.py
│   │       │   ├── rightcommoncarotid.py
│   │       │   └── rightsubclavian.py
│   │       ├── aorticarchrandom.py
│   │       ├── dummy.py
│   │       ├── frommesh.py
│   │       ├── util/
│   │       │   ├── __init__.py
│   │       │   ├── branch.py
│   │       │   ├── cubichermitesplines.py
│   │       │   ├── insertionfromcenterline.py
│   │       │   ├── meshing.py
│   │       │   ├── vmrdownload.py
│   │       │   └── voxelcube.py
│   │       ├── vesseltree.py
│   │       └── vmr.py
│   ├── observation/
│   │   ├── __init__.py
│   │   ├── image.py
│   │   ├── imagewrapper/
│   │   │   ├── __init__.py
│   │   │   └── showvessels.py
│   │   ├── insertionlengthrelative.py
│   │   ├── insertionlengths.py
│   │   ├── lastaction.py
│   │   ├── obsdict.py
│   │   ├── observation.py
│   │   ├── obstuple.py
│   │   ├── rotation.py
│   │   ├── target2d.py
│   │   ├── target3d.py
│   │   ├── tracking2d.py
│   │   ├── tracking3d.py
│   │   ├── trackingdevice2d.py
│   │   └── wrapper/
│   │       ├── __init__.py
│   │       ├── memory.py
│   │       ├── normalize.py
│   │       ├── normalizecustom.py
│   │       ├── normalizetracking2depisode.py
│   │       ├── relativetofirstrow.py
│   │       ├── relativetolaststate.py
│   │       └── selectivememory.py
│   ├── pathfinder/
│   │   ├── __init__.py
│   │   ├── bruteforcebfs.py
│   │   ├── dummy.py
│   │   └── pathfinder.py
│   ├── reward/
│   │   ├── __init__.py
│   │   ├── combination.py
│   │   ├── insertionlengthrelative.py
│   │   ├── insertionlengthrelativedelta.py
│   │   ├── lastaction.py
│   │   ├── pathlength.py
│   │   ├── pathlengthdelta.py
│   │   ├── reward.py
│   │   ├── step.py
│   │   ├── targetreached.py
│   │   └── tiptotargetdistdelta.py
│   ├── start/
│   │   ├── __init__.py
│   │   ├── dummy.py
│   │   ├── insertionpoint.py
│   │   ├── maxdevicelength.py
│   │   ├── randomadvance.py
│   │   ├── start.py
│   │   └── vesselend.py
│   ├── terminal/
│   │   ├── __init__.py
│   │   ├── combination.py
│   │   ├── targetreached.py
│   │   └── terminal.py
│   ├── truncation/
│   │   ├── __init__.py
│   │   ├── combination.py
│   │   ├── dummy.py
│   │   ├── maxsteps.py
│   │   ├── simerror.py
│   │   ├── truncation.py
│   │   └── vesselend.py
│   ├── util/
│   │   ├── __init__.py
│   │   ├── confighandler.py
│   │   ├── coordtransform.py
│   │   ├── eveobject.py
│   │   ├── interventionstatestorage.py
│   │   └── userinput/
│   │       ├── __init__.py
│   │       ├── instrumentaction.py
│   │       └── visumanipulator.py
│   └── visualisation/
│       ├── __init__.py
│       ├── dummy.py
│       ├── fromimaging.py
│       ├── fromstate.py
│       ├── meshes/
│       │   └── unit_sphere.stl
│       ├── plt3d.py
│       ├── sofapygame.py
│       └── visualisation.py
├── examples/
│   ├── minimal_inference.py
│   └── phantom_integration_skeleton.py
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── scripts/
│   ├── compare_nominal_vs_safety.py
│   ├── inspect_force_signal.py
│   ├── run_fuzzy_safety_demo.py
│   └── run_nominal_demo.py
├── tests/
│   ├── test_action_adapter.py
│   ├── test_checkpoint_loading.py
│   ├── test_fuzzy_membership.py
│   ├── test_observation.py
│   └── test_safety_filter.py
├── third_party/
│   ├── stEVE_LICENSE
│   └── TD-MPC2_LICENSE
└── THIRD_PARTY_NOTICES.md
```
