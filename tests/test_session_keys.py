"""Claves por llamada y por sesión; no se consulta a NVIDIA en estas pruebas."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
import pytest
from cafe import config as C
from cafe.agent import run_agent

USER_A='test-session-a'
USER_B='test-session-b'


def fake_client(captured):
    def factory(**credentials):
        def create(**kwargs):
            captured.append((credentials.copy(),kwargs))
            message=SimpleNamespace(content='Consulta fuera de alcance.',tool_calls=[])
            return SimpleNamespace(choices=[SimpleNamespace(message=message,finish_reason='stop')])
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return factory


def test_user_key_does_not_mutate_environment_config_or_messages(monkeypatch):
    import openai
    seen=[]
    monkeypatch.setattr(openai,'OpenAI',fake_client(seen))
    monkeypatch.setattr(C,'LLM_API_KEY','test-server-key')
    monkeypatch.setenv('LLM_API_KEY','test-server-env')
    out=run_agent('precio del dólar',api_key=USER_A,base_url='https://integrate.api.nvidia.com/v1')
    assert seen[0][0]['api_key']==USER_A
    assert C.LLM_API_KEY=='test-server-key'
    assert os.environ['LLM_API_KEY']=='test-server-env'
    assert USER_A not in json.dumps(out,ensure_ascii=False)
    assert USER_A not in json.dumps(seen[0][1],ensure_ascii=False)


def test_empty_user_key_does_not_fall_back_to_server_credentials(monkeypatch):
    import openai
    monkeypatch.setattr(C,'LLM_API_KEY','test-server-key')
    def forbidden(**kwargs):
        pytest.fail('La app no debe usar una clave del servidor si el visitante no ingresó una')
    monkeypatch.setattr(openai,'OpenAI',forbidden)
    assert run_agent('precio del dólar',api_key='')['mode']=='mock'


def test_default_cli_still_uses_environment_configuration(monkeypatch):
    import openai
    seen=[]
    monkeypatch.setattr(openai,'OpenAI',fake_client(seen))
    monkeypatch.setattr(C,'LLM_API_KEY','test-server-key')
    assert run_agent('precio del dólar')['mode']=='llm'
    assert seen[0][0]['api_key']=='test-server-key'


def test_parallel_calls_keep_different_keys(monkeypatch):
    import openai
    seen=[]
    monkeypatch.setattr(openai,'OpenAI',fake_client(seen))
    with ThreadPoolExecutor(max_workers=2) as pool:
        outputs=list(pool.map(lambda key:run_agent('precio del dólar',api_key=key),[USER_A,USER_B]))
    assert {credentials['api_key'] for credentials,_ in seen}=={USER_A,USER_B}
    assert all(o['mode']=='llm' for o in outputs)


def test_widgets_are_session_scoped_and_forget_does_not_affect_other_user(monkeypatch):
    from streamlit.testing.v1 import AppTest
    import cafe.agent as agent
    calls=[]
    def local_response(question,context,history,**kwargs):
        calls.append(kwargs)
        return {'answer':'Respuesta de prueba.','mode':'llm','trace':[],'answer_source':'llm'}
    monkeypatch.setattr(agent,'run_agent',local_response)
    monkeypatch.setattr(C,'LLM_API_KEY','test-server-key')
    dotenv=C.ROOT/'.env'
    before=dotenv.read_bytes() if dotenv.exists() else None
    a=AppTest.from_file(str(C.ROOT/'app.py'),default_timeout=60).run()
    b=AppTest.from_file(str(C.ROOT/'app.py'),default_timeout=60).run()
    assert not a.exception and not b.exception
    assert a.text_input(key='nvidia_api_key').value==''
    assert b.text_input(key='nvidia_api_key').value==''
    from streamlit.proto.TextInput_pb2 import TextInput
    assert a.text_input(key='nvidia_api_key').proto.type==TextInput.PASSWORD
    a.text_input(key='nvidia_api_key').input(USER_A).run()
    assert b.text_input(key='nvidia_api_key').value==''
    b.text_input(key='nvidia_api_key').input(USER_B).run()
    a.chat_input[0].set_value('precio del dólar').run()
    assert calls[-1]['api_key']==USER_A
    assert calls[-1]['base_url']=='https://integrate.api.nvidia.com/v1'
    assert USER_A not in json.dumps(a.session_state['chat'],ensure_ascii=False)
    button=next(button for button in a.button if button.label=='Olvidar mi clave')
    button.click().run()
    assert a.text_input(key='nvidia_api_key').value==''
    assert not a.exception
    assert b.text_input(key='nvidia_api_key').value==USER_B
    if before is not None:
        assert dotenv.read_bytes()==before
