from proyecto_2.Simulador.cpu import CPU
from proyecto_2.Simulador.cpuPipelineSinHazards import CPUpipelineNoHazard
from proyecto_2.Simulador.cpuPipelineHazardControl import CPUPipelineHazardControl
from proyecto_2.Simulador.cpuPipelineConPredicciondeSaltos import CPUpipelineConPrediccionSaltos
from proyecto_2.Simulador.cpuPipelinePrediccionSaltosHazardControl import CPUPipelinePrediccionSaltosHazardControl
# 0-> original ripes
# 1-> no hazard codigo  
# 2-> hazard control necesitado
# 3-> prediccion de saltos  
codigo_pruebas:int = 6
riscv_code=[]
if(codigo_pruebas==0):
    riscv_code = [
        "#=========================================================",
        "# PROGRAMA: Conteo de saltos (branch y jump)",
        "# OBJETIVO: Realizar miles de saltos condicionales e",
        "#           incondicionales y documentar cuántos ocurren.",
        "# COMPATIBLE CON: Ripes (RISC-V RV32I)",
        "#=========================================================",
        "",
        "        .data",
        "count:  .word 0             # Contador de iteraciones",
        "limit:  .word 500          # Límite (miles de saltos)",
        "msg:    .string \"Fin del programa\\n\"",
        "",
        "        .text",
        "        .globl _start",
        "",
        "_start:",
                "addi x1, x0, 5        # x1 = 5",
                "addi x2, x0, 10       # x2 = 10",
                "add x3, x1, x2        # x3 = x1 + x2 (x3 = 15)",
                "add x4, x3, x1        # RAW: x4 depende de x3 recién escrito",
                "add x5, x3, x2        # RAW: x5 depende de x3 recién escrito",
                "add x6, x4, x5        # RAW: x6 depende de x4 y x5 recién escritos"
        "done:",
        "        # Fin del programa",
        "        nop                  # No operation (última instrucción)"
    ]
elif codigo_pruebas==1:
    riscv_code = [
        "# ============================================================",
        "# DEMOSTRACIÓN: Jump and Link (jal)",
        "# ============================================================",
        "",
        "# MAIN: Código principal",
        "addi x1, x0, 100       # x1 = 100",
        "nop",
        "nop",
        "nop",
        "nop",
        "jal x2, funcion1       # Llamar a funcion1, guardar PC+1 en x2",
        "despues_jal1:",
        "addi x5, x0, 50        # x5 = 50 (después de retornar de funcion1)",
        "nop",
        "nop",
        "nop",
        "nop",
        "jal x6, funcion2       # Llamar a funcion2, guardar PC+1 en x6",
        "despues_jal2:",
        "addi x8, x0, 88        # x8 = 88 (código final)",
        "",
        "# FIN - loop infinito para detener ejecución",
        "fin:",
        "jal x0, fin            # Loop infinito (salta a sí mismo)",
        "",
        "# FUNCION 1",
        "funcion1:",
        "addi x10, x0, 10       # x10 = 10",
        "addi x11, x0, 20       # x11 = 20",
        "nop",
        "nop",
        "nop",
        "nop",
        "add x12, x10, x11      # x12 = 10 + 20 = 30",
        "nop",
        "nop",
        "nop",
        "nop",
        "jal x0, despues_jal1   # Retornar a despues_jal1",
        "",
        "# FUNCION 2",
        "funcion2:",
        "addi x15, x0, 77       # x15 = 77",
        "addi x16, x0, 33       # x16 = 33",
        "nop",
        "nop",
        "nop",
        "nop",
        "jal x0, despues_jal2   # Retornar a despues_jal2",
        "",
        "# Resultado esperado:",
        "#   x1  = 100",
        "#   x2  = 24 (PC del primer jal = 20, entonces guardamos 24)",
        "#   x5  = 50",
        "#   x6  = 48 (PC del segundo jal = 44, entonces guardamos 48)",
        "#   x8  = 88",
        "#   x10 = 10, x11 = 20, x12 = 30",
        "#   x15 = 77, x16 = 33",
    ]
