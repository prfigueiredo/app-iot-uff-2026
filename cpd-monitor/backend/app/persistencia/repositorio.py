"""
Storage contract for the history (V3): alerts and periodic averages.

Two implementations follow the same contract: RepositorioPostgres (the real
one) and RepositorioMemoria (tests and runs without a database). The same
test suite runs against both, so they cannot drift apart.
"""
import threading
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class MediaPeriodo:
    """Temperature and humidity summary for one period (one hour by default)."""

    inicio: datetime
    minutos: int
    amostras: int
    temperatura_media: float
    temperatura_min: float
    temperatura_max: float
    amostras_umidade: int = 0
    umidade_media: float | None = None
    umidade_min: float | None = None
    umidade_max: float | None = None

    def mesclar(self, outra: "MediaPeriodo") -> "MediaPeriodo":
        """Combines two partial summaries of the same period, weighting each
        average by its number of samples. Happens when the backend restarts
        in the middle of a period."""
        total = self.amostras + outra.amostras
        total_umidade = self.amostras_umidade + outra.amostras_umidade
        umidade_media = None
        if total_umidade:
            umidade_media = (
                (self.umidade_media or 0) * self.amostras_umidade + (outra.umidade_media or 0) * outra.amostras_umidade
            ) / total_umidade
        return replace(
            self,
            amostras=total,
            temperatura_media=(self.temperatura_media * self.amostras + outra.temperatura_media * outra.amostras) / total,
            temperatura_min=min(self.temperatura_min, outra.temperatura_min),
            temperatura_max=max(self.temperatura_max, outra.temperatura_max),
            amostras_umidade=total_umidade,
            umidade_media=umidade_media,
            umidade_min=_menor(self.umidade_min, outra.umidade_min),
            umidade_max=_maior(self.umidade_max, outra.umidade_max),
        )

    def para_json(self) -> dict:
        dados = asdict(self)
        dados["inicio"] = self.inicio.isoformat()
        return dados


def _menor(a, b):
    return b if a is None else a if b is None else min(a, b)


def _maior(a, b):
    return b if a is None else a if b is None else max(a, b)


class Repositorio(Protocol):
    def salvar_alerta(self, alerta: dict) -> dict:
        """Stores an alert without id and returns it with its new id."""

    def listar_alertas(
        self,
        desde: datetime | None = None,
        ate: datetime | None = None,
        condicao: str | None = None,
        limite: int = 100,
    ) -> list[dict]:
        """Newest first."""

    def marcar_lido(self, alerta_id: int) -> dict | None:
        """Returns the updated alert, or None when it does not exist."""

    def salvar_media(self, media: MediaPeriodo) -> None:
        """Stores a period, merging with what is already stored for it."""

    def listar_medias(self, minutos: int, desde: datetime, ate: datetime) -> list[MediaPeriodo]:
        """Periods starting in [desde, ate), oldest first."""

    def fechar(self) -> None:
        ...


class RepositorioMemoria:
    """Keeps everything in lists. Data is lost when the process ends."""

    def __init__(self):
        self._trava = threading.Lock()  # called from worker threads
        self._alertas: list[dict] = []
        self._medias: dict[tuple[datetime, int], MediaPeriodo] = {}
        self._proximo_id = 1

    def salvar_alerta(self, alerta: dict) -> dict:
        with self._trava:
            salvo = {**alerta, "id": self._proximo_id}
            self._proximo_id += 1
            self._alertas.append(salvo)
            return dict(salvo)

    def listar_alertas(self, desde=None, ate=None, condicao=None, limite=100) -> list[dict]:
        with self._trava:
            alertas = [
                dict(a)
                for a in self._alertas
                if (desde is None or datetime.fromisoformat(a["data"]) >= desde)
                and (ate is None or datetime.fromisoformat(a["data"]) < ate)
                and (condicao is None or a["condicao"] == condicao)
            ]
        alertas.sort(key=lambda a: (a["data"], a["id"]), reverse=True)
        return alertas[:limite]

    def marcar_lido(self, alerta_id: int) -> dict | None:
        with self._trava:
            for alerta in self._alertas:
                if alerta["id"] == alerta_id:
                    alerta["lido"] = True
                    return dict(alerta)
        return None

    def salvar_media(self, media: MediaPeriodo) -> None:
        with self._trava:
            chave = (media.inicio, media.minutos)
            existente = self._medias.get(chave)
            self._medias[chave] = existente.mesclar(media) if existente else media

    def listar_medias(self, minutos: int, desde: datetime, ate: datetime) -> list[MediaPeriodo]:
        with self._trava:
            medias = [m for (inicio, mins), m in self._medias.items() if mins == minutos and desde <= inicio < ate]
        return sorted(medias, key=lambda m: m.inicio)

    def fechar(self) -> None:
        pass
