"""Los fallos de red son accionables y nunca publican texto del proveedor."""
import json
import socket
import ssl
from types import SimpleNamespace
import pytest
from cafe.agent import run_agent
from cafe.llm_errors import connection_diagnostic


@pytest.mark.parametrize("status,code", [(401,"authentication"),(403,"access"),(404,"model"),(429,"rate_limit"),(503,"provider")])
def test_http_errors_are_distinguished(status, code):
    error = RuntimeError("Secret key and provider body must stay private")
    error.status_code = status
    diagnostic = connection_diagnostic(error)
    assert diagnostic["code"] == code
    assert diagnostic["status"] == status
    assert "Secret key" not in json.dumps(diagnostic)


@pytest.mark.parametrize("cause,code", [(PermissionError("private"),"network_permission"),
    (ssl.SSLCertVerificationError("private"),"certificate"),
    (socket.gaierror("private"),"dns"), (TimeoutError("private"),"timeout")])
def test_connection_cause_chain(cause, code):
    error = RuntimeError("private")
    error.__cause__ = cause
    assert connection_diagnostic(error)["code"] == code


def test_fallback_explains_connection_without_exposing_credentials(monkeypatch):
    import openai
    credentials = []
    class APIConnectionError(Exception):
        pass
    def fail(**kwargs):
        error = APIConnectionError("test-secret in provider body")
        error.__cause__ = ssl.SSLCertVerificationError("test-secret in certificate details")
        raise error
    def factory(**kwargs):
        credentials.append(kwargs)
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fail)))
    monkeypatch.setattr(openai, "OpenAI", factory)
    out = run_agent("precio del dólar", api_key="test-secret")
    assert out["mode"] == "fallback"
    assert out["llm_error"] == "APIConnectionError"
    assert out["llm_diagnostic"]["code"] == "certificate"
    assert "certificado HTTPS" in out["answer"]
    assert "test-secret" not in json.dumps(out)
    assert credentials[0]["max_retries"] == 1
