from aidoo_mcp.cli import build_parser, main


def test_parser_exposes_the_documented_flags():
    parser = build_parser()
    args = parser.parse_args(
        ["--api-key", "aid_live_x", "--url", "https://self.hosted/sse", "--transport", "sse"]
    )
    assert args.api_key == "aid_live_x"
    assert args.endpoint == "https://self.hosted/sse"
    assert args.transport == "sse"
    assert args.check is False


def test_a_missing_key_exits_with_a_configuration_code(monkeypatch, capsys):
    monkeypatch.delenv("AIDOO_API_KEY", raising=False)
    assert main([]) == 2
    assert "No API key found" in capsys.readouterr().err


def test_an_invalid_timeout_exits_with_a_configuration_code(monkeypatch, capsys):
    monkeypatch.setenv("AIDOO_API_KEY", "aid_live_key")
    assert main(["--timeout", "nope"]) == 2
    assert "Invalid timeout" in capsys.readouterr().err