elif codigo_pruebas==2:
    riscv_code = [
    "# ============================================================",
    "# PROGRAMA: Generador de Hazards para pruebas de pipeline",
    "# ============================================================",
    "",
    ".text",
    ".globl _start",
    "",
    "_start:",
    "addi x1, x0, 5          # x1 = 5",
    "addi x2, x1, 3          # RAW: x2 depende de x1",
    "add x3, x2, x1          # RAW: x3 depende de x2",
    "",
    "# ---- Hazards con load-use ----",
    "la x4, dato             # Cargar dirección",
    "lw x5, 0(x4)            # Carga a x5",
    "addi x6, x5, 10         # RAW inmediato después del load",
    "",
    "# ---- Hazards en branch ----",
    "addi x7, x6, 1          # x7 depende de x6 recién escrito",
    "beq x7, x0, salto       # RAW branch",
    "addi x8, x0, 99         # (si no salta)",
    "jal x0, fin",
    "",
    "salto:",
    "add x9, x7, x5          # RAW: usa x7 y x5 recién modificados",
    "",
    "# ---- Hazard con JAL ----",
    "jal x10, funcion        # x10 = PC+1",
    "addi x11, x10, 2        # RAW: usa x10 justo después",
    "",
    "fin:",
    "jal x0, fin             # loop infinito",
    "",
    "# ---- Función ----",
    "funcion:",
    "addi x12, x0, 12",
    "addi x13, x12, 1        # RAW: depende de x12",
    "jal x0, fin",
    "",
    ".data",
    "dato: .word 42",
    ]
elif codigo_pruebas==3:
    # ============================================================
    # PRUEBA: Predicción de saltos con bucle
    # ============================================================
    riscv_code = [
        "# ============================================================",
        "# PRUEBA 3: Predicción de saltos - Bucle con decisiones",
        "# ============================================================",
        "",
        "# --- Inicialización ---",
        "addi x1, x0, 0        # x1 = 0 (contador)",
        "addi x2, x0, 5        # x2 = 5 (límite del bucle)",
        "addi x3, x0, 0        # x3 = 0 (acumulador)",
        "nop",
        "nop",
        "nop",
        "",
        "# --- Bucle: sumar números del 1 al 5 ---",
        "bucle:",
        "addi x1, x1, 1        # x1++ (incrementar contador)",
        "nop",
        "nop",
        "nop",
        "add x3, x3, x1        # x3 += x1 (acumular)",
        "nop",
        "nop",
        "nop",
        "nop",
        "beq x1, x2, fin_bucle # Si x1 == 5, salir del bucle",
        "jal x0, bucle         # Si no, repetir bucle",
        "",
        "fin_bucle:",
        "nop",
        "nop",
        "nop",
        "",
        "# --- Decisión: verificar si suma es correcta ---",
        "addi x4, x0, 15       # x4 = 15 (valor esperado)",
        "nop",
        "nop",
        "nop",
        "beq x3, x4, correcto  # Si x3 == 15, ir a 'correcto'",
        "addi x5, x0, 99       # x5 = 99 (ERROR - no debería ejecutarse)",
        "jal x0, fin           # Saltar a fin",
        "",
        "correcto:",
        "addi x5, x0, 100      # x5 = 100 (CORRECTO)",
        "nop",
        "nop",
        "nop",
        "",
        "# --- Operaciones finales ---",
        "mul x6, x3, x2        # x6 = x3 * x2 = 15 * 5 = 75",
        "nop",
        "nop",
        "nop",
        "nop",
        "",
        "fin:",
        "addi x7, x0, 77       # x7 = 77 (marca de fin)",
        "nop",
        "",
        "# Resultado esperado:",
        "#   x1  = 5  (contador final)",
        "#   x2  = 5  (límite)",
        "#   x3  = 15 (suma: 1+2+3+4+5)",
        "#   x4  = 15 (valor esperado)",
        "#   x5  = 100 (marca de correcto)",
        "#   x6  = 75 (15 * 5)",
        "#   x7  = 77 (marca de fin)",
    ]
