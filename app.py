"""Interfaz Streamlit del modelo de priorización espacial."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from bl_blueberry.data import FEATURE_COLUMNS, validate_candidates, validate_views
from bl_blueberry.model import DEFAULT_FEATURE_WEIGHTS, BlackLittermanSpatialModel


ROOT = Path(__file__).parent
SAMPLE_AREAS = ROOT / "data" / "sample_candidates.csv"
SAMPLE_VIEWS = ROOT / "data" / "sample_views.csv"

st.set_page_config(page_title="Blueberry Costa Rica", page_icon="🫐", layout="wide")
st.title("Priorización de áreas para moras azules")
st.caption("Adaptación básica y transparente de Black–Litterman para Costa Rica")

with st.sidebar:
    st.header("Datos")
    area_upload = st.file_uploader("CSV de áreas candidatas", type="csv")
    view_upload = st.file_uploader("CSV de views", type="csv")
    use_demo = st.checkbox("Usar datos demostrativos", value=area_upload is None)
    st.divider()
    st.header("Parámetros")
    tau = st.slider("tau — incertidumbre del prior", 0.05, 1.00, 0.25, 0.05)
    max_share = st.slider("Máximo por área (%)", 5, 100, 25, 5) / 100

    st.subheader("Pesos agronómicos")
    weights = {}
    for feature in FEATURE_COLUMNS:
        label = feature.replace("_score", "").replace("_", " ").title()
        weights[feature] = st.slider(label, 0.0, 1.0, float(DEFAULT_FEATURE_WEIGHTS[feature]), 0.05)
    total = sum(weights.values())
    st.caption(f"Los pesos se normalizan automáticamente. Suma actual: {total:.2f}")

try:
    if use_demo or area_upload is None:
        areas_raw = pd.read_csv(SAMPLE_AREAS)
        views_raw = pd.read_csv(SAMPLE_VIEWS)
        st.info("Se están usando datos sintéticos de demostración. Sustitúyelos por datos públicos procesados antes de tomar decisiones.")
    else:
        areas_raw = pd.read_csv(area_upload)
        views_raw = pd.read_csv(view_upload) if view_upload is not None else pd.DataFrame(columns=["view_id", "view_type", "asset_a", "asset_b", "q", "confidence"])
    areas, report = validate_candidates(areas_raw)
    views = validate_views(views_raw, areas["candidate_id"].astype(str)) if len(views_raw) else views_raw
    for warning in report.warnings:
        st.warning(warning)
    target_default = min(float(areas["area_ha"].sum()), 100.0)
    target = st.number_input("Hectáreas objetivo", min_value=0.1, value=target_default, step=1.0)
    model = BlackLittermanSpatialModel(weights, tau=tau, max_share=max_share, target_area_ha=target)
    result = model.run(areas, views)
except Exception as exc:
    st.error(f"No se pudo ejecutar el modelo: {exc}")
    st.stop()

left, middle, right = st.columns(3)
left.metric("Áreas evaluadas", f"{len(result.table):,}")
middle.metric("Hectáreas recomendadas", f"{result.table['recommended_area_ha'].sum():,.1f}")
right.metric("Mejor score posterior", f"{result.table['posterior_score'].max():.2f}")

st.subheader("Resultado")
display_cols = ["rank", "candidate_id", "canton", "province", "posterior_score", "recommended_area_ha", "allocation_pct"]
shown = result.table[display_cols].copy()
shown["posterior_score"] = shown["posterior_score"].round(3)
shown["recommended_area_ha"] = shown["recommended_area_ha"].round(2)
shown["allocation_pct"] = (shown["allocation_pct"] * 100).round(1).astype(str) + "%"
st.dataframe(shown, use_container_width=True, hide_index=True)

chart_col, map_col = st.columns(2)
with chart_col:
    chart_df = result.table.sort_values("posterior_score", ascending=True)
    fig = px.bar(chart_df, x="posterior_score", y="candidate_id", orientation="h", color="province", title="Score posterior por área")
    fig.update_layout(height=520, xaxis_title="Score normalizado", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
with map_col:
    fig_map = px.scatter_geo(result.table, lat="latitude", lon="longitude", color="posterior_score", size="recommended_area_ha", hover_name="candidate_id", hover_data=["canton", "province", "posterior_score"], scope="south america", title="Ubicación aproximada y asignación")
    fig_map.update_geos(showland=True, landcolor="#eef3ed", showcountries=True, countrycolor="#b4bdb4")
    fig_map.update_layout(height=520, margin=dict(l=0, r=0, t=45, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

with st.expander("Views aplicadas"):
    st.dataframe(views if len(views) else pd.DataFrame({"mensaje": ["No se proporcionaron views; se usa únicamente el prior agronómico."]}), use_container_width=True, hide_index=True)

st.download_button("Descargar ranking CSV", result.table.to_csv(index=False).encode("utf-8"), "blueberry_ranking.csv", "text/csv")
st.caption("Nota: el score es una herramienta de priorización. Requiere validación agronómica, legal, ambiental y de agua en campo.")
