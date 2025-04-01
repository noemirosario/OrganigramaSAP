import pandas as pd

def generar_organigrama(data, Posición_inicial, estatus_filtro='todos',
                        nivel=0, contador=0, empleados_lista=None,
                        max_niveles=None):
    """
    :param data: DataFrame con las columnas mínimas: [Posición, JEFE INMEDIATO, Número de personal, Estatus].
    :param Posición_inicial: Posición raíz para comenzar a trazar el organigrama.
    :param estatus_filtro: "si" para incluir todos los estatus, "no" para excluir "Vacante".
    :param nivel: Nivel actual en la jerarquía (0 para la raíz).
    :param contador: Contador de empleados procesados.
    :param empleados_lista: Lista acumulada de empleados en el organigrama.
    :param max_niveles: Límite de profundidad (int). Si es None, no hay límite.
    """
    if empleados_lista is None:
        empleados_lista = []

    # 1. Si la posición raíz no está en empleados_lista, se agrega:
    if not any(emp['Posición'] == Posición_inicial for emp in empleados_lista):
        fila_inicial = data[data['Posición'] == Posición_inicial]
        if not fila_inicial.empty:
            emp_inicial = fila_inicial.iloc[0]
            empleados_lista.append({
                'Estatus': emp_inicial['Estatus'],
                'fecha ing': emp_inicial.get('fecha ing', ''),
                'Nº pers': emp_inicial['Nº pers'],
                'Número de personal': emp_inicial['Número de personal'],
                'Posición': emp_inicial['Posición'],
                'Posición.1': emp_inicial.get('Posición.1', ''),
                'Subdivisión del': emp_inicial.get('Subdivisión de', ''),
                'Área de nómina': emp_inicial.get('Área de nómina', ''),
                'JEFE INMEDIATO': emp_inicial.get('JEFE INMEDIATO', ''),
                'NOMBRE JEFE INMEDIATO': emp_inicial.get('NOMBRE JEFE INMEDIATO', '')
            })
            print(f"{'  ' * nivel}• {emp_inicial['Número de personal']} (Posición: {emp_inicial['Posición']})")

    # 2. Si ya alcanzamos el nivel máximo, no seguimos recursión
    if max_niveles is not None and nivel >= max_niveles:
        return contador, 0, 0, empleados_lista

    # 3. Filtrar siguientes empleados (directos) según "JEFE INMEDIATO"
    if estatus_filtro == 'si':
        empleados_sub = data[data['JEFE INMEDIATO'] == Posición_inicial]
    else:
        empleados_sub = data[(data['JEFE INMEDIATO'] == Posición_inicial) & (data['Estatus'] != 'Vacante')]

    if empleados_sub.empty:
        return contador, 0, 0, empleados_lista

    vacantes = 0
    activos = 0

    for _, empleado in empleados_sub.iterrows():
        # Contar vacantes o activos
        if empleado['Estatus'] == 'Vacante':
            vacantes += 1
        else:
            activos += 1

        # Evitar duplicados antes de agregar
        if not any(emp['Posición'] == empleado['Posición'] for emp in empleados_lista):
            empleados_lista.append({
                'Estatus': empleado['Estatus'],
                'fecha ing': empleado.get('fecha ing', ''),
                'Nº pers': empleado['Nº pers'],
                'Número de personal': empleado['Número de personal'],
                'Posición': empleado['Posición'],
                'Posición.1': empleado.get('Posición.1', ''),
                'Subdivisión del': empleado.get('Subdivisión de', ''),
                'Área de nómina': empleado.get('Área de nómina', ''),
                'JEFE INMEDIATO': empleado.get('JEFE INMEDIATO', ''),
                'NOMBRE JEFE INMEDIATO': empleado.get('NOMBRE JEFE INMEDIATO', '')
            })

        print("  " * (nivel+1) + f"• {empleado['Número de personal']} (Posición: {empleado['Posición']})")

        # Llamada recursiva para los subordinados del empleado actual
        sub_contador, sub_vacantes, sub_activos, empleados_lista = generar_organigrama(
            data, empleado['Posición'], estatus_filtro, nivel + 1, contador,
            empleados_lista, max_niveles
        )
        vacantes += sub_vacantes
        activos += sub_activos

    return contador + len(empleados_sub), vacantes, activos, empleados_lista


# -------------------------------
# EJEMPLO DE USO
# -------------------------------
if __name__ == "__main__":
    ruta_archivo = r'C:\Users\Juan\Downloads\activos_con_vacantes_y_jefe2.xlsx'

    try:
        data = pd.read_excel(ruta_archivo)
        # Verificar columnas mínimas
        required_columns = {'Posición', 'JEFE INMEDIATO', 'Número de personal', 'Estatus'}
        if not required_columns.issubset(data.columns):
            print(f"Error: El archivo debe contener las columnas {', '.join(required_columns)}.")
        else:
            Posición_inicial = int(input("Ingrese la Posición inicial: ").strip())

            # Filtro de estatus
            estatus_filtro = input("¿Quieres incluir todos los estatus? (si/no): ").strip().lower()
            if estatus_filtro not in ['si', 'no']:
                print("Opción inválida, por favor ingresa 'si' o 'no'.")
            else:
                # Preguntar cuántos niveles se desean
                niveles_input = input("¿Cuántos niveles de jerarquía deseas ver? (Escribe 'todos' para sin límite): ").strip().lower()
                if niveles_input == 'todos':
                    max_niveles = None  # Sin límite
                else:
                    max_niveles = int(niveles_input)  # Límite numérico

                print(f"\nOrganigrama a partir de la posición {Posición_inicial}:\n")

                total_registros, vacantes, activos, empleados_lista = generar_organigrama(
                    data, Posición_inicial, estatus_filtro=estatus_filtro, max_niveles=max_niveles
                )

                # Mostrar resumen
                print("\n--- Resumen ---")


                print(f"Total de vacantes: {vacantes}")
                print(f"Total de activos: {activos}")

                # Guardar los datos organizados en Excel
                df_empleados = pd.DataFrame(empleados_lista)

                # Ajusta la ruta y el nombre del archivo de salida a conveniencia
                ruta_salida = rf'C:\Users\Juan\Downloads\{Posición_inicial}.xlsx'
                df_empleados.to_excel(ruta_salida, index=False)
                print(f"\nArchivo Excel con el organigrama guardado en: {ruta_salida}")

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en la ruta {ruta_archivo}.")
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
