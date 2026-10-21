"""Read-only assertion of the frozen Generic-SOFA scene parameters."""


def assert_generic_scene(env) -> None:
    sim = env._simulation
    solver = sim.root.getObject("Generic")
    contact = sim.root.getObject("DefaultContactManager")
    if solver is None or contact is None:
        raise RuntimeError("Frozen Generic scene missing")
    actual = (
        solver.getClassName(), str(solver.findData("resolutionMethod").value),
        float(solver.findData("tolerance").value),
        int(solver.findData("maxIterations").value),
        bool(solver.findData("computeConstraintForces").value),
        str(contact.findData("response").value),
        str(contact.findData("responseParams").value), float(sim.root.dt.value),
    )
    expected = ("GenericConstraintSolver", "ProjectedGaussSeidel", 1e-4,
                2000, True, "FrictionContactConstraint", "mu=0.001", 0.006)
    if actual != expected:
        raise RuntimeError(f"Frozen Generic scene changed: {actual!r}")
