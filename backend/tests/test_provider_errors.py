from types import SimpleNamespace

import pytest

from backend import main
from backend.services.provider_errors import ScreeningUnavailableError, provider_error


@pytest.mark.parametrize('code,expected', [(404, 'model is unavailable'), (429, 'quota'), (403, 'rejected access'), (400, 'rejected the request'), (503, 'temporarily unavailable'), (None, 'internet connection')])
def test_diagnostics_do_not_expose_raw_provider_error(code, expected):
    exc = RuntimeError('secret-key-and-patient-data')
    exc.code = code
    result = str(provider_error(exc))
    assert expected in result
    assert 'secret-key-and-patient-data' not in result


def test_failed_model_tries_next_model(monkeypatch):
    calls = []
    def generate_content(*, model, contents, config):
        calls.append(model)
        if model == 'missing-model':
            exc = RuntimeError('private raw error')
            exc.code = 404
            raise exc
        return SimpleNamespace(text='OK')
    monkeypatch.setattr(main, 'client', SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))
    monkeypatch.setattr(main, 'MODEL_FALLBACK_CHAIN', ['missing-model', 'working-model'])
    _, model = main.generate_with_fallback('test')
    assert model == 'working-model'
    assert calls == ['missing-model', 'working-model']


def test_all_models_fail_with_actionable_error(monkeypatch):
    def generate_content(**kwargs):
        exc = RuntimeError('private raw error')
        exc.code = 429
        raise exc
    monkeypatch.setattr(main, 'client', SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))
    with pytest.raises(ScreeningUnavailableError, match='quota'):
        main.generate_with_fallback('test')


@pytest.mark.parametrize('code', [400, 401, 403])
def test_access_and_request_errors_stop_model_fallback(monkeypatch, code):
    calls = []
    def generate_content(**kwargs):
        calls.append(kwargs['model'])
        error = RuntimeError('private provider response')
        error.code = code
        raise error
    monkeypatch.setattr(main, 'client', SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))
    monkeypatch.setattr(main, 'MODEL_FALLBACK_CHAIN', ['first', 'second'])
    with pytest.raises(ScreeningUnavailableError):
        main.generate_with_fallback('test')
    assert calls == ['first']


def test_missing_fallback_model_does_not_hide_quota_error(monkeypatch):
    def generate_content(**kwargs):
        error = RuntimeError('private provider response')
        error.code = 429 if kwargs['model'] == 'first' else 404
        raise error
    monkeypatch.setattr(main, 'client', SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))
    monkeypatch.setattr(main, 'MODEL_FALLBACK_CHAIN', ['first', 'missing'])
    with pytest.raises(ScreeningUnavailableError, match='quota'):
        main.generate_with_fallback('test')
