"""Entidades, servicios, reservas y excepciones del proyecto Software FJ.

El diseño aplica abstracción, encapsulación, herencia, polimorfismo y
validaciones estrictas. No guarda datos de clientes ni reservas en archivos.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging
import re
from typing import Any, Literal, overload


# Las excepciones propias permiten reconocer los errores de negocio.
class ErrorSistema(Exception):
    """Error controlado de la aplicación."""


class ErrorValidacion(ErrorSistema):
    """Datos vacíos, mal formados o fuera del rango permitido."""


class ErrorDuplicado(ErrorSistema):
    """Ya existe un identificador o correo registrado."""


class ErrorNoEncontrado(ErrorSistema):
    """No existe la entidad solicitada."""


class ErrorDisponibilidad(ErrorSistema):
    """El servicio está inactivo o no tiene capacidad suficiente."""


class ErrorEstadoReserva(ErrorSistema):
    """La reserva no puede ejecutar la transición solicitada."""


class ErrorCalculo(ErrorSistema):
    """No es posible obtener un costo válido."""


# El redondeo monetario se centraliza para evitar resultados inconsistentes.
CENTAVO = Decimal("0.01")


def texto_obligatorio(valor: Any, nombre: str, minimo: int = 1) -> str:
    """Comprueba que el dato sea un texto no vacío."""
    if not isinstance(valor, str) or len(valor.strip()) < minimo:
        raise ErrorValidacion(f"{nombre}: escriba al menos {minimo} caracter(es).")
    return valor.strip()


def entero_positivo(valor: Any, nombre: str, maximo: int | None = None) -> int:
    """Exige enteros positivos y rechaza booleanos, que son subtipo de int."""
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
        raise ErrorValidacion(f"{nombre}: debe ser un entero positivo.")
    if maximo is not None and valor > maximo:
        raise ErrorValidacion(f"{nombre}: no puede superar {maximo}.")
    return valor


def dinero_positivo(valor: Any, nombre: str) -> Decimal:
    """Convierte un valor a Decimal, encadenando errores de conversión."""
    if isinstance(valor, bool):
        raise ErrorValidacion(f"{nombre}: valor monetario inválido.")
    try:
        resultado = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ErrorValidacion(f"{nombre}: valor monetario inválido.") from error
    if not resultado.is_finite() or resultado <= 0:
        raise ErrorValidacion(f"{nombre}: debe ser mayor que cero y finito.")
    if resultado > Decimal("1000000000"):
        raise ErrorValidacion(f"{nombre}: supera el límite permitido de 1 000 000 000.")
    return resultado


def porcentaje(valor: Any, nombre: str) -> Decimal:
    """Normaliza impuestos y descuentos en el rango inclusivo 0-100."""
    if isinstance(valor, bool):
        raise ErrorCalculo(f"{nombre}: porcentaje inválido.")
    try:
        resultado = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ErrorCalculo(f"{nombre}: porcentaje inválido.") from error
    if not resultado.is_finite() or not Decimal("0") <= resultado <= Decimal("100"):
        raise ErrorCalculo(f"{nombre}: debe estar entre 0 y 100.")
    return resultado


# Una entidad abstracta impide crear objetos sin descripción definida.
class Entidad(ABC):
    def __init__(self, identificador: str) -> None:
        self._identificador = texto_obligatorio(identificador, "Identificador", 2)

    @property
    def identificador(self) -> str:
        return self._identificador

    @abstractmethod
    def describir(self) -> str:
        """Presentación específica de la entidad."""


class Cliente(Entidad):
    """Cliente cuyos datos se mantienen encapsulados en atributos privados."""

    def __init__(self, identificador: str, nombre: str, correo: str, telefono: str) -> None:
        super().__init__(identificador)
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self._nombre = texto_obligatorio(valor, "Nombre", 3)

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        correo = texto_obligatorio(valor, "Correo electrónico")
        if not re.fullmatch(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", correo):
            raise ErrorValidacion("Correo electrónico: formato inválido.")
        self._correo = correo.lower()

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        telefono = texto_obligatorio(valor, "Teléfono")
        if not re.fullmatch(r"\+?[0-9]{7,15}", telefono):
            raise ErrorValidacion("Teléfono: use de 7 a 15 dígitos (prefijo + opcional).")
        self._telefono = telefono

    def describir(self) -> str:
        return f"{self.identificador} | {self.nombre} | {self.correo} | {self.telefono}"


class Servicio(Entidad, ABC):
    """Base abstracta de todos los servicios que ofrece Software FJ."""

    def __init__(self, identificador: str, nombre: str, tarifa_hora: Any) -> None:
        super().__init__(identificador)
        self._nombre = texto_obligatorio(nombre, "Nombre de servicio", 3)
        self._tarifa_hora = dinero_positivo(tarifa_hora, "Tarifa por hora")
        self._disponible = True

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_hora(self) -> Decimal:
        return self._tarifa_hora

    @property
    def disponible(self) -> bool:
        return self._disponible

    def establecer_disponibilidad(self, disponible: bool) -> None:
        if not isinstance(disponible, bool):
            raise ErrorValidacion("La disponibilidad debe ser verdadera o falsa.")
        self._disponible = disponible

    @property
    @abstractmethod
    def capacidad_operativa(self) -> int:
        """Número de unidades que pueden reservarse al mismo tiempo."""

    @abstractmethod
    def validar_parametros(self, duracion: int, **opciones: Any) -> None:
        """Comprueba duración y parámetros particulares del servicio."""

    @abstractmethod
    def calcular_costo(self, duracion: int, **opciones: Any) -> Decimal:
        """Costo bruto de un servicio antes de impuestos o descuentos."""

    @abstractmethod
    def consumo_capacidad(self, **opciones: Any) -> int:
        """Unidades de capacidad utilizadas por una reserva."""

    def _validar_opciones(self, opciones: dict[str, Any], admitidas: set[str]) -> None:
        desconocidas = set(opciones) - admitidas
        if desconocidas:
            raise ErrorValidacion("Parámetros desconocidos: " + ", ".join(sorted(desconocidas)))

    # Sobrecarga de firmas: uso básico o cálculo con porcentajes explícitos.
    # Python implementa ambas variantes con parámetros opcionales.
    @overload
    def calcular_total(self, duracion: int, **opciones: Any) -> Decimal: ...

    @overload
    def calcular_total(
        self, duracion: int, *, impuesto: Decimal, descuento: Decimal, **opciones: Any
    ) -> Decimal: ...

    def calcular_total(
        self, duracion: int, *, impuesto: Any = 0, descuento: Any = 0, **opciones: Any
    ) -> Decimal:
        """Aplica descuento primero y luego impuesto al costo polimórfico."""
        tasa = porcentaje(impuesto, "Impuesto")
        rebaja = porcentaje(descuento, "Descuento")
        bruto = self.calcular_costo(duracion, **opciones)
        if not bruto.is_finite() or bruto < 0:
            raise ErrorCalculo("El cálculo produjo un valor inválido.")
        total = bruto * (Decimal("1") - rebaja / 100) * (Decimal("1") + tasa / 100)
        if not total.is_finite() or total < 0:
            raise ErrorCalculo("El total calculado es inconsistente.")
        return total.quantize(CENTAVO, rounding=ROUND_HALF_UP)


class ServicioSala(Servicio):
    """Reserva de salas; cada sala acepta una reserva confirmada simultánea."""

    def __init__(self, identificador: str, nombre: str, tarifa_hora: Any, capacidad: int) -> None:
        super().__init__(identificador, nombre, tarifa_hora)
        self._capacidad_personas = entero_positivo(capacidad, "Capacidad de personas", 1000)

    @property
    def capacidad_operativa(self) -> int:
        return 1

    def validar_parametros(self, duracion: int, **opciones: Any) -> None:
        entero_positivo(duracion, "Duración", 24)
        self._validar_opciones(opciones, {"personas", "proyector"})
        personas = entero_positivo(opciones.get("personas", 1), "Número de personas")
        if personas > self._capacidad_personas:
            raise ErrorValidacion(f"La sala admite como máximo {self._capacidad_personas} personas.")
        if not isinstance(opciones.get("proyector", False), bool):
            raise ErrorValidacion("Proyector debe ser verdadero o falso.")

    def calcular_costo(self, duracion: int, **opciones: Any) -> Decimal:
        self.validar_parametros(duracion, **opciones)
        extra = Decimal("15000") if opciones.get("proyector", False) else Decimal("0")
        return (self.tarifa_hora + extra) * duracion

    def consumo_capacidad(self, **opciones: Any) -> int:
        return 1

    def describir(self) -> str:
        return (f"{self.identificador} | Sala: {self.nombre} | ${self.tarifa_hora}/hora "
                f"| {self._capacidad_personas} personas | disponible: {self.disponible}")


class ServicioEquipo(Servicio):
    """Alquiler por unidades; cada equipo reduce el inventario disponible."""

    def __init__(self, identificador: str, nombre: str, tarifa_hora: Any, stock: int) -> None:
        super().__init__(identificador, nombre, tarifa_hora)
        self._stock = entero_positivo(stock, "Stock de equipos", 10000)

    @property
    def capacidad_operativa(self) -> int:
        return self._stock

    def validar_parametros(self, duracion: int, **opciones: Any) -> None:
        entero_positivo(duracion, "Duración", 24)
        self._validar_opciones(opciones, {"unidades"})
        unidades = entero_positivo(opciones.get("unidades", 1), "Unidades")
        if unidades > self._stock:
            raise ErrorValidacion("Las unidades solicitadas superan el stock total.")

    def calcular_costo(self, duracion: int, **opciones: Any) -> Decimal:
        self.validar_parametros(duracion, **opciones)
        return self.tarifa_hora * duracion * opciones.get("unidades", 1)

    def consumo_capacidad(self, **opciones: Any) -> int:
        return opciones.get("unidades", 1)

    def describir(self) -> str:
        return (f"{self.identificador} | Equipo: {self.nombre} | ${self.tarifa_hora}/hora "
                f"| stock: {self._stock} | disponible: {self.disponible}")


class ServicioAsesoria(Servicio):
    """Asesoría virtual o presencial con máximo cuatro horas por sesión."""

    def __init__(
        self, identificador: str, nombre: str, tarifa_hora: Any, especialistas: int
    ) -> None:
        super().__init__(identificador, nombre, tarifa_hora)
        self._especialistas = entero_positivo(especialistas, "Especialistas", 1000)

    @property
    def capacidad_operativa(self) -> int:
        return self._especialistas

    def validar_parametros(self, duracion: int, **opciones: Any) -> None:
        entero_positivo(duracion, "Duración", 4)
        self._validar_opciones(opciones, {"modalidad"})
        if opciones.get("modalidad", "virtual") not in ("virtual", "presencial"):
            raise ErrorValidacion("Modalidad: solo se permite 'virtual' o 'presencial'.")

    def calcular_costo(self, duracion: int, **opciones: Any) -> Decimal:
        self.validar_parametros(duracion, **opciones)
        factor = Decimal("1.20") if opciones.get("modalidad", "virtual") == "presencial" else Decimal("1")
        return self.tarifa_hora * duracion * factor

    def consumo_capacidad(self, **opciones: Any) -> int:
        return 1

    def describir(self) -> str:
        return (f"{self.identificador} | Asesoría: {self.nombre} | ${self.tarifa_hora}/hora "
                f"| especialistas: {self._especialistas} | disponible: {self.disponible}")


Estado = Literal["Pendiente", "Confirmada", "Cancelada"]


class Reserva(Entidad):
    """Asocia a un cliente con un servicio y administra el estado de la reserva."""

    def __init__(
        self, identificador: str, cliente: Cliente, servicio: Servicio,
        duracion: int, opciones: dict[str, Any] | None = None
    ) -> None:
        super().__init__(identificador)
        if not isinstance(cliente, Cliente) or not isinstance(servicio, Servicio):
            raise ErrorValidacion("La reserva requiere un cliente y un servicio válidos.")
        self._cliente = cliente
        self._servicio = servicio
        self._duracion = entero_positivo(duracion, "Duración", 24)
        if opciones is not None and not isinstance(opciones, dict):
            raise ErrorValidacion("Las opciones deben enviarse como diccionario.")
        self._opciones = dict(opciones or {})
        self._estado: Estado = "Pendiente"
        self._total: Decimal | None = None
        self._logger = logging.getLogger("software_fj")

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion(self) -> int:
        return self._duracion

    @property
    def opciones(self) -> dict[str, Any]:
        return dict(self._opciones)  # Devolver copia evita modificaciones externas.

    @property
    def estado(self) -> Estado:
        return self._estado

    @property
    def total(self) -> Decimal | None:
        return self._total

    def confirmar(self, total: Decimal) -> None:
        if self._estado != "Pendiente":
            raise ErrorEstadoReserva(f"No se puede confirmar una reserva {self._estado.lower()}.")
        if not isinstance(total, Decimal) or not total.is_finite() or total < 0:
            raise ErrorCalculo("El total de la reserva es inválido.")
        self._total = total
        self._estado = "Confirmada"

    def cancelar(self) -> None:
        if self._estado == "Cancelada":
            raise ErrorEstadoReserva("La reserva ya está cancelada.")
        self._estado = "Cancelada"
        self._logger.info("Reserva cancelada: %s", self.identificador)

    def procesar(self, impuesto: Any = 0, descuento: Any = 0) -> Decimal:
        """Demuestra try/except/else/finally manteniendo estado consistente."""
        self._logger.info("Comienza procesamiento de la reserva %s", self.identificador)
        try:
            if self.estado != "Pendiente":
                raise ErrorEstadoReserva("Solo pueden procesarse reservas pendientes.")
            if not self.servicio.disponible:
                raise ErrorDisponibilidad("El servicio se encuentra deshabilitado.")
            self.servicio.validar_parametros(self.duracion, **self._opciones)
            costo = self.servicio.calcular_total(
                self.duracion, impuesto=impuesto, descuento=descuento, **self._opciones
            )
        except ErrorSistema as error:
            self._logger.error("Error en procesamiento %s: %s", self.identificador, error)
            raise
        else:
            self.confirmar(costo)
            self._logger.info("Reserva confirmada: %s por $%s", self.identificador, costo)
            return costo
        finally:
            self._logger.info("Finaliza intento de proceso: %s", self.identificador)

    def describir(self) -> str:
        total = "pendiente" if self.total is None else f"${self.total}"
        return (f"{self.identificador} | Cliente {self.cliente.identificador} | "
                f"Servicio {self.servicio.identificador} | {self.duracion} h | "
                f"{self.estado} | Total: {total}")
