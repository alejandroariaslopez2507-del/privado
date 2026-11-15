# Software FJ - Fase 4 (UNAD, Programación 213023)

Proyecto en **Python 3.10 o superior** para gestionar clientes, tres tipos de servicios y reservas. Se trabaja con **objetos y diccionarios en memoria**, sin bases de datos. El único archivo generado por la aplicación es `software_fj.log`, para errores y eventos.

## Archivos

| Archivo | Función |
|---|---|
| `modelo.py` | Excepciones propias, clase abstracta `Entidad`, `Cliente`, clase abstracta `Servicio`, tres subclases y `Reserva`. |
| `gestor.py` | Controlador central, validación de duplicados, inventario y estados. |
| `main.py` | Menú interactivo de consola para usar el sistema. |
| `simulacion.py` | 36 operaciones de prueba, con éxitos y rechazos controlados. |
| `test_sistema.py` | Pruebas unitarias de la lógica del negocio. |
| `resultados_simulacion.txt` | Evidencia textual generada al ejecutar la simulación. |
| `software_fj.log` | Archivo de eventos/errores generado durante la ejecución. |

## Requisitos

- Python 3.10 o superior.
- Solo biblioteca estándar. No hace falta instalar paquetes.
- No requiere base de datos.

## Cómo ejecutar en Windows

1. Descomprime el ZIP del proyecto en una carpeta.
2. Abre la carpeta con Visual Studio Code o abre una consola dentro de ella.
3. Ejecuta:

```powershell
python main.py
```

4. Usa la opción **8** si quieres ver de inmediato la simulación de 36 operaciones.
5. También puedes ejecutar la simulación directamente:

```powershell
python simulacion.py
```

6. Para comprobar los casos mediante pruebas unitarias:

```powershell
python -m unittest -v test_sistema
```

> Si `python` no está reconocido en Windows, intenta `py main.py`.

## Arquitectura y requisitos

- **Abstracción:** `Entidad` y `Servicio` usan `ABC` y `abstractmethod`.
- **Herencia y polimorfismo:** `ServicioSala`, `ServicioEquipo` y `ServicioAsesoria` implementan los cálculos, validaciones y descripciones de formas distintas.
- **Encapsulación:** atributos internos y `@property`, validaciones con `@setter` para los clientes, copia defensiva de opciones.
- **Sobrecarga:** `calcular_total` ofrece firmas sobrecargadas mediante `typing.overload` y una implementación con parámetros opcionales. En Python la sobrecarga de firma se expresa mediante anotaciones, mientras que la selección en ejecución se hace con valores opcionales.
- **Errores:** excepciones personalizadas; uso de `try/except`, `try/except/else/finally` y `raise ... from ...` para encadenamiento.
- **Logs:** `software_fj.log` registra operaciones y errores; no guarda listas de clientes ni reservas.
- **Reservas:** pueden estar **Pendiente**, **Confirmada** o **Cancelada**. Las reservas canceladas liberan capacidad.

## Supuestos de diseño 

- La moneda demostrativa son **pesos colombianos (COP)**; las tarifas son valores de ejemplo ajustables.
- Una reserva ocupa recursos de forma concurrente mientras permanezca **Confirmada**. No se implementan fechas ni calendario porque no los exige el Anexo 3; el sistema simula la disponibilidad con cupos.
- Una sala acepta una reserva confirmada a la vez, limitada por el número de personas.
- Cada unidad de equipo ocupa una unidad de stock.
- Cada especialista atiende una asesoría simultánea y la duración máxima de cada sesión es de cuatro horas.
- El proyector añade $15 000 COP por hora a una sala, y la asesoría presencial aumenta la tarifa base un 20 %. Estos importes son reglas de ejemplo, no reglas establecidas por la UNAD.
- `calcular_total` aplica primero el descuento y después el impuesto; ambos porcentajes pueden ir de 0 a 100.
- Los objetos solo duran mientras se ejecuta la aplicación; **no hay persistencia de datos del negocio**, por indicación de la tarea.

## Repositorio del proyecto

Repositorio del grupo: **[Software FJ – Fase 4](https://github.com/alejandroariaslopez2507-del/privado)** (privado).

Los integrantes pueden clonar el repositorio usando:

```bash
git clone https://github.com/alejandroariaslopez2507-del/privado.git
```

Los cinco estudiantes deben aportar su trabajo a través de sus propias contribuciones (commits); los resultados automatizados incluidos son evidencias de la solución base y no sustituyen la participación colaborativa. Compartir el enlace del repositorio en el foro de la actividad y añadirlo al informe PDF.

## Ejemplos de uso

- Registrar cliente `C001`, correo `ana@ejemplo.com`, teléfono `3001234567`.
- Registrar sala `S001` con tarifa `50000` y capacidad `8`.
- Reservar dos horas para cuatro personas, con proyector e impuesto del 19 %.
- Consultar el estado y cancelar la reserva para liberar la capacidad.

## Licencia académica

Ejemplo didáctico desarrollado para el componente práctico de Programación - UNAD. Documentación y resultados deben ser revisados y explicados por los integrantes del equipo.
