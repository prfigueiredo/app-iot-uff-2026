# FIWARE Orion

Broker intermediário entre os sensores e o backend. Os sensores publicam
entidades NGSI-v2 aqui, e o backend lê essas entidades. Um sensor novo só
precisa publicar uma entidade, sem mudança no backend.

## Subir e parar

Com o Docker Desktop aberto:

```bash
docker compose up -d
```

```bash
docker compose down
```

O Orion fica em `http://127.0.0.1:1026`. Os dados ficam no volume
`mongo-data` e sobrevivem a reinícios. Para apagar tudo, use
`docker compose down -v`.

## Conferir o que os sensores publicaram

```bash
curl "http://127.0.0.1:1026/v2/entities?options=keyValues"
```

## Entidade do ar-condicionado

```json
{
  "id": "urn:ngsi-ld:ArCondicionado:cpd-01",
  "type": "ArCondicionado",
  "temperatura": 22.3,
  "umidade": 48.0,
  "status": "ligado"
}
```

`temperatura` em °C. `umidade` em % (opcional). `status` é `ligado` ou
`desligado`.
