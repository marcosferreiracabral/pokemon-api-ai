import subprocess
import os
import shutil
import pytest

# Use o shutil para encontrar o script de ponto de entrada ou o bash:
ENTRYPOINT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "entrypoint.sh"))


def get_bash_command():
    """Find a suitable bash executable, preferring Git Bash on Windows."""
    # Verifique primeiro os locais comuns do Git Bash:
    git_bash_paths = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe"
    ]

    for path in git_bash_paths:
        if os.path.exists(path):
            return path
            
    # Recorrer ao PATH:
    cmd = shutil.which("bash")
    if cmd:
        # Verifique se realmente funciona (o WSL pode estar com problemas):
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return cmd
        except Exception:
            pass
            
    return None

BASH_CMD = get_bash_command()

@pytest.fixture
def mock_env():
    """Dispositivo que proporciona um ambiente básico."""
    return os.environ.copy()

def run_entrypoint(env_vars: dict, args: list = []):
    """Execute o ponto de entrada com as variáveis ​​de ambiente e argumentos fornecidos."""
    if not BASH_CMD:
        pytest.skip("Bash não encontrado neste sistema.")

    if not os.path.exists(ENTRYPOINT_PATH):
        pytest.fail(f"Script de ponto de entrada não encontrado em {ENTRYPOINT_PATH}")

    formatted_path = ENTRYPOINT_PATH.replace("\\", "/") # O Bash no Windows geralmente prefere barras invertidas.
    cmd = [BASH_CMD, formatted_path] + args
    
    # Mesclar ambiente atual com as variáveis ​​de ambiente fornecidas:
    env = os.environ.copy()
    env.update(env_vars)
    
    # Certifique-se de que o PYTHONPATH inclua a raiz do projeto:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{project_root}{os.pathsep}{current_pythonpath}"
    
    # Use o registro de codificação explícita em todo o processo:
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8', 
        errors='replace'
    )

    return result

def test_missing_vars():
    """Deve falhar se as variáveis ​​obrigatórias estiverem ausentes."""
    res = run_entrypoint({"OPENAI_API_KEY": ""})
    
    assert res.returncode == 1, f"Expected return code 1, got {res.returncode}. Output: {res.stdout} {res.stderr}"
    assert "Variáveis obrigatórias não definidas" in res.stdout or "Variáveis obrigatórias não definidas" in res.stderr

def test_invalid_app_env():
    """Deve falhar se APP_ENV for inválido."""
    # Precisamos de uma chave válida para ignorar a verificação de chave e chegar à verificação de ambiente.
    # Mas, como estamos chamando um subprocesso, a verificação ocorre dentro do subprocesso (código do agente) OU nas verificações do entrypoint.sh.
    # Seria bom analisar a lógica do entrypoint.sh, mas vamos assumir que ele verifica variáveis.
    
    res = run_entrypoint({
        "OPENAI_API_KEY": "sk-mock-key-for-test",
        "APP_ENV": "invalid-env"
    })
    
    assert res.returncode == 1
    assert "APP_ENV inválido" in res.stdout or "APP_ENV inválido" in res.stderr

@pytest.mark.integration
def test_valid_execution():
    """Deve passar com ambiente correto."""
    # Se não tivermos uma chave real, devemos confiar no script para lidar com ela ou simulá-la, se houver suporte.
    # O teste anterior usou uma chave simulada ou uma chave real.
    
    res = run_entrypoint(
        {
            "OPENAI_API_KEY": "sk-mock-key-mandatory",
            "APP_ENV": "production"
        },
        args=["python", "--version"]
    )
    
    if res.returncode != 0:
        pytest.fail(f"Execution failed: {res.stdout} {res.stderr}")
        
    assert res.returncode == 0
    assert "Todas validações passaram" in res.stdout

def test_json_logging_production():
    """Deve gerar logs em JSON em produção por padrão."""
    res = run_entrypoint(
        {
            "OPENAI_API_KEY": "sk-mock-key-for-test",
            "APP_ENV": "production"
        },
        args=["python", "--version"]
    )
    assert '{"timestamp":' in res.stdout
    assert '"level":"INFO"' in res.stdout

def test_text_logging_development():
    """Deve gerar logs em texto em desenvolvimento."""
    res = run_entrypoint(
        {
            "OPENAI_API_KEY": "sk-mock-key-for-test",
            "APP_ENV": "development"
        },
        args=["python", "--version"]
    )
    assert res.returncode == 0
    # Formato do texto: [TIMESTAMP] [LEVEL] [SERVICE] Mensagem:
    assert "] [INFO] [pokemon-agent]" in res.stdout
