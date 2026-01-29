import asyncio
import websockets
import time
import argparse
import random
import json
import statistics

async def simulate_client(client_id, uri, messages_to_send):
    """Simula um único cliente conectando-se e trocando mensagens."""
    latencies = []
    errors = 0
    
    try:
        start_connect = time.time()
        async with websockets.connect(uri) as websocket:
            connect_time = (time.time() - start_connect) * 1000 # ms
            # print(f"Client {client_id}: Connected in {connect_time:.2f}ms")
            
            for msg in messages_to_send:
                start_req = time.time()
                await websocket.send(msg)
                _ = await websocket.recv()
                latency = (time.time() - start_req) * 1000 # ms
                latencies.append(latency)
                # Tempo de reflexão aleatório entre solicitações:
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
    except Exception as e:
        print(f"Client {client_id} error: {e}")
        errors += 1
        
    return latencies, errors

async def main():
    parser = argparse.ArgumentParser(description="WebSocket Async Load Test")
    parser.add_argument("--uri", default="ws://localhost:8000/ws", help="WebSocket URI")
    parser.add_argument("--clients", type=int, default=10, help="Number of concurrent clients")
    parser.add_argument("--messages", type=int, default=5, help="Messages per client")
    args = parser.parse_args()

    print(f"Starting load test on {args.uri}")
    print(f"Clients: {args.clients}, Messages per client: {args.messages}")

    messages_pool = [
        "Quem é Pikachu?",
        "Qual o tipo do Charizard?",
        "Liste pokemons de água",
        "Evolução do Eevee?",
        "Status do Mewtwo"
    ]

    tasks = []
    start_test = time.time()

    for i in range(args.clients):
        # Selecione mensagens aleatórias para este cliente:
        msgs = [random.choice(messages_pool) for _ in range(args.messages)]
        tasks.append(simulate_client(i, args.uri, msgs))

    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_test
    
    all_latencies = []
    total_errors = 0
    
    for latencies, errors in results:
        all_latencies.extend(latencies)
        total_errors += errors

    if not all_latencies:
        print("Nenhuma mensagem trocada com sucesso.")
        return
    
    print("\n--- Resultados ---")
    print(f"Tempo Total: {total_time:.2f}s")
    print(f"Total de Requisições: {len(all_latencies)}")
    print(f"Total de Erros: {total_errors}")
    print(f"Taxa de Transferência: {len(all_latencies) / total_time:.2f} req/s")
    print(f"Latência Média: {statistics.mean(all_latencies):.2f}ms")
    print(f"Latência P95: {statistics.quantiles(all_latencies, n=20)[18]:.2f}ms")
    print(f"Latência Mínima: {min(all_latencies):.2f}ms")
    print(f"Latência Máxima: {max(all_latencies):.2f}ms")

if __name__ == "__main__":
    asyncio.run(main())
