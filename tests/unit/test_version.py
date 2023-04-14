def test_version() -> None:
    """Test that version string can be imported successfully"""
    from aiomanager import __version__
    from aiomanager.__about__ import __version__ as __about_version__

    assert isinstance(__version__, str)
    assert __version__ == __about_version__
