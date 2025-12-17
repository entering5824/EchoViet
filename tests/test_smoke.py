def test_smoke():
    """Lightweight smoke test that does not import heavy modules.

    This ensures pytest always collects at least one test even if other
    test modules fail to import due to heavy dependencies (Whisper/Torch).
    """
    assert True
