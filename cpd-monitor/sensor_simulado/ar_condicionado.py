"""
Sensor simulado do ar-condicionado do CPD.

Publica uma leitura em JSON no FIWARE Orion a cada intervalo, como um sensor
real faria. O backend lê a leitura do Orion. Temperatura e umidade caminham
aos poucos em direção a --alvo e --umidade-alvo, o que permite provocar cada
alerta durante a demonstração.

Uso:
    python ar_condicionado.py
    python ar_condicionado.py --alvo 31 --intervalo 2       # superaquecimento
    python ar_condicionado.py --umidade-alvo 75             # possível vazamento
    python ar_condicionado.py --status desligado            # ar-condicionado desligado
    python ar_condicionado.py --id urn:ngsi-ld:ArCondicionado:cpd-02
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request


def aproximar(atual: float, alvo: float, ruido: float) -> float:
    # Moves 15% of the way to the target per reading, plus a little noise.
    return round(atual + (alvo - atual) * 0.15 + random.uniform(-ruido, ruido), 1)


def publicar(orion: str, entidade: dict) -> int:
    # upsert creates the entity on the first reading and updates it afterwards,
    # so a new sensor registers itself just by publishing.
    requisicao = urllib.request.Request(
        f"{orion}/v2/entities?options=upsert,keyValues",
        data=json.dumps(entidade).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(requisicao, timeout=5) as resposta:
        return resposta.status


def main():
    parser = argparse.ArgumentParser(description="Sensor simulado do ar-condicionado")
    parser.add_argument("--orion", default="http://127.0.0.1:1026", help="URL do FIWARE Orion")
    parser.add_argument("--id", default="urn:ngsi-ld:ArCondicionado:cpd-01", help="id da entidade no Orion")
    parser.add_argument("--intervalo", type=float, default=5, help="segundos entre leituras")
    parser.add_argument("--inicial", type=float, default=21.5, help="temperatura inicial em °C")
    parser.add_argument("--alvo", type=float, default=22, help="temperatura para onde a leitura tende")
    parser.add_argument("--umidade-inicial", type=float, default=48, help="umidade inicial em %%")
    parser.add_argument("--umidade-alvo", type=float, default=48, help="umidade para onde a leitura tende")
    parser.add_argument("--status", choices=["ligado", "desligado"], default="ligado")
    args = parser.parse_args()

    temperatura, umidade = args.inicial, args.umidade_inicial
    print(f"Publicando {args.id} em {args.orion} a cada {args.intervalo}s (Ctrl+C para parar)")
    while True:
        temperatura = aproximar(temperatura, args.alvo, ruido=0.2)
        umidade = min(100.0, max(0.0, aproximar(umidade, args.umidade_alvo, ruido=0.5)))
        entidade = {
            "id": args.id,
            "type": "ArCondicionado",
            "temperatura": temperatura,
            "umidade": umidade,
            "status": args.status,
        }
        try:
            status = publicar(args.orion, entidade)
            print(f"{time.strftime('%H:%M:%S')}  {temperatura}°C  {umidade}%  {args.status}  -> Orion HTTP {status}")
        except urllib.error.HTTPError as e:
            print(f"{time.strftime('%H:%M:%S')}  Orion recusou a leitura: HTTP {e.code} {e.read().decode()}")
        except urllib.error.URLError as e:
            print(f"{time.strftime('%H:%M:%S')}  Orion indisponível: {e.reason}")
        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
