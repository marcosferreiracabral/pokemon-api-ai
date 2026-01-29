import pytest
from httpx import AsyncClient
from api.main import app

# NOTA: Normalmente, esses testes exigem um banco de dados em execução ou uma sessão de banco de dados simulada.
# Para simplificar, neste ambiente, podemos ignorar a execução se o banco de dados não estiver disponível
# ou se as dependências simuladas não estiverem. Aqui, assumimos que podemos importar 'app', mas executá-lo requer a sobrescrita de 'get_db'.

@pytest.mark.asyncio
async def test_health_check():
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}

@pytest.mark.asyncio
async def test_root_path():
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Pokedex API v1" in response.json()["message"]
