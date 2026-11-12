"""Dashboard Streamlit: mapa de riesgo, series, pronóstico (red bayesiana), calendario (CSP) y chat con el agente."""
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from cafe import config as C
from cafe import csp as csp_mod
from cafe import tools as T
from cafe.agent import run_agent

st.set_page_config(page_title="Café · Asistente agroclimático", page_icon="☕", layout="wide")
COL = {"Bajo": "#2e7d32", "Medio": "#f9a825", "Alto": "#c62828"}

if not (C.WEEKLY.exists() and C.MODEL_PATH.exists()):
    st.error("Faltan datos o modelo. Ejecute (ver README): `python -m cafe.data_download && python -m cafe.data_prep && python -m cafe.risk_model`")
    st.stop()

if C.is_demo_data():
    st.warning("MODO DEMO: los datos son sintéticos y solo sirven para probar la aplicación. No representan observaciones IDEAM ni deben usarse para análisis o informes.")

W = T._weekly()
MUNS = T.municipios()

# ------------------------- Barra lateral: parámetros -------------------------
st.sidebar.title("☕ Parámetros")
mun = st.sidebar.selectbox("Municipio", MUNS)
dmax = W["semana"].max().date()
fecha = st.sidebar.date_input("Fecha de referencia", dmax, min_value=W["semana"].min().date(), max_value=dmax)
horizonte = st.sidebar.slider("Horizonte del calendario (semanas)", 4, 12, 8)
ha = st.sidebar.number_input("Hectáreas", 0.5, 50.0, 1.0, 0.5)
cap = st.sidebar.number_input("Capacidad de mano de obra (jornales/semana)", 5.0, 200.0, 30.0, 5.0)
labs = st.sidebar.multiselect("Labores", list(csp_mod.CATALOGO), ["deshierba", "fertilizacion", "aspersion_roya", "recoleccion"])
st.sidebar.caption(f"Modo del agente: {'LLM (' + C.LLM_MODEL + ')' if C.LLM_API_KEY else 'local (sin LLM, determinista)'}")
st.sidebar.caption("⚠️ Indicador climático orientativo. No es diagnóstico ni consejo agronómico.")

st.title(f"☕ Asistente agroclimático — {mun.title()}")
tabs = st.tabs(["🗺️ Mapa de riesgo", "📈 Series de tiempo", "🔮 Pronóstico", "📅 Calendario de labores", "💬 Agente", "📊 Métricas"])

# ------------------------- Mapa -------------------------
with tabs[0]:
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
                             zoom=7, height=520, category_orders={"riesgo": ["Bajo", "Medio", "Alto"]})
        fig.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, width="stretch")
        source = "datos sintéticos de demostración" if C.is_demo_data() else "municipios con estaciones IDEAM"
        st.caption(f"Color = riesgo climático más probable de roya la semana siguiente; tamaño = P(riesgo Alto). Fuente: {source}.")

# ------------------------- Series -------------------------
with tabs[1]:
    d = W[(W.municipio == mun) & (W.semana <= pd.Timestamp(fecha))].tail(104)
    f = make_subplots(specs=[[{"secondary_y": True}]])
    f.add_bar(x=d.semana, y=d.lluvia_mm, name="Lluvia semanal (mm)", marker_color="#4f83cc")
    f.add_scatter(x=d.semana, y=d.temp_c, name="Temperatura media (°C)", line=dict(color="#d84315"), secondary_y=True)
    f.add_hrect(y0=21, y1=25, fillcolor="orange", opacity=0.12, line_width=0, secondary_y=True,
                annotation_text="21–25 °C (favorable a roya)", annotation_position="top left")
    f.update_yaxes(title_text="mm", secondary_y=False)
    f.update_yaxes(title_text="°C", secondary_y=True)
    f.update_layout(height=450, legend=dict(orientation="h"), margin=dict(t=30))
    st.plotly_chart(f, width="stretch")
    source = "datos sintéticos locales (demo)" if C.is_demo_data() else "IDEAM (datos.gov.co)"
    st.caption(f"Fuente: {source}, agregado semanal y promediado entre las estaciones del municipio. Datos crudos no validados.")

# ------------------------- Pronóstico -------------------------
with tabs[2]:
    r = T.risk(mun, str(fecha))
    if "error" in r:
        st.error(r["error"])
    else:
        c1, c2 = st.columns([1, 1])
        p = r["prob_riesgo_semana_siguiente"]
        fig = go.Figure(go.Bar(x=list(p), y=list(p.values()), marker_color=[COL[k] for k in p], text=[f"{v:.0%}" for v in p.values()]))
        fig.update_layout(title="P(riesgo de roya la semana siguiente)", yaxis_range=[0, 1], height=380)
        c1.plotly_chart(fig, width="stretch")
        c2.metric("Riesgo más probable", r["riesgo_mas_probable"])
        c2.write(f"Último dato: semana del **{r['semana_ultimo_dato']}** · lluvia {r['lluvia_ultima_semana_mm']} mm · {r['temp_ultima_semana_c']} °C")
        c2.json(r["evidencia"])
        c2.caption(r["aviso"] + " Inferencia por eliminación de variables sobre una red bayesiana propia.")

# ------------------------- Calendario -------------------------
with tabs[3]:
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
                    fg.add_trace(go.Bar(y=[g["labor"]], x=[g["fin"] - g["ini"]], base=g["ini"], orientation="h", showlegend=False))
                fg.update_layout(height=330, xaxis=dict(title="Semana (desde la referencia)", dtick=1, range=[0.5, horizonte + 0.5]), barmode="overlay")
                for i, cat in enumerate(clima.lluvia_esperada, 1):
                    fg.add_vrect(x0=i - 0.5, x1=i + 0.5, fillcolor={"Baja": "#fff59d", "Media": "#a5d6a7", "Alta": "#90caf9"}[cat], opacity=0.35, line_width=0, layer="below")
                st.plotly_chart(fg, width="stretch")
                st.dataframe(cal, hide_index=True, width="stretch")
            st.caption(f"Fondo: lluvia esperada (amarillo=Baja, verde=Media, azul=Alta; climatología IDEAM del municipio). Nodos explorados por el CSP: {s['nodos']}. {s['aviso']}")

# ------------------------- Chat -------------------------
with tabs[4]:
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("trace"):
                with st.expander("Herramientas llamadas"):
                    st.code(json.dumps([{"tool": t["tool"], "args": t["args"]} for t in m["trace"]], ensure_ascii=False, indent=1))
    q = st.chat_input(f"Pregunte sobre roya, clima o labores en {mun.title()}…")
    if q:
        st.session_state.chat.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat[-7:-1]]
        with st.chat_message("assistant"):
            with st.spinner("Pensando…"):
                out = run_agent(q, {"municipio": mun, "fecha": str(fecha), "hectareas": ha, "capacidad_jornales": cap}, hist)
            st.markdown(out["answer"])
            with st.expander("Herramientas llamadas"):
                st.code(json.dumps([{"tool": t["tool"], "args": t["args"]} for t in out["trace"]], ensure_ascii=False, indent=1))
        st.session_state.chat.append({"role": "assistant", "content": out["answer"], "trace": out["trace"]})

# ------------------------- Métricas -------------------------
with tabs[5]:
    for f_, t_ in ((C.RESULTS_DIR / "metricas_modelo.md", "Modelo (red bayesiana vs. líneas base)"), (C.RESULTS_DIR / "eval_agente.md", "Evaluación del agente")):
        st.subheader(t_)
        st.markdown(f_.read_text(encoding="utf-8") if f_.exists() else "Aún no generado. Ver README.")