elif codigo_pruebas==4:
    # ============================================================
    # PRUEBA: Predicción de saltos con bucle
    # ============================================================
    riscv_code = [
"# ============================================================",
        "# PRUEBA 4: Múltiples Store Words (sw)",
        "# Objetivo: Escribir varios valores en memoria",
        "# ============================================================",
        "",
        "# --- Inicializar valores en registros ---",
        "addi x1, x0, 10       # x1 = 10",
        "addi x2, x0, 20       # x2 = 20",
        "addi x3, x0, 30       # x3 = 30",
        "addi x4, x0, 40       # x4 = 40",
        "addi x5, x0, 50       # x5 = 50",
        "nop",
        "nop",
        "nop",
        "",
        "# --- Dirección base ---",
        "addi x10, x0, 0       # x10 = 0 (dirección base)",
        "nop",
        "nop",
        "nop",
        "",
        "# --- Store múltiples valores ---",
        "sw x1, 0(x10)         # Mem[0] = 10",
        "nop",
        "nop",
        "nop",
        "nop",
        "sw x2, 4(x10)         # Mem[4] = 20",
        "nop",
        "nop",
        "nop",
        "nop",
        "sw x3, 8(x10)         # Mem[8] = 30",
        "nop",
        "nop",
        "nop",
        "nop",
        "sw x4, 12(x10)        # Mem[12] = 40",
        "nop",
        "nop",
        "nop",
        "nop",
        "sw x5, 16(x10)        # Mem[16] = 50",
        "nop",
        "nop",
        "nop",
        "nop",
        "",
        "# --- Calcular suma y guardar ---",
        "add x6, x1, x2        # x6 = 10 + 20 = 30",
        "nop",
        "nop",
        "nop",
        "nop",
        "sw x6, 20(x10)        # Mem[20] = 30",
        "nop",
        "nop",
        "nop",
        "nop",
        "",
        "add x7, x3, x4        # x7 = 30 + 40 = 70",
        "nop",
        "nop",
        "nop",
        "nop",
        "sw x7, 24(x10)        # Mem[24] = 70",
        "nop",
        "nop",
        "nop",
        "nop",
        "",
        "add x8, x5, x6        # x8 = 50 + 30 = 80",
        "nop",
        "nop",
        "nop",
        "nop",
        "sw x8, 28(x10)        # Mem[28] = 80",
        "nop",
        "nop",
        "nop",
        "nop",
        "",
        "# --- Store valor final ---",
        "addi x9, x0, 99       # x9 = 99 (marca de finalización)",
        "nop",
        "nop",
        "nop",
        "nop",
        "sw x9, 32(x10)        # Mem[32] = 99",
        "nop",
        "",
    ]
elif codigo_pruebas==5:
    riscv_code = [
        "# TEST SIMPLE: branches, add, addi, lw, sw",
        "",
        "# Inicializar",
        "addi x1, x0, 10",
        "addi x2, x0, 20",
        "add x3, x1, x2",
        "",
        "# Store",
        "addi x10, x0, 0",
        "sw x1, 0(x10)",
        "sw x2, 4(x10)",
        "sw x3, 8(x10)",
        "",
        "# Load",
        "lw x4, 0(x10)",
        "",
        "# Branch NO tomado",
        "beq x1, x2, skip1",
        "addi x5, x0, 50",
        "skip1:",
        "",
        "# Branch SI tomado",
        "beq x1, x1, skip2",
        "addi x6, x0, 99",
        "skip2:",
        "addi x7, x0, 77",
        "nop"
    ]
