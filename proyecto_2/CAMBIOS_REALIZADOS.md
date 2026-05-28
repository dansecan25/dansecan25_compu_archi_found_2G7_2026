# 📝 Resumen de Cambios Realizados - Integración Frontend-Backend

## 🎯 Objetivo
Conectar el frontend (visualización) con el backend (simulador) para que las simulaciones se ejecuten automáticamente y los datos se visualicen correctamente.

---

## 🔧 Archivos Modificados

### 1. **Backend - Simulador (4 archivos)**

#### `proyecto_2/Simulador/cpuPipelineSinHazards.py`
**Cambios:**
- ✅ Corregida ruta de generación de log: ahora genera en `proyecto_2/Front/log.txt`
- ✅ Corregida ruta de archivo de memoria: ahora genera en `proyecto_2/Front/memoria_salida.txt`
- ✅ Usa `Path(__file__).parent.parent / "Front"` para rutas relativas correctas

**Líneas modificadas:** 1-33, 286-291

#### `proyecto_2/Simulador/cpuPipelineHazardControl.py`
**Cambios:**
- ✅ Corregida ruta de generación de log: ahora genera en `proyecto_2/Front/log_hazard_control.txt`
- ✅ Corregida ruta de archivo de memoria: ahora genera en `proyecto_2/Front/memoria_salida_hazard_control.txt`
- ✅ Eliminada variable `pathGen` obsoleta
- ✅ Usa `Path(__file__).parent.parent / "Front"` para rutas relativas correctas

**Líneas modificadas:** 1-33, 385-390

#### `proyecto_2/Simulador/cpuPipelineConPredicciondeSaltos.py`
**Cambios:**
- ✅ Corregida ruta de generación de log: ahora genera en `proyecto_2/Front/log_prediccion.txt`
- ✅ Corregida ruta de archivo de memoria: ahora genera en `proyecto_2/Front/memoria_salida_prediccion.txt`
- ✅ Eliminada variable `pathGen` obsoleta
- ✅ Usa `Path(__file__).parent.parent / "Front"` para rutas relativas correctas

**Líneas modificadas:** 1-100, 432-437

#### `proyecto_2/Simulador/cpuPipelinePrediccionSaltosHazardControl.py`
**Cambios:**
- ✅ Corregida ruta de generación de log: ahora genera en `proyecto_2/Front/log_prediccion_hazard_control.txt`
- ✅ Corregida ruta de archivo de memoria: ahora genera en `proyecto_2/Front/memoria_salida_prediccion_hazard_control.txt`
- ✅ Eliminada variable `pathGen` obsoleta
- ✅ Usa `Path(__file__).parent.parent / "Front"` para rutas relativas correctas

**Líneas modificadas:** 1-50, 564-569

---

### 2. **Frontend - Interfaz Gráfica (2 archivos)**

#### `proyecto_2/Front/mainMenu.py`
**Cambios:**
- ✅ Importado `SimulatorRunner` para ejecutar simulaciones
- ✅ Eliminados imports comentados de CPUs
- ✅ Ajustado tamaño de ventana principal: ahora usa 80% de pantalla (máx 1200x750)
- ✅ Ventana principal centrada correctamente
- ✅ Método `get_txt()` completamente reescrito:
  - Ejecuta simulaciones automáticamente al presionar "Compile"
  - Muestra mensajes de progreso y éxito/error
  - Valida que haya código antes de ejecutar
  - Calcula tamaños de ventana dinámicamente (70% de pantalla)
  - Abre ventanas de procesador con posiciones correctas

**Líneas modificadas:** 1-14, 25-42, 98-165

#### `proyecto_2/Front/processor_window.py`
**Cambios:**
- ✅ Parámetros del constructor cambiados: ahora recibe `window_width` y `window_height` en lugar de `lft_pos` y `top_pos`
- ✅ Ventanas ahora son redimensionables (`resizable=True`)
- ✅ Tamaño ajustado dinámicamente (máx 70% de pantalla, límite 1100x700)
- ✅ Posicionamiento corregido:
  - CPU 0 y 1 (primera columna) → lado izquierdo (offset 50px)
  - CPU 2 y 3 (segunda columna) → lado derecho (offset desde borde derecho)
- ✅ Posición vertical centrada pero siempre visible (mínimo 50px desde arriba)
- ✅ Frame del procesador ahora usa `pack` con `fill='both', expand=True` para mejor escalado
- ✅ Mensaje de error mejorado si falla la carga del log

**Líneas modificadas:** 13-48

---

## 📄 Archivos Nuevos Creados

### 1. **`proyecto_2/Front/simulator_runner.py`** (165 líneas)
**Propósito:** Módulo de integración entre frontend y backend

**Características:**
- ✅ Clase `SimulatorRunner` con métodos estáticos
- ✅ Mapeo de índices a clases de CPU (0-3)
- ✅ Mapeo de nombres de archivos de log y memoria
- ✅ Método `run_simulation()`: ejecuta una simulación individual
- ✅ Método `run_dual_simulation()`: ejecuta par de simulaciones según selección
- ✅ Manejo de errores con try-except y mensajes informativos
- ✅ Soporte para estrategias de predicción de saltos
- ✅ Código de prueba incluido en `if __name__ == "__main__"`

**Funcionalidad:**
```python
# Ejecutar par de simulaciones
success1, success2 = SimulatorRunner.run_dual_simulation(cpu_pair_index, code)
```

### 2. **`proyecto_2/Front/test_code_sample.txt`** (58 líneas)
**Propósito:** Código de prueba completo para validar el simulador

**Incluye:**
- ✅ Operaciones aritméticas (add, addi)
- ✅ Operaciones con memoria (lw, sw)
- ✅ Branches tomados y no tomados (beq)
- ✅ Loops con contadores
- ✅ Llamadas a funciones (jal, jalr)
- ✅ Comentarios explicativos

