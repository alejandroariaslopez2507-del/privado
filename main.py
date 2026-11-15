"""Menú principal de Software FJ. Ejecutar: python main.py"""

from decimal import Decimal, InvalidOperation
import logging

from gestor import GestorSoftwareFJ, configurar_logger
from modelo import (
    Cliente, ErrorSistema, ErrorValidacion, ServicioAsesoria, ServicioEquipo,
    ServicioSala,
)
from simulacion import ejecutar_simulacion


def pedir_entero(etiqueta: str) -> int:
    try:
        return int(input(etiqueta).strip())
    except ValueError as error:
        raise ErrorValidacion("Ingrese un número entero válido.") from error


def pedir_decimal(etiqueta: str) -> Decimal:
    try:
        numero = Decimal(input(etiqueta).strip())
    except (InvalidOperation, ValueError) as error:
        raise ErrorValidacion("Ingrese un número decimal válido.") from error
    return numero


def mostrar_registros(registros) -> None:
    if not registros:
        print("No hay registros todavía.")
    for elemento in registros:
        print("  -", elemento.describir())


def nuevo_servicio(gestor: GestorSoftwareFJ) -> None:
    print("\n1. Sala   2. Alquiler de equipos   3. Asesoría")
    tipo = input("Tipo de servicio: ").strip()
    identificador = input("Código del servicio: ").strip()
    nombre = input("Nombre del servicio: ").strip()
    tarifa = pedir_decimal("Tarifa por hora: ")
    if tipo == "1":
        servicio = ServicioSala(identificador, nombre, tarifa, pedir_entero("Capacidad de personas: "))
    elif tipo == "2":
        servicio = ServicioEquipo(identificador, nombre, tarifa, pedir_entero("Cantidad de equipos: "))
    elif tipo == "3":
        servicio = ServicioAsesoria(identificador, nombre, tarifa, pedir_entero("Número de especialistas: "))
    else:
        raise ErrorValidacion("Seleccione un tipo de servicio válido.")
    gestor.registrar_servicio(servicio)
    print("Servicio registrado correctamente.")


def nueva_reserva(gestor: GestorSoftwareFJ) -> None:
    identificador = input("Código de reserva: ").strip()
    cliente = input("Código del cliente: ").strip()
    codigo_servicio = input("Código del servicio: ").strip()
    duracion = pedir_entero("Duración (horas): ")
    servicio = gestor.obtener_servicio(codigo_servicio)
    opciones = {}
    if isinstance(servicio, ServicioSala):
        opciones["personas"] = pedir_entero("Número de personas: ")
        respuesta = input("¿Requiere proyector? (s/n): ").strip().lower()
        if respuesta not in ("s", "n"):
            raise ErrorValidacion("Para el proyector, responda 's' o 'n'.")
        opciones["proyector"] = respuesta == "s"
    elif isinstance(servicio, ServicioEquipo):
        opciones["unidades"] = pedir_entero("Número de equipos: ")
    elif isinstance(servicio, ServicioAsesoria):
        opciones["modalidad"] = input("Modalidad (virtual/presencial): ").strip().lower()
    reserva = gestor.crear_reserva(identificador, cliente, codigo_servicio, duracion, **opciones)
    print("Reserva creada en estado Pendiente:", reserva.describir())
    impuesto = pedir_decimal("Impuesto (%; 0 si no aplica): ")
    descuento = pedir_decimal("Descuento (%; 0 si no aplica): ")
    total = gestor.procesar_reserva(identificador, impuesto=impuesto, descuento=descuento)
    print(f"Reserva confirmada. Total: ${total}")


def menu() -> None:
    gestor = GestorSoftwareFJ()
    logger = configurar_logger()
    while True:
        print("\n" + "=" * 52)
        print("SOFTWARE FJ | SISTEMA DE CLIENTES, SERVICIOS Y RESERVAS")
        print("1. Registrar cliente        2. Consultar clientes")
        print("3. Registrar servicio       4. Consultar servicios")
        print("5. Crear y procesar reserva 6. Consultar reservas")
        print("7. Cancelar reserva         8. Simulación automática")
        print("9. Reintentar reserva       10. Disponibilidad del servicio")
        print("0. Salir")
        try:
            opcion = input("Seleccione una opción: ").strip()
        except (EOFError, KeyboardInterrupt):
            logger.warning("La aplicación se cerró por interrupción de entrada")
            print("\nEntrada finalizada. Hasta pronto.")
            break
        if opcion == "0":
            print("Aplicación finalizada. Hasta pronto.")
            break
        try:
            if opcion == "1":
                cliente = Cliente(
                    input("Código: ").strip(), input("Nombre: ").strip(),
                    input("Correo: ").strip(), input("Teléfono: ").strip()
                )
                gestor.registrar_cliente(cliente)
                print("Cliente registrado correctamente.")
            elif opcion == "2":
                mostrar_registros(gestor.listar_clientes())
            elif opcion == "3":
                nuevo_servicio(gestor)
            elif opcion == "4":
                mostrar_registros(gestor.listar_servicios())
            elif opcion == "5":
                nueva_reserva(gestor)
            elif opcion == "6":
                mostrar_registros(gestor.listar_reservas())
            elif opcion == "7":
                reserva = gestor.cancelar_reserva(input("Código de reserva: ").strip())
                print("Reserva cancelada:", reserva.describir())
            elif opcion == "8":
                ejecutar_simulacion()
            elif opcion == "9":
                codigo = input("Código de la reserva pendiente: ").strip()
                total = gestor.procesar_reserva(
                    codigo, pedir_decimal("Impuesto (%): "), pedir_decimal("Descuento (%): ")
                )
                print("Reserva confirmada; total: $", total)
            elif opcion == "10":
                codigo = input("Código del servicio: ").strip()
                disponible = input("¿Activar? (s/n): ").strip().lower()
                if disponible not in ("s", "n"):
                    raise ErrorValidacion("Responda 's' o 'n'.")
                gestor.cambiar_disponibilidad(codigo, disponible == "s")
                print("Disponibilidad actualizada.")
            else:
                print("Opción no válida. Inténtelo nuevamente.")
        except ErrorSistema as error:
            logger.error("Error controlado en menú: %s", error)
            print("[ERROR CONTROLADO]", error)
        except (KeyboardInterrupt, EOFError):
            print("\nEntrada interrumpida. Regresando al menú o cerrando la consola.")
            logger.warning("Entrada interrumpida en la operación %s", opcion)
            break
        except Exception:
            # Protección adicional ante fallos no anticipados, sin perder el menú.
            logger.exception("Error inesperado en menú, opción %s", opcion)
            print("[ERROR] Ocurrió un error inesperado. Revise software_fj.log.")


if __name__ == "__main__":
    menu()