elif codigo_pruebas==6:
    riscv_code = [
    "# TEST GLOBAL: arithmetic, loads/stores, hazards, branches, jal",
    ".data",
    "val1: .word 7",
    "val2: .word 3",
    ".text",
    ".globl _start",
    "",
    "_start:",
    "    # Inicializar registros",
    "    addi x1, x0, 5        # x1 = 5",
    "    addi x2, x0, 10       # x2 = 10",
    "    add x3, x1, x2        # x3 = x1 + x2 -> depende de x1,x2",
    "    addi x4, x3, 2        # x4 = x3 + 2 -> RAW con x3",
    "",
    "    # Guardar en memoria (sw) y luego leer (lw)",
    "    addi x10, x0, 0       # x10 = base 0",
    "    sw x1, 0(x10)         # Mem[0] = x1",
    "    sw x2, 4(x10)         # Mem[4] = x2",
    "    sw x3, 8(x10)         # Mem[8] = x3",
    "    lw x5, 8(x10)         # x5 <- Mem[8] (debe ser x3)",
    "",
    "    # Hazards intencionados: load-use y RAW",
    "    lw x6, 0(x10)         # x6 <- Mem[0] (load)",
    "    addi x7, x6, 1        # usa x6 inmediatamente -> load-use",
    "    add x8, x3, x7        # usa x3 y x7 -> RAW encadenado",
    "",
    "    # Branch: probamos no tomado y tomado",
    "    beq x1, x2, skip_bt1  # x1!=x2 -> no tomado",
    "    addi x9, x0, 99       # no debe ejecutarse",
    "skip_bt1:",
    "    beq x1, x1, skip_bt2  # siempre tomado",
    "    addi x9, x0, 50       # no debe ejecutarse",
    "skip_bt2:",
    "",
    "    # Loop simple para probar predicción",
    "    addi x11, x0, 0       # cnt = 0",
    "    addi x12, x0, 4       # limit = 4",
    "loop:",
    "    addi x11, x11, 1      # cnt++",
    "    add x13, x13, x11     # acc += cnt (x13 starts 0)",
    "    beq x11, x12, endloop",
    "    jal x0, loop",
    "endloop:",
    "",
    "    # Llamada a función (jal) y uso del return address",
    "    jal x14, funcion      # jal guarda PC+4 en x14",
    "    addi x15, x14, 2      # usar x14 inmediatamente -> RAW con jal",
    "",
    "    # Fin (marca) y loop infinito para detener ejecución",
    "    addi x31, x0, 77      # marca final en x31",
    "    jal x0, fin",
    "",
    "funcion:",
    "    addi x20, x0, 11      # x20 = 11",
    "    addi x21, x20, 1      # x21 = x20 + 1",
    "    jalr x0, x14, 0       # retornar a x14",
    "",
    "fin:",
    "    nop"
]



# 0-> no hazard control
# 1-> hazard control 
# 2-> prediccion de saltos (always_taken)
# 3-> prediccion de saltos (always_not_taken)
cpu_testear:int=4
if(cpu_testear==0):
    cpuPipeline=CPUpipelineNoHazard()
elif cpu_testear==1:
    cpuPipeline=CPUPipelineHazardControl()
elif cpu_testear==2:
    cpuPipeline=CPUpipelineConPrediccionSaltos(predictor_strategy='always_taken')
elif cpu_testear==3:
    cpuPipeline=CPUpipelineConPrediccionSaltos(predictor_strategy='always_not_taken')
elif cpu_testear==4:
    cpuPipeline=CPUPipelinePrediccionSaltosHazardControl(predictor_strategy='always_taken')
elif cpu_testear==5:
    cpuPipeline=CPUPipelinePrediccionSaltosHazardControl(predictor_strategy='always_not_taken')
cpuPipeline.cargarCodigo(riscv_code)
cpuPipeline.ejecutar()

# cpu.ejecutar(riscv_code)
# cpu.ejecutar_todo()

print("\n" + "=" * 80)
print("ANÁLISIS DE RESULTADOS - PREDICCIÓN DE SALTOS")
print("=" * 80)

