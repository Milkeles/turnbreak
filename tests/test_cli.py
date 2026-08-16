from turnbreak.cli import main


def test_main_with_no_args_returns_nonzero() -> None:
    assert main([]) == 1
