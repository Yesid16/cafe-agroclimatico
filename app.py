"""Dashboard Streamlit: mapa de riesgo, series, pronóstico (red bayesiana), calendario (CSP) y chat con el agente."""
import json
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from cafe import config as C
from cafe import csp as csp_mod
from cafe import tools as T
from cafe.agent import run_agent
from cafe.climate_series import calendar_view
from cafe.ui import apply_theme, summary_card, show_chart, LABOR_LABELS

st.set_page_config(page_title="Café · Asistente agroclimático", page_icon="☕", layout="wide")
apply_theme(C.ROOT)
COL = {"Bajo": "#397d60", "Medio": "#c49a40", "Alto": "#b95848"}

if not (C.WEEKLY.exists() and C.MODEL_PATH.exists()):
    st.error("Faltan artefactos. Ejecute notebooks/02_Colab_pipeline.ipynb en Colab y copie data/processed/ desde el ZIP de resultados (ver README).")
    st.stop()

W = T._weekly()
MUNS = T.municipios()

# ------------------------- Controles y resumen -------------------------
st.sidebar.markdown(
    '<div class="agro-brand"><span class="agro-brand-icon">☕</span>'
    '<div><strong>Café Agroclima</strong><small>Clima, contexto y planificación</small></div></div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown('<p class="agro-eyebrow">Tu ubicación</p>', unsafe_allow_html=True)
mun = st.sidebar.selectbox("Municipio", MUNS, format_func=lambda m: m.replace(" / ", ", ").title())
dmax = W["semana"].max().date()
fecha = st.sidebar.date_input("Fecha de referencia", dmax, min_value=W["semana"].min().date(), max_value=dmax,
                              help="Las estimaciones y el calendario parten de esta fecha y de los datos disponibles.")

with st.sidebar.expander("Planificar labores", expanded=False):
    horizonte = st.slider("Horizonte del calendario (semanas)", 4, 12, 8)
    ha = st.number_input("Hectáreas", 0.5, 50.0, 1.0, 0.5)
    cap = st.number_input("Capacidad de mano de obra (jornales/semana)", 5.0, 200.0, 30.0, 5.0)
    labs = st.multiselect("Labores", list(csp_mod.CATALOGO), ["deshierba", "fertilizacion", "recoleccion"],
                          format_func=lambda name: LABOR_LABELS.get(name, name))


def forget_nvidia_key():
    st.session_state["nvidia_api_key"] = ""


with st.sidebar.expander("Conectar con NVIDIA", expanded=False):
    user_api_key = st.text_input(
        "Tu API key de NVIDIA", type="password", key="nvidia_api_key",
        help="Se usa solo en tu sesión. No se escribe en archivos ni se comparte con otros visitantes.",
    ).strip()
    st.button("Olvidar mi clave", on_click=forget_nvidia_key, disabled=not user_api_key)
    st.caption("La clave pasa por este servidor para consultar NVIDIA. No se guarda en archivos; no la pegues en el chat.")
    st.markdown("[Crear una clave en NVIDIA](https://build.nvidia.com/)")
st.sidebar.caption("● Clave de sesión ingresada" if user_api_key else "○ Chat en modo demostración")
with st.sidebar.expander("Sobre los datos y el alcance"):
    st.caption("Datos históricos de estaciones IDEAM, usados como referencia municipal. "
               "La fecha estimada parte del último dato disponible. Las consultas históricas utilizan el modelo "
               "final; la evaluación temporal está en Evaluación.")
    st.caption("Indicador climático orientativo. No es diagnóstico de campo ni consejo agronómico.")

st.markdown(
    '<div class="agro-hero"><div class="agro-eyebrow">CAFÉ · ASISTENTE AGROCLIMÁTICO</div>'
    '<h1>El clima de tu café, más claro.</h1>'
    '<p>Explora las condiciones de tu municipio y organiza tus labores con más contexto.</p></div>',
    unsafe_allow_html=True,
)
preview = T.risk(mun, str(fecha))
last_day = preview.get("semana_ultimo_dato")
target_day = preview.get("semana_objetivo_fin")
st.markdown('<span class="agro-badge">Datos históricos · Referencia '+escape(fecha.strftime("%d/%m/%Y"))+'</span>',
            unsafe_allow_html=True)
cards = st.columns([1.2, 1, 1, 1])
with cards[0]:
    summary_card("MUNICIPIO", mun.split(" / ")[0].title(), mun.split(" / ")[-1].title())
with cards[1]:
    summary_card("ÚLTIMA OBSERVACIÓN", pd.Timestamp(last_day).strftime("%d/%m/%Y") if last_day else "Sin datos",
                 "Semana terminada en domingo")
with cards[2]:
    risk_name = preview.get("riesgo_mas_probable", "Sin datos")
    note = "Indicador climático de favorabilidad"
    summary_card("RIESGO CLIMÁTICO", risk_name, note, risk=risk_name)
with cards[3]:
    summary_card("SEMANA ESTIMADA", pd.Timestamp(target_day).strftime("%d/%m/%Y") if target_day else "Sin datos",
                 "Fecha de cierre del periodo estimado")

tabs = st.tabs(["Mapa", "Clima", "Riesgo climático", "Plan de labores", "Asistente", "Evaluación"])

# ------------------------- Mapa -------------------------
with tabs[0]:
    st.subheader("Favorabilidad por municipio")
    st.caption("Explora la estimación climática regional. Cada punto muestra la fecha de su último dato.")
    rows = []
    for m in MUNS:
        r = T.risk(m, str(fecha))
        if "error" in r:
            continue
        d = W[W.municipio == m].iloc[0]
        rows.append({"municipio": m.title(), "lat": d.lat, "lon": d.lon, "riesgo": r["riesgo_mas_probable"],
                     "p_alto": r["prob_riesgo_semana_siguiente"]["Alto"], "ultimo_dato": r["semana_ultimo_dato"]})
    mp = pd.DataFrame(rows)
    if mp.empty:
        st.warning("Sin datos para la fecha elegida.")
    else:
        fig = px.scatter_map(mp, lat="lat", lon="lon", color="riesgo", color_discrete_map=COL, size="p_alto", size_max=22,
                             hover_name="municipio", hover_data={"p_alto": ":.2f", "ultimo_dato": True, "lat": False, "lon": False},
                             center={"lat": 4.5, "lon": -73.5}, zoom=4, height=520,
                             category_orders={"riesgo": ["Bajo", "Medio", "Alto"]})
        fig.update_layout(map_style="carto-positron", margin=dict(l=0, r=0, t=0, b=0))
        show_chart(fig)
        st.caption("Color = riesgo climático más probable de roya la semana siguiente; tamaño = P(riesgo Alto). Municipios con estaciones IDEAM.")

# ------------------------- Series -------------------------
@st.cache_data(show_spinner=False)
def read_climate_series(path, modified_ns):
    return pd.read_csv(path, parse_dates=["semana"])

with tabs[1]:
    st.subheader("Histórico del clima")
    st.caption("Lluvia, temperatura y humedad, con los datos disponibles de cada semana.")
    period = st.selectbox("Periodo de la serie", ["Últimos 2 años", "Todo el histórico"])
    if C.CLIMATE_WEEKLY.exists():
        climate = read_climate_series(str(C.CLIMATE_WEEKLY), C.CLIMATE_WEEKLY.stat().st_mtime_ns)
    else:
        climate = W
        st.caption("Esta instalación solo contiene las semanas disponibles para el modelo.")
    d = calendar_view(climate, mun, fecha, weeks=104 if period == "Últimos 2 años" else None)
    if d.empty:
        st.info("No hay registros de este municipio hasta la fecha elegida.")
    else:
        f = make_subplots(specs=[[{"secondary_y": True}]])
        f.add_bar(x=d.semana, y=d.lluvia_mm, name="Lluvia semanal (mm)", marker_color="#7eaa98")
        zero = d[d.lluvia_mm.eq(0)]
        f.add_scatter(x=zero.semana, y=zero.lluvia_mm, mode="markers",
                      marker=dict(color="#397d60", size=6), name="Semana con 0 mm")
        f.add_scatter(x=d.semana, y=d.temp_c, name="Temperatura media (°C)",
                      connectgaps=False, line=dict(color="#bd8656", width=2.5), secondary_y=True)
        f.add_hrect(y0=21, y1=25, fillcolor="#dcc6a3", opacity=0.14, line_width=0, secondary_y=True,
                    annotation_text="21–25 °C (favorable a roya)", annotation_position="top left")
        f.update_yaxes(title_text="mm", secondary_y=False)
        f.update_yaxes(title_text="°C", secondary_y=True)
        f.update_layout(height=450, legend=dict(orientation="h"), margin=dict(t=30))
        show_chart(f)
        if d.humedad_pct.notna().any():
            humidity = px.line(d, x="semana", y="humedad_pct", title="Humedad relativa media semanal (%)")
            humidity.update_traces(connectgaps=False)
            show_chart(humidity)
        st.caption(
            f"Semanas con datos válidos en este periodo: lluvia {int(d.lluvia_mm.notna().sum())}/{len(d)}, "
            f"temperatura {int(d.temp_c.notna().sum())}/{len(d)}, "
            f"humedad {int(d.humedad_pct.notna().sum())}/{len(d)}."
        )
        st.caption(
            "Los huecos significan que faltan datos válidos, no 0 mm de lluvia. "
            "Los puntos azules sobre cero identifican semanas observadas con 0 mm. "
            "Las fechas son domingos de cierre semanal; cada variable se muestra de forma independiente."
        )
        missing = d[list(("lluvia_mm", "temp_c", "humedad_pct"))].isna()
        if missing.any(axis=1).any():
            with st.expander("Ver semanas sin datos válidos"):
                absent = d.loc[missing.any(axis=1), ["semana", "lluvia_mm", "temp_c", "humedad_pct"]]
                st.dataframe(absent.rename(columns={"semana":"Semana (fin)", "lluvia_mm":"Lluvia (mm)",
                                                    "temp_c":"Temperatura (°C)", "humedad_pct":"Humedad (%)"}),
                             hide_index=True, width="stretch")
        st.caption(
            "Fuente: IDEAM (datos.gov.co), promedio municipal de estaciones. "
            "Lluvia con 5/6 días válidos extrapolada a 7; con menos de 5 días no se muestra. "
            "Temperatura y humedad requieren al menos 4 días válidos."
        )

# ------------------------- Pronóstico -------------------------
with tabs[2]:
    st.subheader("Riesgo climático de roya")
    st.caption("Una estimación de favorabilidad climática, basada en la última observación disponible.")
    r = preview
    if "error" in r:
        st.error(r["error"])
    else:
        c1, c2 = st.columns([1, 1])
        p = r["prob_riesgo_semana_siguiente"]
        fig = go.Figure(go.Bar(x=list(p), y=list(p.values()), marker_color=[COL[k] for k in p], text=[f"{v:.0%}" for v in p.values()]))
        fig.update_layout(title="Distribución del indicador climático", yaxis_range=[0, 1], height=380)
        with c1:
            show_chart(fig)
        c2.metric("Riesgo más probable", r["riesgo_mas_probable"])
        c2.write(f"Último dato: semana del **{r['semana_ultimo_dato']}** · lluvia {r['lluvia_ultima_semana_mm']} mm · {r['temp_ultima_semana_c']} °C")
        if r["riesgo_mas_probable"] == "Alto":
            c2.warning("Favorabilidad climática alta: priorice el monitoreo de campo con el extensionista.")
        for warning in r.get("avisos_datos", []):
            c2.warning(warning)
        with c2.expander("Ver condiciones utilizadas"):
            st.json(r["evidencia"])
        c2.caption(r["aviso"] + " Inferencia por eliminación de variables sobre una red bayesiana propia.")

# ------------------------- Calendario -------------------------
with tabs[3]:
    st.subheader("Organiza tus labores")
    st.caption("Ajusta área, mano de obra y actividades en «Planificar labores», en el panel lateral.")
    if not labs:
        st.info("Seleccione al menos una labor en la barra lateral.")
    else:
        s = T.schedule(mun, labs, horizonte, ha, cap, str(fecha))
        if "error" in s:
            st.error(s["error"])
        else:
            clima = pd.DataFrame({"semana": range(1, horizonte + 1), "lluvia_esperada": s["clima_esperado_por_semana"]})
            if not s["factible"]:
                st.warning(s["motivo"])
            else:
                cal = pd.DataFrame(s["calendario"])
                gantt = [{"labor": c.labor, "ini": c.semana_inicio - 0.5, "fin": c.semana_inicio - 0.5 + c.duracion_sem} for c in cal.itertuples()]
                fg = go.Figure()
                for g in gantt:
                    fg.add_trace(go.Bar(y=[LABOR_LABELS.get(g["labor"], g["labor"])], x=[g["fin"] - g["ini"]], base=g["ini"], orientation="h", showlegend=False))
                fg.update_layout(height=330, xaxis=dict(title="Semana (desde la referencia)", dtick=1, range=[0.5, horizonte + 0.5]), barmode="overlay")
                for i, cat in enumerate(clima.lluvia_esperada, 1):
                    fg.add_vrect(x0=i - 0.5, x1=i + 0.5, fillcolor={"Baja": "#fff59d", "Media": "#a5d6a7", "Alta": "#90caf9"}[cat], opacity=0.35, line_width=0, layer="below")
                show_chart(fg)
                display_cal = cal.assign(labor=cal.labor.map(lambda name: LABOR_LABELS.get(name, name)))
                st.dataframe(display_cal.rename(columns={"labor":"Labor", "semana_inicio":"Semana de inicio",
                    "duracion_sem":"Duración (semanas)", "fecha_inicio_aprox":"Inicio aproximado",
                    "lluvia_esperada":"Lluvia esperada"}), hide_index=True, width="stretch")
            st.caption(f"Fondo: lluvia esperada (amarillo=Baja, verde=Media, azul=Alta; climatología IDEAM del municipio). Nodos explorados por el CSP: {s['nodos']}. {s['aviso']}")

# ------------------------- Chat -------------------------
with tabs[4]:
    st.subheader("Conversa con tu asistente")
    st.caption("Pregunta por el clima, la favorabilidad de roya o la planificación de labores.")
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if st.button("Nueva conversación"):
        st.session_state.chat = []
    suggestion = None
    if not st.session_state.chat:
        st.markdown(
            '<div class="agro-chat-welcome"><span class="agro-brand-icon" style="margin:auto">☕</span>'
            '<h3>¿Qué necesitas saber hoy?</h3><p>Empieza con una consulta o escribe tu propia pregunta.</p></div>',
            unsafe_allow_html=True,
        )
        quick = st.columns(3)
        with quick[0]:
            if st.button("Consultar riesgo", width="stretch"):
                suggestion = f"¿Cuál es el riesgo climático de roya en {mun.title()}?"
        with quick[1]:
            if st.button("Planificar labores", width="stretch"):
                suggestion = f"Arma un calendario de labores para {mun.title()}."
        with quick[2]:
            if st.button("Entender la roya", width="stretch"):
                suggestion = "¿Qué es la roya del cafeto y cuáles son sus síntomas?"
        if not user_api_key:
            st.caption("Para usar NVIDIA con tu cuenta, abre «Conectar con NVIDIA» en el panel lateral. Sin clave puedes probar la demostración.")
    for message in st.session_state.chat:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("trace"):
                with st.expander("Fuentes y herramientas consultadas"):
                    st.code(json.dumps([{"tool": t["tool"], "args": t["args"]} for t in message["trace"]],
                                       ensure_ascii=False, indent=1))
    q = st.chat_input(f"Escribe una pregunta sobre {mun.split(' / ')[0].title()}…") or suggestion
    if q:
        st.session_state.chat.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat[-7:-1]]
        with st.chat_message("assistant"):
            with st.spinner("Consultando información…"):
                out = run_agent(q, {"municipio": mun, "fecha": str(fecha), "hectareas": ha,
                    "capacidad_jornales": cap, "semanas": horizonte, "labores": labs}, hist,
                    api_key=user_api_key, base_url="https://integrate.api.nvidia.com/v1")
            modes = {"llm":"NVIDIA", "mock":"Demostración", "fallback":"Demostración · NVIDIA no disponible"}
            source = " · Resumen de las fuentes" if out.get("answer_source") == "tool_summary" else ""
            st.caption(modes.get(out["mode"], out["mode"]) + source)
            st.markdown(out["answer"])
            with st.expander("Fuentes y herramientas consultadas"):
                st.code(json.dumps([{"tool": t["tool"], "args": t["args"]} for t in out["trace"]],
                                   ensure_ascii=False, indent=1))
        st.session_state.chat.append({"role": "assistant", "content": out["answer"], "trace": out["trace"]})

# ------------------------- Métricas -------------------------
with tabs[5]:
    st.subheader("Resultados y transparencia")
    st.caption("La demo carga la instantánea original de Colab. La variante conservadora se conserva como sensibilidad y no es una validación certificada de sensores.")
    comparison = C.ROOT / "results/revision_calidad/comparacion_calidad.md"
    if comparison.exists():
        st.subheader("Sensibilidad a la política de calidad")
        st.markdown(comparison.read_text(encoding="utf-8"))
    for f_, t_ in ((C.RESULTS_DIR / "metricas_modelo.md", "Modelo (red bayesiana vs. líneas base)"), (C.RESULTS_DIR / "eval_agente_llm.md", "LLM: ejecución original de Colab"),
                    (C.RESULTS_DIR / "eval_agente_llm_revisado.md", "LLM: revisión con control de citas"), (C.RESULTS_DIR / "eval_agente_mock.md", "Evaluación del respaldo")):
        st.subheader(t_)
        st.markdown(f_.read_text(encoding="utf-8") if f_.exists() else "Aún no generado. Ver README.")
