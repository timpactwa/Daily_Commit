from pipeline import build


def test_crlf_corpus_file_is_normalized(tmp_path, monkeypatch):
    """Windows checkouts can turn corpus files into CRLF; load() must still return LF source."""
    src = (build.CORPUS / "factorial.py").read_bytes().replace(b"\r\n", b"\n")
    crlf_dir = tmp_path / "corpus"
    crlf_dir.mkdir()
    (crlf_dir / "factorial.py").write_bytes(src.replace(b"\n", b"\r\n"))
    monkeypatch.setattr(build, "CORPUS", crlf_dir)
    source, cases = build.load("factorial")
    assert "\r" not in source
    assert source == src.decode()
