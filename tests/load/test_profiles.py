from load.profiles import PROFILES, profile


def test_smoke_profile_is_ci_safe() -> None:
    smoke = profile("smoke")

    assert smoke.users == 1
    assert smoke.max_requests == 5
    assert smoke.provider_mode == "fake"
    assert not smoke.requires_confirmation


def test_aggressive_profiles_require_confirmation() -> None:
    for name in ["volume-300", "burst", "soak-short", "soak-long", "spike-recovery"]:
        assert PROFILES[name].requires_confirmation


def test_real_provider_has_small_ceiling() -> None:
    real = profile("real-provider")

    assert real.requires_confirmation
    assert real.max_requests <= 10