### 3. **`proyecto_2/README_INTEGRACION.md`** (329 líneas)
**Propósito:** Documentación completa del proyecto integrado

**Contenido:**
- ✅ Descripción del proyecto y configuraciones de CPU
- ✅ Explicación detallada de todos los cambios realizados
- ✅ Guía paso a paso de uso del simulador
- ✅ Interpretación de resultados y visualización
- ✅ Solución de problemas comunes
- ✅ Estructura de archivos generados
- ✅ Formato de archivos de log
- ✅ Lista de instrucciones RISC-V soportadas
- ✅ Ejemplo completo de uso
- ✅ Checklist de verificación

### 4. **`proyecto_2/CAMBIOS_REALIZADOS.md`** (Este archivo)
**Propósito:** Resumen técnico de todos los cambios

---

## 🔄 Flujo de Datos Corregido

### Antes (❌ No funcionaba):
```
Usuario escribe código → Presiona Compile → Se abren ventanas vacías
                                          → No hay simulación
                                          → No hay archivos de log
                                          → Frontend no encuentra datos
```

### Después (✅ Funciona correctamente):
```
Usuario escribe código
    ↓
Presiona "Compile"
    ↓
SimulatorRunner.run_dual_simulation()
    ↓
├─→ Ejecuta CPU 1 (según selección)
│   ├─→ Genera log en Front/log_X.txt
│   └─→ Genera memoria en Front/memoria_salida_X.txt
│
└─→ Ejecuta CPU 2 (según selección)
    ├─→ Genera log en Front/log_Y.txt
    └─→ Genera memoria en Front/memoria_salida_Y.txt
    ↓
Se abren 2 ventanas ProcessorWindow
    ↓
├─→ Ventana 1 lee Front/log_X.txt
│   └─→ Visualiza pipeline de CPU 1
│
└─→ Ventana 2 lee Front/log_Y.txt
    └─→ Visualiza pipeline de CPU 2
    ↓
Usuario navega por ciclos y ve resultados
```

---

## 🎨 Mejoras de UI

### Ventana Principal
- **Antes:** 1500x900 (fijo, muy grande)
- **Después:** 80% de pantalla, máx 1200x750 (adaptativo)

### Ventanas de Procesador
- **Antes:** 1250x750 y posiciones incorrectas (fuera de pantalla)
- **Después:** 70% de pantalla, máx 1100x700, lado a lado, siempre visibles

### Redimensionamiento
- **Antes:** No redimensionable
- **Después:** Redimensionable con scroll automático

---

## 📊 Configuraciones de CPU Soportadas

### Par 1: CPU_NH / CPU_HC
- **CPU 0:** Sin Hazards → `log.txt`
- **CPU 2:** Con Hazard Control → `log_hazard_control.txt`

### Par 2: CPU_PS / CPU_SHC
- **CPU 1:** Con Predicción de Saltos → `log_prediccion.txt`
- **CPU 3:** Con Predicción + Hazard Control → `log_prediccion_hazard_control.txt`

---

## ✅ Problemas Resueltos

1. ✅ **Desconexión Frontend-Backend:** Ahora el frontend ejecuta el simulador automáticamente
2. ✅ **Rutas de archivos incorrectas:** Todos los logs y archivos de memoria se generan en `Front/`
3. ✅ **Ventanas fuera de pantalla:** Posicionamiento corregido, siempre visibles
4. ✅ **Tamaños de ventana fijos:** Ahora se adaptan a la resolución de pantalla
5. ✅ **Falta de feedback:** Mensajes de progreso y error implementados
6. ✅ **Archivos de memoria faltantes:** Todas las CPUs generan archivos de memoria
7. ✅ **Documentación inexistente:** README completo creado

---

## 🚀 Cómo Probar los Cambios

### 1. Ejecutar el simulador:
```bash
cd proyecto_2/Front
python main.py
```

### 2. Cargar código de prueba:
- Copiar contenido de `test_code_sample.txt`
- Pegar en el editor
- Seleccionar configuración de CPU
- Presionar "Compile"

### 3. Verificar resultados:
- ✅ Se ejecutan 2 simulaciones (ver consola)
- ✅ Se generan archivos de log en `Front/`
- ✅ Se abren 2 ventanas de visualización
- ✅ Ventanas visibles y bien posicionadas
- ✅ Pipeline se visualiza correctamente
- ✅ Registros se actualizan
- ✅ Navegación por ciclos funciona

### 4. Verificar archivos generados:
```bash
ls proyecto_2/Front/*.txt
```
Deberías ver:
- `log.txt`
- `log_hazard_control.txt`
- `log_prediccion.txt`
- `log_prediccion_hazard_control.txt`
- `memoria_salida.txt`
- `memoria_salida_hazard_control.txt`
- `memoria_salida_prediccion.txt`
- `memoria_salida_prediccion_hazard_control.txt`

---

## 📈 Estadísticas de Cambios

- **Archivos modificados:** 6
- **Archivos creados:** 4
- **Líneas de código modificadas:** ~200
- **Líneas de código nuevas:** ~550
- **Bugs corregidos:** 7
- **Mejoras de UI:** 4

---

## 🎓 Conclusión

El proyecto ahora está completamente integrado y funcional:

✅ Frontend y Backend conectados
✅ Simulaciones automáticas
✅ Visualización correcta de datos
✅ UI responsive y adaptativa
✅ Documentación completa
✅ Código de prueba incluido
✅ Manejo de errores robusto

**El simulador está listo para ser usado y demostrado.**

---

**Fecha de integración:** Mayo 2026  
**Versión:** 1.0  
**Estado:** ✅ Completado y probado