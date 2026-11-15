"""Pruebas automáticas: python -m unittest -v test_sistema"""

import unittest
from decimal import Decimal

from gestor import GestorSoftwareFJ
from modelo import (
    Cliente, ErrorCalculo, ErrorDisponibilidad, ErrorDuplicado, ErrorEstadoReserva,
    ErrorNoEncontrado, ErrorValidacion, ServicioAsesoria, ServicioEquipo, ServicioSala,
)


class PruebasSoftwareFJ(unittest.TestCase):
    def setUp(self):
        self.gestor = GestorSoftwareFJ()
        self.gestor.registrar_cliente(Cliente("C001", "Ana Torres", "ana@ejemplo.com", "3001234567"))
        self.gestor.registrar_cliente(Cliente("C002", "Luis Pérez", "luis@ejemplo.com", "3111234567"))
        self.gestor.registrar_servicio(ServicioSala("S001", "Sala central", 50000, 10))
        self.gestor.registrar_servicio(ServicioEquipo("S002", "Computadores", 20000, 3))
        self.gestor.registrar_servicio(ServicioAsesoria("S003", "Soporte técnico", 80000, 2))

    def test_registro_clientes(self):
        self.assertEqual(len(self.gestor.listar_clientes()), 2)

    def test_correo_invalido(self):
        with self.assertRaises(ErrorValidacion):
            Cliente("C003", "Persona X", "correo_malo", "3001234567")

    def test_telefono_invalido(self):
        with self.assertRaises(ErrorValidacion):
            Cliente("C003", "Persona X", "x@ejemplo.com", "abc")

    def test_id_cliente_duplicado(self):
        with self.assertRaises(ErrorDuplicado):
            self.gestor.registrar_cliente(Cliente("C001", "Persona X", "x@ejemplo.com", "3001234567"))

    def test_correo_duplicado(self):
        with self.assertRaises(ErrorDuplicado):
            self.gestor.registrar_cliente(Cliente("C003", "Persona X", "ana@ejemplo.com", "3001234567"))

    def test_identificador_servicio_duplicado(self):
        with self.assertRaises(ErrorDuplicado):
            self.gestor.registrar_servicio(ServicioEquipo("S002", "Repetido", 10000, 1))

    def test_no_encontrado_encadenado(self):
        with self.assertRaises(ErrorNoEncontrado) as capturado:
            self.gestor.obtener_cliente("C999")
        self.assertIsInstance(capturado.exception.__cause__, KeyError)

    def test_sala_con_descuento_e_impuesto(self):
        servicio = self.gestor.obtener_servicio("S001")
        total = servicio.calcular_total(2, personas=3, proyector=True, impuesto=19, descuento=10)
        self.assertEqual(total, Decimal("139230.00"))

    def test_sala_sin_recargo(self):
        self.assertEqual(self.gestor.obtener_servicio("S001").calcular_total(2), Decimal("100000.00"))

    def test_equipo_con_unidades(self):
        self.assertEqual(self.gestor.obtener_servicio("S002").calcular_total(3, unidades=2), Decimal("120000.00"))

    def test_asesoria_presencial(self):
        self.assertEqual(self.gestor.obtener_servicio("S003").calcular_total(2, modalidad="presencial"), Decimal("192000.00"))

    def test_servicio_incorrecto(self):
        with self.assertRaises(ErrorValidacion):
            ServicioSala("S004", "Sala nueva", -50, 8)

    def test_opciones_desconocidas(self):
        with self.assertRaises(ErrorValidacion):
            self.gestor.obtener_servicio("S001").calcular_total(1, opcion_inesperada=True)

    def test_reserva_estado_y_cancelacion(self):
        reserva = self.gestor.crear_reserva("R001", "C001", "S001", 2, personas=4)
        self.assertEqual(reserva.estado, "Pendiente")
        self.gestor.procesar_reserva("R001")
        self.assertEqual(reserva.estado, "Confirmada")
        self.gestor.cancelar_reserva("R001")
        self.assertEqual(reserva.estado, "Cancelada")
        with self.assertRaises(ErrorEstadoReserva):
            self.gestor.cancelar_reserva("R001")

    def test_sala_ocupada_y_liberada(self):
        self.gestor.crear_reserva("R001", "C001", "S001", 1)
        self.gestor.crear_reserva("R002", "C002", "S001", 1)
        self.gestor.procesar_reserva("R001")
        with self.assertRaises(ErrorDisponibilidad):
            self.gestor.procesar_reserva("R002")
        self.gestor.cancelar_reserva("R001")
        self.assertEqual(self.gestor.procesar_reserva("R002"), Decimal("50000.00"))

    def test_stock_de_equipos(self):
        self.gestor.crear_reserva("R001", "C001", "S002", 2, unidades=3)
        self.gestor.crear_reserva("R002", "C002", "S002", 1, unidades=1)
        self.gestor.procesar_reserva("R001")
        with self.assertRaises(ErrorDisponibilidad):
            self.gestor.procesar_reserva("R002")

    def test_servicio_inactivo(self):
        self.gestor.cambiar_disponibilidad("S003", False)
        self.gestor.crear_reserva("R001", "C001", "S003", 1)
        with self.assertRaises(ErrorDisponibilidad):
            self.gestor.procesar_reserva("R001")

    def test_duracion_cero(self):
        with self.assertRaises(ErrorValidacion):
            self.gestor.crear_reserva("R001", "C001", "S003", 0)

    def test_duracion_asesoria_mayor_cuatro(self):
        self.gestor.crear_reserva("R001", "C001", "S003", 5)
        with self.assertRaises(ErrorValidacion):
            self.gestor.procesar_reserva("R001")

    def test_descuento_invalido_reserva_pendiente(self):
        reserva = self.gestor.crear_reserva("R001", "C001", "S003", 1)
        with self.assertRaises(ErrorCalculo):
            self.gestor.procesar_reserva("R001", descuento=200)
        self.assertEqual(reserva.estado, "Pendiente")

    def test_no_confirmar_dos_veces(self):
        self.gestor.crear_reserva("R001", "C001", "S003", 1)
        self.gestor.procesar_reserva("R001")
        with self.assertRaises(ErrorValidacion):
            self.gestor.procesar_reserva("R001")

    def test_encapsulacion_de_opciones(self):
        reserva = self.gestor.crear_reserva("R001", "C001", "S002", 1, unidades=2)
        copia = reserva.opciones
        copia["unidades"] = 1000
        self.assertEqual(reserva.opciones["unidades"], 2)

    def test_booleanos_no_aceptados_en_duracion(self):
        with self.assertRaises(ErrorValidacion):
            self.gestor.crear_reserva("R001", "C001", "S003", True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
