import streamlit as st
import pandas as pd
from io import BytesIO

def generar_organigrama(data, posicion_inicial, estatus_filtro='todos',
                        nivel=0, empleados_lista=None, max_niveles=None):

    if empleados_lista is None:
        empleados_lista = []

    if not any(emp['Posición'] == posicion_inicial for emp in empleados_lista):
        fila_inicial = data[data['Posición'] == posicion_inicial]
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

    if max_niveles is not None and nivel >= max_niveles:
        return empleados_lista

    if estatus_filtro == 'si':
        empleados_sub = data[data['JEFE INMEDIATO'] == posicion_inicial]
    else:
        empleados_sub = data[(data['JEFE INMEDIATO'] == posicion_inicial) & (data['Estatus'] != 'Vacante')]

    for _, empleado in empleados_sub.iterrows():
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

        empleados_lista = generar_organigrama(
            data, empleado['Posición'], estatus_filtro, nivel + 1,
            empleados_lista, max_niveles
        )

    return empleados_lista

# --- Streamlit App ---
st.set_page_config(page_title="📂 Generador de Organigrama SAP", layout="wide")

st.title("📂 Generador de Organigrama SAP")
st.subheader("⚠️ El Organigrama se genera con las siguientes columnas:")
st.markdown("""
    Estatus, Fecha ing, Nº pers, Número de personal, Posición, Posición.1 (Nombre de la Posición), Subdivisión del,	Área de nómina,	Jefe Inmediato,	Nombre Jefe Inmediato
    """)

# Subir archivos
uploaded_activos = st.file_uploader("Sube la base de **activos.xlsx** de SAP", type=['xlsx'])
uploaded_vacantes = st.file_uploader("Sube la base de **vacantes.xlsx** de SAP", type=['xlsx'])
uploaded_pwp = st.file_uploader("Sube la base de Estructura de **PWP.xlsx**", type=['xlsx'])

if uploaded_activos and uploaded_vacantes and uploaded_pwp:
    df_activos = pd.read_excel(uploaded_activos, header=4)
    df_vacantes = pd.read_excel(uploaded_vacantes, header=4)
    df_pwp = pd.read_excel(uploaded_pwp)

    df_activos.columns = df_activos.columns.str.strip()
    df_vacantes.columns = df_vacantes.columns.str.strip()
    df_pwp.columns = df_pwp.columns.str.strip()

    df_vacantes_convertido = pd.DataFrame({col: [pd.NA] * df_vacantes.shape[0] for col in df_activos.columns})

    mapeo = {
        "Ce.coste": "Ce.Co",
        "Centro de coste": "Ce.Co.1",
        "Un.org.": "Un.Org.",
        "Unidad Organizativa": "Unidad Organizativa",
        "Posición": "ID obj.",
        "Posición.1": "Denominación objeto",
        "Subdivisión de": "Subdivisión de personal"
    }

    for dest, orig in mapeo.items():
        if orig in df_vacantes.columns and dest in df_vacantes_convertido.columns:
            df_vacantes_convertido[dest] = df_vacantes[orig].fillna("")

    df_vacantes_convertido["Nº pers"] = 0
    df_vacantes_convertido["Número de personal"] = "Vacante"
    df_vacantes_convertido.fillna("", inplace=True)

    df_final = pd.concat([df_activos, df_vacantes_convertido], ignore_index=True)
    df_final["Estatus"] = df_final["Número de personal"].apply(
        lambda x: "Vacante" if x == "Vacante" else "Activo"
    )

    df_merged = df_final.merge(
        df_pwp[["CODIGO", "JEFE INMEDIATO"]],
        how="left",
        left_on="Posición",
        right_on="CODIGO"
    ).drop(columns="CODIGO")

    df_merged[["JEFE INMEDIATO", "NOMBRE JEFE INMEDIATO"]] = df_merged["JEFE INMEDIATO"].str.split("-", n=1, expand=True)
    df_merged["JEFE INMEDIATO"] = df_merged["JEFE INMEDIATO"].str.strip().astype(str)
    df_merged["Posición"] = df_merged["Posición"].astype(str)
    df_merged["NOMBRE JEFE INMEDIATO"] = df_merged["NOMBRE JEFE INMEDIATO"].str.strip()

    st.success("✅ Archivos cargados y procesados exitosamente.")

    # Parámetros del usuario
    posicion_inicial = st.text_input("📌 Ingresa la Posición inicial:")
    estatus_filtro = st.selectbox("¿Incluir vacantes?", ['si', 'no'])
    niveles_input = st.text_input("🔢 ¿Cuántos niveles quieres? ('todos' para sin límite)", "todos")

    if st.button("Generar Organigrama"):
        max_niveles = None if niveles_input == 'todos' else int(niveles_input)

        empleados_lista = generar_organigrama(
            df_merged, posicion_inicial, estatus_filtro, max_niveles=max_niveles
        )

        if empleados_lista:
            df_resultado = pd.DataFrame(empleados_lista)
            st.dataframe(df_resultado, use_container_width=True)

            # Descargar Excel
            buffer = BytesIO()
            df_resultado.to_excel(buffer, index=False)
            st.download_button(
                "📥 Descargar Organigrama en Excel",
                data=buffer.getvalue(),
                file_name=f'organigrama_{posicion_inicial}.xlsx',
                mime='application/vnd.ms-excel'
            )
        else:
            st.warning("⚠️ No se encontraron empleados bajo esta posición.")
else:
    st.info("⚠️ Sube los archivos solicitados para continuar.")

