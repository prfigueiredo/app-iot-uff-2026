"""
Sensor simulado do ar-condicionado do CPD.

Envia uma leitura em JSON para o backend a cada intervalo, como um sensor real
faria. A temperatura caminha aos poucos em direção ao valor de --alvo, o que
permite provocar um superaquecimento durante a demonstração.

Uso:
    python ar_condicionado.py
    python ar_condicionado.py --alvo 30 --intervalo 2
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request


def proxima_temperatura(atual: float, alvo: float) -> float:
    # Moves 15% of the way to the target per reading, plus a little noise.
    return round(atual + (alvo - atual) * 0.15 + random.uniform(-0.2, 0.2), 1)


def enviar(url: str, chave: str, leitura: dict) -> int:
    requisicao = urllib.request.Request(
        url,
        data=json.dumps(leitura).encode(),
        headers={"Content-Type": "application/json", "X-Sensor-Key": chave},
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=5) as resposta:
        return resposta.status


def main():
    parser = argparse.ArgumentParser(description="Sensor simulado do ar-condicionado")
    parser.add_argument("--url", default="http://127.0.0.1:8000/sensores/ar-condicionado")
    parser.add_argument("--chave", default="chave-sensor-dev")
    parser.add_argument("--intervalo", type=float, default=5, help="segundos entre leituras")
    parser.add_argument("--inicial", type=float, default=21.5, help="temperatura inicial em °C")
    parser.add_argument("--alvo", type=float, default=22, help="temperatura para onde a leitura tende")
    args = parser.parse_args()

    temperatura = args.inicial
    print(f"Enviando leituras para {args.url} a cada {args.intervalo}s (Ctrl+C para parar)")
    while True:
        temperatura = proxima_temperatura(temperatura, args.alvo)
        leitura = {"temperatura_c": temperatura, "status": "ligado"}
        try:
            status = enviar(args.url, args.chave, leitura)
            print(f"{time.strftime('%H:%M:%S')}  {json.dumps(leitura)}  -> HTTP {status}")
        except urllib.error.HTTPError as e:
            print(f"{time.strftime('%H:%M:%S')}  backend recusou a leitura: HTTP {e.code}")
        except urllib.error.URLError as e:
            print(f"{time.strftime('%H:%M:%S')}  backend indisponível: {e.reason}")
        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
