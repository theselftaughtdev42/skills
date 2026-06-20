from mysk.domain import LifecycleState


def test_all_lifecycle_states_exist():
    assert {s.value for s in LifecycleState} == {
        "init",
        "active",
        "experimental",
        "deprecated",
    }
