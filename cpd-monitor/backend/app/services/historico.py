"""
Builds the periodic averages of the history (V3), one per hour by default.

Pure logic, no database: readings go in, closed periods come out, and the
caller decides where to store them. A period with no readings produces no
average at all, so a dead sensor shows up as a gap instead of a made-up value.
"""
from datetime import datetime, timedelta

from app.persistencia.repositorio import MediaPeriodo


class AgregadorDeMedias:
    def __init__(self, minutos: int):
        if minutos <= 0 or 1440 % minutos:
            raise ValueError("O intervalo precisa dividir o dia em partes iguais (1, 5, 15, 30, 60, 120...)")
        self.minutos = minutos
        self._inicio: datetime | None = None
        self._temperaturas: list[float] = []
        self._umidades: list[float] = []
        self._ultima_leitura: datetime | None = None

    def inicio_do_periodo(self, momento: datetime) -> datetime:
        minuto_do_dia = momento.hour * 60 + momento.minute
        inicio = minuto_do_dia - minuto_do_dia % self.minutos
        return momento.replace(hour=inicio // 60, minute=inicio % 60, second=0, microsecond=0)

    def adicionar(self, medido_em: datetime, temperatura: float, umidade: float | None) -> list[MediaPeriodo]:
        """Adds one sensor reading. Returns the period it closed, if any."""
        # The backend polls faster than the sensor publishes, so the same
        # reading arrives several times. Only a newer one counts.
        if self._ultima_leitura is not None and medido_em <= self._ultima_leitura:
            return []
        self._ultima_leitura = medido_em

        fechados = []
        inicio = self.inicio_do_periodo(medido_em)
        if self._inicio is not None and inicio != self._inicio:
            fechados.append(self._fechar())
        self._inicio = inicio
        self._temperaturas.append(temperatura)
        if umidade is not None:
            self._umidades.append(umidade)
        return fechados

    def fechar_vencidos(self, agora: datetime) -> list[MediaPeriodo]:
        """Closes the open period once its time is over, even if the sensor
        stopped publishing and no newer reading will ever close it."""
        if self._inicio is not None and agora >= self._inicio + timedelta(minutes=self.minutos):
            return [self._fechar()]
        return []

    def esvaziar(self) -> list[MediaPeriodo]:
        """Returns the open period as it is. Used on shutdown: the stored
        partial average is merged with the rest of the period after restart."""
        return [self._fechar()] if self._inicio is not None else []

    def _fechar(self) -> MediaPeriodo:
        temperaturas, umidades = self._temperaturas, self._umidades
        media = MediaPeriodo(
            inicio=self._inicio,
            minutos=self.minutos,
            amostras=len(temperaturas),
            temperatura_media=sum(temperaturas) / len(temperaturas),
            temperatura_min=min(temperaturas),
            temperatura_max=max(temperaturas),
            amostras_umidade=len(umidades),
            umidade_media=sum(umidades) / len(umidades) if umidades else None,
            umidade_min=min(umidades) if umidades else None,
            umidade_max=max(umidades) if umidades else None,
        )
        self._inicio, self._temperaturas, self._umidades = None, [], []
        return media
