import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime


def generar_organigrama(data, codigo_inicial, estatus_filtro='todos', nivel=0, salida_texto=None):
    """
    Genera el organigrama de forma recursiva, iniciando desde `codigo_inicial`.

    Args:
        data (pd.DataFrame): DataFrame con las columnas CODIGO, JEFE INMEDIATO, NOMBRE EMPLEADO, ESTATUS SAP, etc.
        codigo_inicial (str): Código raíz (jefe inicial) en formato string.
        estatus_filtro (str): 'si' -> incluye todos los estatus; 'no' -> excluye 'Inactivo'.
        nivel (int): Nivel de indentación (para mostrar jerarquía).
        salida_texto (list): Lista donde se irán acumulando las líneas de jerarquía (en vez de imprimir).

    Returns:
        tuple: (contador, vacantes, activos, empleados_lista)
    """
    # Filtramos según el estatus elegido
    if estatus_filtro == 'si':
        empleados = data[data['JEFE INMEDIATO'] == codigo_inicial]
    else:
        # Excluimos "Inactivo"
        empleados = data[
            (data['JEFE INMEDIATO'] == codigo_inicial)
            & (data['ESTATUS SAP'] != 'Inactivo')
            ]

    if empleados.empty:
        return 0, 0, 0, []

    contador = 0
    vacantes = 0
    activos = 0
    empleados_lista = []

    for _, empleado in empleados.iterrows():
        # Contamos el registro
        contador += 1

        # Vacante o activo
        if empleado['NOMBRE EMPLEADO'] == 'Vacante':
            vacantes += 1
        else:
            activos += 1

        # Procesar area nomina si viene con " - "
        if isinstance(empleado['AREA NOMINA'], str) and ' - ' in empleado['AREA NOMINA']:
            area_nomina = empleado['AREA NOMINA'].split(' - ', 1)[-1]
        else:
            area_nomina = empleado['AREA NOMINA']

        # Determinar el nombre del jefe inmediato, si se encuentra
        nombre_jefe = ''
        jefe_match = data[data['CODIGO'] == empleado['JEFE INMEDIATO']]
        if not jefe_match.empty:
            nombre_jefe = jefe_match.iloc[0]['NOMBRE EMPLEADO']

        # Agregamos registro a la lista
        empleados_lista.append({
            'ESTATUS SAP': empleado['ESTATUS SAP'],
            'NUMERO EMPLEADO': empleado.get('NUMERO EMPLEADO', ''),
            'NOMBRE EMPLEADO': empleado['NOMBRE EMPLEADO'],
            'CODIGO': empleado['CODIGO'],
            'NOMBRE POSICION': empleado.get('NOMBRE POSICION', ''),
            'CENTRO COSTE': empleado.get('CENTRO COSTE', ''),
            'AREA NOMINA': area_nomina,
            'JEFE INMEDIATO': empleado['JEFE INMEDIATO'],
            'NOMBRE JEFE INMEDIATO': nombre_jefe
        })

        # En lugar de print, acumulamos en salida_texto
        if salida_texto is not None:
            salida_texto.append("  " * nivel + f"• {empleado['NOMBRE EMPLEADO']} (CODIGO: {empleado['CODIGO']})")

        # Llamada recursiva
        sub_contador, sub_vacantes, sub_activos, sub_empleados_lista = generar_organigrama(
            data,
            codigo_inicial=empleado['CODIGO'],
            estatus_filtro=estatus_filtro,
            nivel=nivel + 1,
            salida_texto=salida_texto
        )

        # Acumulamos
        contador += sub_contador
        vacantes += sub_vacantes
        activos += sub_activos
        empleados_lista.extend(sub_empleados_lista)

    return contador, vacantes, activos, empleados_lista


def main():
    st.title("📂 Generación de Organigrama con estructura de PWP")

    # Cargar archivo Excel
    st.subheader("Sube tu archivo Excel (.xlsx)")
    st.subheader("⚠️ Instrucción importante")
    st.markdown("""
    Es importante que al descargar el **Reporte de estructura desde PWP** por primera vez, lo abras en Excel y lo **guardes nuevamente como archivo `.xlsx`** antes de subirlo aquí.

    Esto evita errores de formato y garantiza que se pueda procesar correctamente.
    """)
    file = st.file_uploader("Selecciona el archivo con la estructura de datos", type=["xlsx"])

    if file:
        try:
            # Leer el Excel en un DataFrame
            data = pd.read_excel(file)

            # Limpieza para evitar errores con 'null'
            data['CODIGO'] = data['CODIGO'].replace('null', '').astype(str)
            data['JEFE INMEDIATO'] = data['JEFE INMEDIATO'].replace('null', '').astype(str)

            # Partir JEFE INMEDIATO antes de " - "
            data['JEFE INMEDIATO'] = data['JEFE INMEDIATO'].apply(
                lambda x: x.split(" - ")[0] if " - " in x else x
            )

            # Opciones de entrada
            codigo_inicial = st.text_input("Ingrese el CODIGO inicial", value="")
            estatus_filtro = st.selectbox("¿Quieres incluir todos los estatus?", ["no (excluye Inactivo)", "si"])

            if st.button("Generar organigrama"):
                if not codigo_inicial:
                    st.warning("Por favor ingresa un valor para CODIGO inicial.")
                else:
                    # Generar organigrama
                    salida_texto = []
                    total_registros, vacantes, activos, empleados_lista = generar_organigrama(
                        data,
                        codigo_inicial=codigo_inicial,
                        estatus_filtro=estatus_filtro,
                        salida_texto=salida_texto
                    )

                    # Mostrar jerarquía
                    st.subheader("Jerarquía Generada:")
                    for linea in salida_texto:
                        st.text(linea)

                    # Mostrar resultados
                    st.write(f"**Total de registros encontrados**: {total_registros}")
                    st.write(f"**Total de vacantes**: {vacantes}")
                    st.write(f"**Total de activos**: {activos}")

                    # Preparamos el DataFrame
                    df_empleados = pd.DataFrame(empleados_lista)

                    # Nombre de archivo dinámico
                    hoy_str = datetime.now().strftime("%Y_%m_%d")
                    # Buscamos el nombre del jefe en data
                    filtro_jefe = data[data['CODIGO'] == codigo_inicial]
                    if not filtro_jefe.empty:
                        nombre_jefe = filtro_jefe.iloc[0]['NOMBRE EMPLEADO']
                    else:
                        nombre_jefe = "Desconocido"

                    # Reemplazar espacios por guiones bajos, etc.
                    nombre_jefe_limpio = nombre_jefe.replace(" ", "_")
                    # Armamos el nombre final
                    nombre_archivo = f"Organigrama_{hoy_str}_{codigo_inicial}_{nombre_jefe_limpio}.xlsx"

                    # Convertir a Excel en memoria
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_empleados.to_excel(writer, index=False, sheet_name="Organigrama")
                    datos_xlsx = output.getvalue()

                    # Botón de descarga
                    st.download_button(
                        label="Descargar Organigrama en Excel",
                        data=datos_xlsx,
                        file_name=nombre_archivo,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")


if __name__ == "__main__":
    main()
