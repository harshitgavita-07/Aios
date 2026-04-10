import sys
import types

from rag.embedder import LocalEmbedder


def test_embedder_requests_local_files_only(monkeypatch):
    captured = {}

    class FakeSentenceTransformer:
        def __init__(self, model_name, **kwargs):
            captured["model_name"] = model_name
            captured.update(kwargs)

        def encode(self, texts, show_progress_bar=False):
            return [[0.0] * 384 for _ in texts]

    fake_module = types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer)
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    embedder = LocalEmbedder("cached-model")

    assert captured["model_name"] == "cached-model"
    assert captured["local_files_only"] is True
    assert embedder.embed_query("hello") == [0.0] * 384


def test_embedder_falls_back_when_local_model_is_missing(monkeypatch):
    class MissingSentenceTransformer:
        def __init__(self, *args, **kwargs):
            raise OSError("model is not cached")

    fake_module = types.SimpleNamespace(SentenceTransformer=MissingSentenceTransformer)
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    embedder = LocalEmbedder("missing-model")
    embedding = embedder.embed_query("hello")

    assert embedder._model is None
    assert len(embedding) == 384
