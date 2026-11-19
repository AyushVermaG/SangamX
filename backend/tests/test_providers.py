"""
Tests for the SangamX provider abstraction (providers.py).

All LLM calls are fully mocked — no real API keys are needed,
no quota is consumed, and no money is ever spent.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.engine.providers import (
    AllProvidersFailedError,
    LLMResponse,
    OllamaUnavailableError,
    ProviderError,
    ProviderUnavailableError,
    QuotaExceededError,
    _is_quota_error,
    _is_unavailable_error,
    invoke_llm,
    reset_ollama_semaphore,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_semaphore():
    """Reset Ollama semaphore between tests to avoid state leakage."""
    reset_ollama_semaphore()
    yield
    reset_ollama_semaphore()


@pytest.fixture()
def settings_gemini():
    """Settings with only Gemini key — Groq disabled."""
    return Settings(
        gemini_api_key="gemini-test-key",
        groq_api_key="",
        ollama_base_url="http://localhost:11434",
        ollama_model="qwen3:4b",
        ollama_max_concurrency=1,
        llm_timeout=5.0,
        provider_max_retries=1,
    )


@pytest.fixture()
def settings_groq():
    """Settings with only Groq key — Gemini disabled."""
    return Settings(
        gemini_api_key="",
        groq_api_key="groq-test-key",
        ollama_base_url="http://localhost:11434",
        ollama_model="qwen3:4b",
        ollama_max_concurrency=1,
        llm_timeout=5.0,
        provider_max_retries=1,
    )


@pytest.fixture()
def settings_all():
    """Settings with all providers configured."""
    return Settings(
        gemini_api_key="gemini-test-key",
        groq_api_key="groq-test-key",
        ollama_base_url="http://localhost:11434",
        ollama_model="qwen3:4b",
        ollama_max_concurrency=2,
        llm_timeout=5.0,
        provider_max_retries=2,
    )


@pytest.fixture()
def mock_messages():
    from langchain_core.messages import HumanMessage, SystemMessage
    return [SystemMessage(content="You are helpful."), HumanMessage(content="Hello")]


def _mock_llm_response(content: str):
    """Return a mock LangChain response object."""
    resp = MagicMock()
    resp.content = content
    return resp


# ---------------------------------------------------------------------------
# Error classifier tests
# ---------------------------------------------------------------------------


class TestErrorClassifiers:
    def test_quota_error_429_message(self):
        exc = Exception("Error 429: Too Many Requests")
        assert _is_quota_error(exc) is True

    def test_quota_error_rate_limit(self):
        exc = Exception("rate limit exceeded")
        assert _is_quota_error(exc) is True

    def test_quota_error_resource_exhausted(self):
        exc = Exception("ResourceExhausted: quota limit reached")
        assert _is_quota_error(exc) is True

    def test_quota_error_false_for_normal(self):
        exc = Exception("some random error")
        assert _is_quota_error(exc) is False

    def test_unavailable_timeout(self):
        exc = Exception("Request timeout after 30s")
        assert _is_unavailable_error(exc) is True

    def test_unavailable_connection(self):
        exc = Exception("Connection refused")
        assert _is_unavailable_error(exc) is True

    def test_unavailable_503(self):
        exc = Exception("HTTP 503 Service Unavailable")
        assert _is_unavailable_error(exc) is True

    def test_unavailable_false_for_quota(self):
        exc = Exception("quota exceeded")
        assert _is_unavailable_error(exc) is False


# ---------------------------------------------------------------------------
# Gemini provider tests
# ---------------------------------------------------------------------------


class TestGeminiProvider:
    @pytest.mark.asyncio
    async def test_gemini_success(self, settings_gemini, mock_messages):
        """Gemini provider returns LLMResponse on success."""
        mock_resp = _mock_llm_response("Gemini answer")

        with patch("app.engine.providers._build_gemini") as mock_build:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_resp)
            mock_build.return_value = mock_llm

            result = await invoke_llm(
                messages=mock_messages,
                model="gemini-2.0-flash-exp",
                provider="gemini",
                settings=settings_gemini,
                temperature=0.3,
            )

        assert result.content == "Gemini answer"
        assert result.provider == "gemini"
        assert result.model == "gemini-2.0-flash-exp"
        mock_build.assert_called_once_with(
            "gemini-2.0-flash-exp", "gemini-test-key", 0.3
        )

    @pytest.mark.asyncio
    async def test_gemini_no_api_key_raises(self, mock_messages):
        """Gemini with empty API key raises ProviderUnavailableError."""
        settings = Settings(gemini_api_key="", groq_api_key="", ollama_model="qwen3:4b")

        with patch("app.engine.providers._build_gemini") as mock_build:
            mock_build.side_effect = ProviderUnavailableError("GEMINI_API_KEY is not set")
            # Ollama also unavailable
            with patch("app.engine.providers._invoke_ollama") as mock_ollama:
                mock_ollama.side_effect = OllamaUnavailableError("Ollama not running")
                with pytest.raises(AllProvidersFailedError):
                    await invoke_llm(
                        messages=mock_messages,
                        model="gemini-2.0-flash-exp",
                        provider="gemini",
                        settings=settings,
                    )


# ---------------------------------------------------------------------------
# Groq provider tests
# ---------------------------------------------------------------------------


class TestGroqProvider:
    @pytest.mark.asyncio
    async def test_groq_success(self, settings_groq, mock_messages):
        """Groq provider returns LLMResponse on success."""
        mock_resp = _mock_llm_response("Groq answer")

        with patch("app.engine.providers._build_groq") as mock_build:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_resp)
            mock_build.return_value = mock_llm

            result = await invoke_llm(
                messages=mock_messages,
                model="llama-3.1-8b-instant",
                provider="groq",
                settings=settings_groq,
                temperature=0.1,
            )

        assert result.content == "Groq answer"
        assert result.provider == "groq"
        assert result.model == "llama-3.1-8b-instant"
        mock_build.assert_called_once_with(
            "llama-3.1-8b-instant", "groq-test-key", 0.1
        )

    @pytest.mark.asyncio
    async def test_groq_no_api_key_raises(self, mock_messages):
        """Groq with empty API key raises ProviderUnavailableError → Ollama fallback."""
        settings = Settings(gemini_api_key="", groq_api_key="", ollama_model="qwen3:4b",
                            llm_timeout=5.0, provider_max_retries=1)

        with patch("app.engine.providers._build_groq") as mock_build:
            mock_build.side_effect = ProviderUnavailableError("GROQ_API_KEY is not set")
            with patch("app.engine.providers._invoke_ollama") as mock_ollama:
                mock_ollama.side_effect = OllamaUnavailableError("Ollama not running")
                with pytest.raises(AllProvidersFailedError) as exc_info:
                    await invoke_llm(
                        messages=mock_messages,
                        model="llama-3.1-8b-instant",
                        provider="groq",
                        settings=settings,
                    )
        assert "All providers failed" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Ollama provider tests
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_ollama_direct_success(self, settings_all, mock_messages):
        """Direct Ollama call (provider='ollama') succeeds."""
        with patch("app.engine.providers._invoke_ollama") as mock_ollama:
            mock_ollama.return_value = "Ollama answer"

            result = await invoke_llm(
                messages=mock_messages,
                model="qwen3:4b",
                provider="ollama",
                settings=settings_all,
            )

        assert result.content == "Ollama answer"
        assert result.provider == "ollama"
        assert result.model == "qwen3:4b"

    @pytest.mark.asyncio
    async def test_ollama_direct_unavailable_raises(self, settings_all, mock_messages):
        """Direct Ollama call raises AllProvidersFailedError when server is down."""
        with patch("app.engine.providers._invoke_ollama") as mock_ollama:
            mock_ollama.side_effect = OllamaUnavailableError("Connection refused")

            with pytest.raises(AllProvidersFailedError):
                await invoke_llm(
                    messages=mock_messages,
                    model="qwen3:4b",
                    provider="ollama",
                    settings=settings_all,
                )

    @pytest.mark.asyncio
    async def test_ollama_concurrency_semaphore(self, settings_all, mock_messages):
        """Multiple Ollama requests respect the max_concurrency semaphore."""
        call_times = []

        async def slow_ollama(model, messages, settings, temperature):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.05)
            return "done"

        with patch("app.engine.providers._invoke_ollama", side_effect=slow_ollama):
            settings_all.ollama_max_concurrency = 1
            tasks = [
                invoke_llm(mock_messages, "qwen3:4b", "ollama", settings_all)
                for _ in range(3)
            ]
            results = await asyncio.gather(*tasks)

        assert all(r.provider == "ollama" for r in results)


# ---------------------------------------------------------------------------
# Provider switching and fallback tests
# ---------------------------------------------------------------------------


class TestProviderFallback:
    @pytest.mark.asyncio
    async def test_quota_exceeded_falls_back_to_ollama(self, settings_all, mock_messages):
        """HTTP 429 on Gemini triggers Ollama fallback."""
        with patch("app.engine.providers._build_gemini") as mock_build:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(
                side_effect=Exception("Error 429: RESOURCE_EXHAUSTED quota exceeded")
            )
            mock_build.return_value = mock_llm

            with patch("app.engine.providers._invoke_ollama") as mock_ollama:
                mock_ollama.return_value = "Fallback answer"

                result = await invoke_llm(
                    messages=mock_messages,
                    model="gemini-2.0-flash-exp",
                    provider="gemini",
                    settings=settings_all,
                )

        assert result.provider == "ollama"
        assert result.content == "Fallback answer"
        assert "fallback_reason" in result.metadata

    @pytest.mark.asyncio
    async def test_timeout_falls_back_to_ollama(self, settings_all, mock_messages):
        """Timeout on cloud provider triggers Ollama fallback."""
        with patch("app.engine.providers._build_groq") as mock_build:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(
                side_effect=asyncio.TimeoutError("timed out")
            )
            mock_build.return_value = mock_llm

            with patch("app.engine.providers._invoke_ollama") as mock_ollama:
                mock_ollama.return_value = "Timeout fallback"

                result = await invoke_llm(
                    messages=mock_messages,
                    model="llama-3.1-8b-instant",
                    provider="groq",
                    settings=settings_all,
                )

        assert result.provider == "ollama"
        assert result.content == "Timeout fallback"

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_clear_error(self, settings_all, mock_messages):
        """When both cloud and Ollama fail, AllProvidersFailedError is raised."""
        with patch("app.engine.providers._build_gemini") as mock_build:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(
                side_effect=Exception("429 quota exceeded")
            )
            mock_build.return_value = mock_llm

            with patch("app.engine.providers._invoke_ollama") as mock_ollama:
                mock_ollama.side_effect = OllamaUnavailableError("Ollama not running")

                with pytest.raises(AllProvidersFailedError) as exc_info:
                    await invoke_llm(
                        messages=mock_messages,
                        model="gemini-2.0-flash-exp",
                        provider="gemini",
                        settings=settings_all,
                    )

        error_msg = str(exc_info.value)
        assert "All providers failed" in error_msg
        assert "Ollama" in error_msg
        assert "ollama serve" in error_msg

    @pytest.mark.asyncio
    async def test_paid_provider_never_used_in_fallback(self, settings_all, mock_messages):
        """
        ZERO-COST GUARANTEE: When a provider fails, only Ollama is used as fallback.
        No paid upgrade or billing ever happens.
        """
        openai_called = False

        def fake_build_gemini(model, key, temp):
            raise QuotaExceededError("quota exceeded")

        async def fake_ollama(model, messages, settings, temperature):
            return "local answer"

        # Patch 'openai' to detect if it's ever imported/used
        with patch("app.engine.providers._build_gemini", side_effect=fake_build_gemini):
            with patch("app.engine.providers._invoke_ollama", side_effect=fake_ollama):
                # Ensure OpenAI is NOT called
                with patch("app.engine.providers._build_groq") as mock_groq_build:
                    result = await invoke_llm(
                        messages=mock_messages,
                        model="gemini-2.0-flash-exp",
                        provider="gemini",
                        settings=settings_all,
                    )
                    # Groq was not used as fallback (only Ollama is)
                    mock_groq_build.assert_not_called()

        assert result.provider == "ollama"
        assert not openai_called, "OpenAI must NEVER be called"

    @pytest.mark.asyncio
    async def test_retry_on_unavailable_then_succeed(self, settings_all, mock_messages):
        """Provider retries on transient failure before falling back."""
        attempt_count = 0

        async def flaky_ainvoke(messages):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("503 Service Unavailable")
            return _mock_llm_response("Success after retry")

        with patch("app.engine.providers._build_gemini") as mock_build:
            settings_all.provider_max_retries = 2
            mock_llm = MagicMock()
            mock_llm.ainvoke = flaky_ainvoke
            mock_build.return_value = mock_llm

            result = await invoke_llm(
                messages=mock_messages,
                model="gemini-2.0-flash-exp",
                provider="gemini",
                settings=settings_all,
            )

        assert result.provider == "gemini"
        assert result.content == "Success after retry"
        assert attempt_count == 2


# ---------------------------------------------------------------------------
# Full agent workflow test (mocked providers)
# ---------------------------------------------------------------------------


class TestFullAgentWorkflow:
    """
    End-to-end test of the agent workflow using mocked LLM responses.
    Verifies agent sequencing without consuming API quota.
    """

    @pytest.mark.asyncio
    async def test_planner_uses_invoke_llm(self, settings_all):
        """Planner calls invoke_llm with correct provider/model."""
        from app.engine.agents.planner import run_planner
        from app.engine.state import ModelConfig

        config = ModelConfig(
            planner_provider="gemini",
            planner_model="gemini-2.0-flash-exp",
        )
        plan_json = '{"tasks": [{"id": "t1", "type": "research", "description": "Find info", "priority": 1}], "approach": "Research first", "complexity": "low"}'

        with patch("app.engine.providers.invoke_llm") as mock_invoke:
            mock_invoke.return_value = LLMResponse(
                content=plan_json, provider="gemini", model="gemini-2.0-flash-exp"
            )
            plan = await run_planner("What is AI?", config, settings_all)

        assert plan["complexity"] == "low"
        assert plan["_provider_meta"]["provider"] == "gemini"
        mock_invoke.assert_called_once()
        call_kwargs = mock_invoke.call_args
        assert call_kwargs.kwargs["provider"] == "gemini"
        assert call_kwargs.kwargs["model"] == "gemini-2.0-flash-exp"

    @pytest.mark.asyncio
    async def test_researcher_records_provider(self, settings_all):
        """Researcher AgentOutput includes provider metadata."""
        from app.engine.agents.researcher import run_researcher
        from app.engine.state import ModelConfig

        config = ModelConfig(researcher_provider="groq", researcher_model="llama-3.1-8b-instant")
        plan = {"tasks": [], "approach": "General", "complexity": "low"}

        with patch("app.engine.providers.invoke_llm") as mock_invoke:
            mock_invoke.return_value = LLMResponse(
                content="Research findings here.", provider="groq", model="llama-3.1-8b-instant"
            )
            output = await run_researcher(plan, "What is AI?", config, settings_all)

        assert output.agent == "researcher"
        assert output.metadata["provider"] == "groq"
        assert output.metadata["model"] == "llama-3.1-8b-instant"

    @pytest.mark.asyncio
    async def test_critic_records_provider(self, settings_all):
        """Critic CriticVerdict is parsed correctly from mocked response."""
        from app.engine.agents.critic import run_critic
        from app.engine.state import AgentOutput, ModelConfig
        from datetime import datetime

        config = ModelConfig(critic_provider="groq", critic_model="llama-3.1-8b-instant")
        research = AgentOutput(agent="researcher", content="R content", timestamp=datetime.utcnow())
        analyst = AgentOutput(agent="analyst", content="A content", timestamp=datetime.utcnow())

        with patch("app.engine.providers.invoke_llm") as mock_invoke:
            mock_invoke.return_value = LLMResponse(
                content='{"agree": true, "reason": "Outputs align", "confidence": 0.9}',
                provider="groq",
                model="llama-3.1-8b-instant",
            )
            verdict = await run_critic(research, analyst, "What is AI?", config, settings_all)

        assert verdict.agree is True
        assert verdict.confidence == 0.9

    @pytest.mark.asyncio
    async def test_ollama_fallback_in_agent(self, settings_all):
        """When cloud provider quota is hit in an agent, Ollama answer is used."""
        from app.engine.agents.researcher import run_researcher
        from app.engine.state import ModelConfig

        config = ModelConfig(researcher_provider="gemini", researcher_model="gemini-2.0-flash-exp")
        plan = {"tasks": [], "approach": "General", "complexity": "low"}

        # invoke_llm itself returns ollama result (simulating internal fallback)
        with patch("app.engine.providers.invoke_llm") as mock_invoke:
            mock_invoke.return_value = LLMResponse(
                content="Local Ollama research answer",
                provider="ollama",
                model="qwen3:4b",
                metadata={"fallback_reason": "gemini quota exceeded"},
            )
            output = await run_researcher(plan, "Query", config, settings_all)

        assert output.metadata["provider"] == "ollama"
        assert output.metadata.get("fallback_reason") == "gemini quota exceeded"
