"""Simulación automática de operaciones exitosas e inválidas.

Ejecutar: python simulacion.py
Cada caso sigue su curso incluso si otro caso produce un error esperado.
"""

from collections import Counter
from typing import Callable

from gestor import GestorSoftwareFJ, configurar_logger
from modelo import (
    Cliente, ErrorSistema, ServicioAsesoria, ServicioEquipo, ServicioSala,
)


def ejecutar_simulacion(mostrar: bool = True) -> tuple[Counter, list[str]]:
    gestor = GestorSoftwareFJ()
    log = configurar_logger()
    resumen: Counter = Counter()
    resultados: list[str] = []

    def caso(numero: int, nombre: str, operacion: Callable, error_esperado: bool = False) -> None:
        """Registra el resultado, validando tanto los éxitos como los rechazos."""
        try:
            resultado = operacion()
        except ErrorSistema as error:
            log.error("Caso %s - %s - %s", numero, nombre, error)
            if error_esperado:
                resumen["error_controlado"] += 1
                linea = f"{numero:02}. ERROR CONTROLADO | {nombre} | {error}"
            else:
                resumen["fallo_inesperado"] += 1
                linea = f"{numero:02}. FALLO INESPERADO | {nombre} | {error}"
        except Exception as error:
            # Un error no previsto se registra, pero no cierra la simulación.
            log.exception("Error no previsto en caso %s", numero)
            resumen["fallo_inesperado"] += 1
            linea = f"{numero:02}. FALLO INESPERADO | {nombre} | {type(error).__name__}: {error}"
        else:
            if error_esperado:
                resumen["fallo_inesperado"] += 1
                linea = f"{numero:02}. FALLO: debió rechazarse | {nombre}"
            else:
                resumen["correcto"] += 1
                info = f" | {resultado}" if resultado is not None and not hasattr(resultado, "describir") else ""
                linea = f"{numero:02}. CORRECTO | {nombre}{info}"
        finally:
            resultados.append(linea)
            if mostrar:
                print(linea)

    caso(1, "Registrar cliente C001", lambda: gestor.registrar_cliente(
        Cliente("C001", "Ana Torres", "ana@ejemplo.com", "3001234567")))
    caso(2, "Registrar cliente C002", lambda: gestor.registrar_cliente(
        Cliente("C002", "Luis Pérez", "luis@ejemplo.com", "3111234567")))
    caso(3, "Rechazar identificador duplicado", lambda: gestor.registrar_cliente(
        Cliente("C001", "Otro Cliente", "otro@ejemplo.com", "3121234567")), True)
    caso(4, "Rechazar correo inválido", lambda: gestor.registrar_cliente(
        Cliente("C003", "María López", "correo_sin_arroba", "3001234567")), True)
    caso(5, "Rechazar teléfono inválido", lambda: gestor.registrar_cliente(
        Cliente("C004", "María López", "maria@ejemplo.com", "123")), True)
    caso(6, "Crear servicio de sala", lambda: gestor.registrar_servicio(
        ServicioSala("S001", "Sala de reuniones", 50000, 8)))
    caso(7, "Crear servicio de equipos", lambda: gestor.registrar_servicio(
        ServicioEquipo("S002", "Proyectores", 20000, 2)))
    caso(8, "Crear servicio de asesoría", lambda: gestor.registrar_servicio(
        ServicioAsesoria("S003", "Asesoría informática", 80000, 2)))
    caso(9, "Rechazar tarifa negativa", lambda: gestor.registrar_servicio(
        ServicioSala("S004", "Sala inválida", -1, 5)), True)
    caso(10, "Rechazar servicio duplicado", lambda: gestor.registrar_servicio(
        ServicioEquipo("S001", "Otra sala", 10000, 2)), True)
    caso(11, "Crear reserva de sala R001", lambda: gestor.crear_reserva(
        "R001", "C001", "S001", 2, personas=4, proyector=True))
    caso(12, "Confirmar R001 con impuesto y descuento", lambda: gestor.procesar_reserva(
        "R001", impuesto=19, descuento=10))
    caso(13, "Crear reserva de sala R002", lambda: gestor.crear_reserva(
        "R002", "C002", "S001", 1, personas=3))
    caso(14, "Rechazar sala ocupada", lambda: gestor.procesar_reserva("R002"), True)
    caso(15, "Cancelar R001 y liberar sala", lambda: gestor.cancelar_reserva("R001"))
    caso(16, "Confirmar R002 tras cancelación", lambda: gestor.procesar_reserva("R002"))
    caso(17, "Crear alquiler de dos equipos", lambda: gestor.crear_reserva(
        "R003", "C001", "S002", 3, unidades=2))
    caso(18, "Confirmar alquiler de dos equipos", lambda: gestor.procesar_reserva("R003"))
    caso(19, "Crear alquiler de otro equipo", lambda: gestor.crear_reserva(
        "R004", "C002", "S002", 1, unidades=1))
    caso(20, "Rechazar alquiler sin stock", lambda: gestor.procesar_reserva("R004"), True)
    caso(21, "Crear asesoría virtual", lambda: gestor.crear_reserva(
        "R005", "C001", "S003", 2, modalidad="virtual"))
    caso(22, "Confirmar asesoría virtual", lambda: gestor.procesar_reserva("R005"))
    caso(23, "Crear reserva con modalidad incorrecta", lambda: gestor.crear_reserva(
        "R006", "C002", "S003", 1, modalidad="telepatía"))
    caso(24, "Rechazar modalidad incorrecta", lambda: gestor.procesar_reserva("R006"), True)
    caso(25, "Rechazar duración de cinco horas en asesoría", lambda: gestor.crear_reserva(
        "R007", "C002", "S003", 5, modalidad="virtual") and gestor.procesar_reserva("R007"), True)
    caso(26, "Rechazar cliente inexistente", lambda: gestor.crear_reserva(
        "R008", "C999", "S003", 1), True)
    caso(27, "Rechazar duración cero", lambda: gestor.crear_reserva(
        "R009", "C001", "S003", 0), True)
    caso(28, "Cancelar asesoría R005", lambda: gestor.cancelar_reserva("R005"))
    caso(29, "Rechazar doble cancelación", lambda: gestor.cancelar_reserva("R005"), True)
    caso(30, "Crear asesoría presencial", lambda: gestor.crear_reserva(
        "R010", "C001", "S003", 1, modalidad="presencial"))
    caso(31, "Rechazar impuesto excesivo", lambda: gestor.procesar_reserva(
        "R010", impuesto=250), True)
    caso(32, "Confirmar asesoría tras corregir impuesto", lambda: gestor.procesar_reserva(
        "R010", impuesto=19))
    caso(33, "Rechazar segundo procesamiento", lambda: gestor.procesar_reserva("R010"), True)
    caso(34, "Deshabilitar servicio de equipos", lambda: gestor.cambiar_disponibilidad("S002", False))
    caso(35, "Rechazar servicio deshabilitado", lambda: gestor.procesar_reserva("R004"), True)
    caso(36, "Listar reservas sin interrumpir la app", lambda: len(gestor.listar_reservas()))

    resultados.append("")
    resultados.append(
        f"RESUMEN: {resumen['correcto']} operaciones correctas, "
        f"{resumen['error_controlado']} errores controlados y "
        f"{resumen['fallo_inesperado']} fallos inesperados."
    )
    if mostrar:
        print("\n" + resultados[-1])
    return resumen, resultados


if __name__ == "__main__":
    _, _ = ejecutar_simulacion()