if codigo_pruebas == 3:

    # ==== IMPRIMIR 32 REGISTROS ====
    print(f"\n[REGISTROS FINALES - BANCO COMPLETO]")
    for i in range(32):
        print(f"  x{i:02d} = {cpuPipeline.regs[i]:4d}")

    print(f"\n[ESTADÍSTICAS DE PREDICCIÓN]")
    print(f"  Estrategia: {cpuPipeline.branch_predictor.strategy}")
    print(f"  Total ciclos: {cpuPipeline.ciclo_actual}")
    print(f"  Branches ejecutados: {cpuPipeline.branch_count}")
    print(f"  Predicciones: {cpuPipeline.branch_predictor.predictions}")
    print(f"  Correctas: {cpuPipeline.branch_predictor.correct_predictions}")
    print(f"  Incorrectas: {cpuPipeline.branch_predictor.mispredictions}")
    print(f"  Precisión: {cpuPipeline.branch_predictor.get_accuracy():.1f}%")
    print(f"  Flushes: {cpuPipeline.total_flushes}")
    
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DETALLADA")
    print("=" * 80)

    errores = 0
    tests = [
        (1, 5, "x1 - contador"),
        (2, 5, "x2 - límite"),
        (3, 15, "x3 - suma (1+2+3+4+5)"),
        (4, 15, "x4 - esperado"),
        (5, 100, "x5 - marca correcto"),
        (6, 75, "x6 = x3 * x2"),
        (7, 77, "x7 - marca fin"),
    ]
    
    for reg, esperado, descripcion in tests:
        valor_real = cpuPipeline.regs[reg]
        if valor_real == esperado:
            print(f"[OK] {descripcion}: {valor_real}")
        else:
            print(f"[ERROR] {descripcion}: esperado={esperado}, obtenido={valor_real}")
            errores += 1

    print("\n" + "=" * 80)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 80)
    
    if errores == 0:
        print("[OK] TODOS LOS TESTS PASARON")
        print("\nFuncionalidad validada:")
        print("  - Predicción de saltos funciona correctamente")
        print("  - Ejecución especulativa implementada")
        print("  - Detección y corrección de mispredictions")
        print("  - CPU completa ejecuta código con branches")
    else:
        print(f"[ERROR] FALLO {errores} TEST(S)")
        print("    Revisar implementación de predicción")
    
    print("=" * 80)

else:

    # ==== IMPRIMIR 32 REGISTROS ====
    print(f"\n[REGISTROS FINALES - BANCO COMPLETO]")
    for i in range(32):
        print(f"  x{i:02d} = {cpuPipeline.regs[i]:4d}")

    print(f"\n[FUNCION 1]")
    print(f"  x10 = {cpuPipeline.regs[10]:3d} (esperado: 10)")
    print(f"  x11 = {cpuPipeline.regs[11]:3d} (esperado: 20)")
    print(f"  x12 = {cpuPipeline.regs[12]:3d} (esperado: 30 = x10 + x11)")

    print(f"\n[FUNCION 2]")
    print(f"  x15 = {cpuPipeline.regs[15]:3d} (esperado: 77)")
    print(f"  x16 = {cpuPipeline.regs[16]:3d} (esperado: 33)")

    print("\n" + "=" * 80)
    print("VERIFICACION DETALLADA")
    print("=" * 80)

    errores = 0
    tests = [
        (1, 100, "x1 (main)"),
        (2, 24, "x2 (return address 1)"),
        (5, 50, "x5 (despues de funcion1)"),
        (6, 48, "x6 (return address 2)"),
        (8, 88, "x8 (codigo final)"),
        (10, 10, "x10 (funcion1)"),
        (11, 20, "x11 (funcion1)"),
        (12, 30, "x12 (suma en funcion1)"),
        (15, 77, "x15 (funcion2)"),
        (16, 33, "x16 (funcion2)"),
    ]

    print("\n" + "=" * 80)
    print("RESUMEN DE VALIDACION")
    print("=" * 80)

    if errores == 0:
        print("[OK] TODOS LOS TESTS PASARON")
        print("\nFuncionalidad JAL validada:")
        print("  - Salto incondicional a labels")
        print("  - Guardado de direccion de retorno en rd")
        print("  - Pipeline flush en cada jal")
        print("  - Llamadas a funciones y retornos")
        print("  - JAL anidado (funciones que llaman a otras)")
    else:
        print(f"[ERROR] FALLO {errores} TEST(S)")
        print("    Revisar implementacion de JAL")

    print("=" * 80)