import json
import sys
import types
from pathlib import Path
import shutil


def test_analyze_text_parses_json_and_caches(monkeypatch, tmp_path):
    # Prepare required module and directories
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    import services.ai as ai
    try:
        # Redirect cache and logs to temporary directory
        monkeypatch.setattr(ai, "CACHE_DIR", tmp_path)
        log_file = tmp_path / "ai.log"
        log_file.touch()
        monkeypatch.setattr(ai, "LOG_FILE", log_file)

        # Stub OpenAI client
        class DummyResponse:
            choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=json.dumps({
                "flashcards": [{"front": "F", "back": "B"}],
                "exercices": [{"question": "Q"}]
            })))]

        class DummyClient:
            calls = 0

            def __init__(self, api_key=None):
                self.chat = types.SimpleNamespace(
                    completions=types.SimpleNamespace(create=self._create)
                )

            def _create(self, **kwargs):
                DummyClient.calls += 1
                return DummyResponse()

        monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyClient))
        monkeypatch.setenv("OPENAI_API_KEY", "test")

        items1 = ai.analyze_text("hello")
        assert items1 == [
            {"id": "ai0", "kind": "card", "payload": {"front": "F", "back": "B"}},
            {"id": "ai1", "kind": "exercise", "payload": {"question": "Q"}},
        ]

        items2 = ai.analyze_text("hello")
        assert items2 == items1
        assert DummyClient.calls == 1
        # cache file created
        assert len(list(tmp_path.glob("*.json"))) == 1
    finally:
        shutil.rmtree(logs_dir)
