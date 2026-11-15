"""Gestión de clientes, servicios y reservas exclusivamente en memoria."""

from __future__ import annotations

from pathlib import Path
import logging
from typing import Any

from modelo import (
    Cliente, Entidad, ErrorDisponibilidad, ErrorDuplicado, ErrorNoEncontrado,
    ErrorSistema, ErrorValidacion, Reserva, Servicio, entero_positivo,
    texto_obligatorio,
)


def configurar_logger(ruta: Path | None = None) -> logging.Logger:
    """Crea logs persistentes; nunca guarda información de clientes en ellos."""
    logger = logging.getLogger("software_fj")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        archivo = ruta if ruta is not None else Path(__file__).resolve().parent / "software_fj.log"
        manejador = logging.FileHandler(archivo, encoding="utf-8")
        manejador.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(manejador)
    return logger


class GestorSoftwareFJ:
    """Controlador en memoria que controla duplicados y ocupación de recursos."""

    def __init__(self) -> None:
        self._clientes: dict[str, Cliente] = {}
        self._servicios: dict[str, Servicio] = {}
        self._reservas: dict[str, Reserva] = {}
        self._logger = configurar_logger()

    def registrar_cliente(self, cliente: Cliente) -> Cliente:
        if not isinstance(cliente, Cliente):
            raise ErrorValidacion("Se esperaba una instancia de Cliente.")
        if cliente.identificador in self._clientes:
            raise ErrorDuplicado("Identificador de cliente ya registrado.")
        if any(c.correo == cliente.correo for c in self._clientes.values()):
            raise ErrorDuplicado("El correo electrónico ya está registrado.")
        self._clientes[cliente.identificador] = cliente
        self._logger.info("Cliente registrado: %s", cliente.identificador)
        return cliente

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        if not isinstance(servicio, Servicio):
            raise ErrorValidacion("Se esperaba un servicio válido.")
        if servicio.identificador in self._servicios:
            raise ErrorDuplicado("Identificador de servicio ya registrado.")
        self._servicios[servicio.identificador] = servicio
        self._logger.info("Servicio registrado: %s", servicio.identificador)
        return servicio

    def obtener_cliente(self, identificador: str) -> Cliente:
        clave = texto_obligatorio(identificador, "Identificador")
        try:
            return self._clientes[clave]
        except KeyError as error:
            raise ErrorNoEncontrado(f"No existe el cliente {clave}.") from error

    def obtener_servicio(self, identificador: str) -> Servicio:
        clave = texto_obligatorio(identificador, "Identificador")
        try:
            return self._servicios[clave]
        except KeyError as error:
            raise ErrorNoEncontrado(f"No existe el servicio {clave}.") from error

    def obtener_reserva(self, identificador: str) -> Reserva:
        clave = texto_obligatorio(identificador, "Identificador")
        try:
            return self._reservas[clave]
        except KeyError as error:
            raise ErrorNoEncontrado(f"No existe la reserva {clave}.") from error

    def crear_reserva(
        self, identificador: str, id_cliente: str, id_servicio: str,
        duracion: int, **opciones: Any
    ) -> Reserva:
        if identificador in self._reservas:
            raise ErrorDuplicado("Identificador de reserva ya registrado.")
        cliente = self.obtener_cliente(id_cliente)
        servicio = self.obtener_servicio(id_servicio)
        reserva = Reserva(identificador, cliente, servicio, duracion, opciones)
        self._reservas[reserva.identificador] = reserva
        self._logger.info("Reserva creada: %s en estado pendiente", reserva.identificador)
        return reserva

    def _comprobar_disponibilidad(self, reserva: Reserva) -> None:
        """Rechaza reservas concurrentes que superen el inventario del servicio."""
        servicio = reserva.servicio
        servicio.validar_parametros(reserva.duracion, **reserva.opciones)
        if not servicio.disponible:
            raise ErrorDisponibilidad("El servicio está temporalmente inactivo.")
        ocupado = sum(
            anterior.servicio.consumo_capacidad(**anterior.opciones)
            for anterior in self._reservas.values()
            if anterior.servicio.identificador == servicio.identificador
            and anterior.estado == "Confirmada"
        )
        solicitado = servicio.consumo_capacidad(**reserva.opciones)
        if ocupado + solicitado > servicio.capacidad_operativa:
            raise ErrorDisponibilidad(
                f"Capacidad insuficiente: ocupada {ocupado}, requerida {solicitado}, "
                f"máximo {servicio.capacidad_operativa}."
            )

    def procesar_reserva(self, identificador: str, impuesto: Any = 0, descuento: Any = 0):
        reserva = self.obtener_reserva(identificador)
        try:
            if reserva.estado != "Pendiente":
                # La comprobación de estado impide reusar indebidamente recursos.
                raise ErrorValidacion("Solo se pueden procesar reservas pendientes.")
            self._comprobar_disponibilidad(reserva)
            return reserva.procesar(impuesto=impuesto, descuento=descuento)
        except ErrorSistema as error:
            self._logger.error("Fallo al procesar %s: %s", identificador, error)
            raise

    def cancelar_reserva(self, identificador: str) -> Reserva:
        reserva = self.obtener_reserva(identificador)
        reserva.cancelar()
        return reserva

    def cambiar_disponibilidad(self, identificador: str, disponible: bool) -> None:
        servicio = self.obtener_servicio(identificador)
        servicio.establecer_disponibilidad(disponible)
        self._logger.info("Servicio %s disponible=%s", identificador, disponible)

    def listar_clientes(self) -> tuple[Cliente, ...]:
        return tuple(self._clientes.values())

    def listar_servicios(self) -> tuple[Servicio, ...]:
        return tuple(self._servicios.values())

    def listar_reservas(self) -> tuple[Reserva, ...]:
        return tuple(self._reservas.values())
