# tests/test_llm_param_shapes.py
import os
import types

def test_gpt5_responses_shapes(monkeypatch):
    os.environ["NOVA_FORCE_OPENAI_CHAT"] = "0"
    from src.nova.agent.llm_client import LLMClient
    client = LLMClient()
    client.model = "gpt-5"
    # Fake OpenAI client
    class FakeResp: output_text = "ok"
    class FakeOpenAI:
        class responses:
            @staticmethod
            def create(**kw):
                assert "input" in kw and isinstance(kw["input"], list)
                assert "max_output_tokens" in kw
                assert kw.get("temperature") == 1.0
                return FakeResp()
    client.client = types.SimpleNamespace(responses=FakeOpenAI.responses, chat=None)
    out = client.complete("sys", "user", temperature=0.3, max_tokens=123, reasoning_effort="medium")
    assert out == "ok"

def test_gpt5_chat_shapes(monkeypatch):
    os.environ["NOVA_FORCE_OPENAI_CHAT"] = "1"
    from src.nova.agent.llm_client import LLMClient
    client = LLMClient()
    client.model = "gpt-5"
    class FakeChoice: 
        def __init__(self): self.message = types.SimpleNamespace(content="ok")
    class FakeChat:
        @staticmethod
        def completions(): pass
        class completions:
            @staticmethod
            def create(**kw):
                assert "max_completion_tokens" in kw
                assert kw.get("temperature") == 1.0
                return types.SimpleNamespace(choices=[FakeChoice()])
    client.client = types.SimpleNamespace(chat=FakeChat)
    out = client.complete("sys", "user", temperature=0.2, max_tokens=77)
    assert out == "ok"
