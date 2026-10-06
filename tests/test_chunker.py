"""Tests unitaires du chunker."""

from copilot_rag.chunker import chunk_text, is_binary


def test_small_text_single_chunk():
    chunks = chunk_text("a = 1\nb = 2", "p", "f.py", "python", "h")
    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 2
    assert chunks[0].text == "a = 1\nb = 2"


def test_large_text_splits_with_overlap():
    lines = [f"ligne {i} " + "x" * 90 for i in range(1, 41)]  # ~100 chars/ligne
    text = "\n".join(lines)
    chunks = chunk_text(text, "p", "f.py", "python", "h", max_chars=1000, overlap_chars=200)
    assert len(chunks) > 1
    # Les chunks sont ordonnés et se recouvrent
    for prev, nxt in zip(chunks, chunks[1:]):
        assert nxt.start_line <= prev.end_line
        assert nxt.end_line > prev.end_line
    assert chunks[0].start_line == 1
    assert chunks[-1].end_line == 40


def test_empty_and_blank_text_produce_no_chunk():
    assert chunk_text("", "p", "f.py", "python", "h") == []
    assert chunk_text("   \n\n  ", "p", "f.py", "python", "h") == []


def test_metadata_and_id_are_stable():
    (c1,) = chunk_text("x = 1", "proj", "src/f.py", "python", "abc")
    (c2,) = chunk_text("x = 1", "proj", "src/f.py", "python", "abc")
    assert c1.chunk_id == c2.chunk_id
    md = c1.metadata
    assert md["project"] == "proj"
    assert md["path"] == "src/f.py"
    assert md["language"] == "python"
    assert md["file_hash"] == "abc"


def test_binary_detection():
    assert is_binary(b"\x89PNG\x00\x00")
    assert not is_binary("du texte".encode("utf-8"))
