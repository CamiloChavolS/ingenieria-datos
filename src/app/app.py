"""RavenStack customer churn analytics dashboard."""

import os
from io import BytesIO
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.exc import SQLAlchemyError

try:
    from google.api_core.exceptions import GoogleAPIError
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    class GoogleAPIError(Exception):
        """Fallback when optional Google Cloud packages are absent."""

    class DefaultCredentialsError(Exception):
        """Fallback when optional Google auth packages are absent."""


st.set_page_config(
    page_title="RavenStack | Churn Intelligence",
    page_icon="📊",
    layout="wide",
)

APP_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = Path(os.path.abspath(os.path.join(APP_DIR, "..", "..")))
load_dotenv(os.path.abspath(os.path.join(PROJECT_ROOT, ".env")))
MODEL_PATH = os.path.abspath(
    os.path.join(PROJECT_ROOT, "models_saved", "churn_model.joblib")
)


def database_url():
    """Build the PostgreSQL URL from environment variables."""
    return URL.create(
        drivername=os.getenv("DB_DRIVER", "postgresql+psycopg2"),
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "ravenstack_db"),
    )


@st.cache_resource
def get_engine():
    return create_engine(database_url(), pool_pre_ping=True)


@st.cache_resource
def get_bigquery_client():
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError(
            "Instala google-cloud-bigquery para consultar BigQuery."
        ) from exc
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("Define GCP_PROJECT_ID para consultar BigQuery.")
    return bigquery.Client(project=project_id)


@st.cache_data(ttl=300)
def load_data():
    if os.getenv("APP_BACKEND", "postgres").lower() == "bigquery":
        project_id = os.environ["GCP_PROJECT_ID"]
        query = f"""
            SELECT industry, country, plan_tier,
                   monthly_recurring_revenue, is_churned, is_active,
                   churn_date, total_feature_usage, total_usage_errors,
                   last_activity_date, total_support_tickets,
                   avg_resolution_time_hours, avg_satisfaction_score
            FROM `{project_id}.gold.mart_customer_churn`
        """
        rows = get_bigquery_client().query(query).result()
        return pd.DataFrame([dict(row.items()) for row in rows])

    query = """
        SELECT industry, country, plan_tier,
               monthly_recurring_revenue, is_churned, is_active, churn_date,
               total_feature_usage, total_usage_errors, last_activity_date,
               total_support_tickets, avg_resolution_time_hours,
               avg_satisfaction_score
        FROM gold.mart_customer_churn
    """
    return pd.read_sql_query(query, con=get_engine())


@st.cache_data(ttl=300)
def load_feedback_themes():
    if os.getenv("APP_BACKEND", "postgres").lower() == "bigquery":
        project_id = os.environ["GCP_PROJECT_ID"]
        query = f"""
            SELECT theme, sentiment, feedback_count, average_confidence
            FROM `{project_id}.gold.mart_feedback_themes`
        """
        rows = get_bigquery_client().query(query).result()
        return pd.DataFrame([dict(row.items()) for row in rows])

    query = """
        SELECT theme, sentiment, feedback_count, average_confidence
        FROM gold.mart_feedback_themes
    """
    return pd.read_sql_query(query, con=get_engine())


@st.cache_resource
def load_model():
    model_uri = os.getenv("MODEL_GCS_URI")
    if model_uri:
        if not model_uri.startswith("gs://"):
            raise ValueError("MODEL_GCS_URI debe comenzar con gs://")
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError(
                "Instala google-cloud-storage para cargar el modelo desde GCS."
            ) from exc
        bucket_name, blob_name = model_uri[5:].split("/", 1)
        content = (
            storage.Client()
            .bucket(bucket_name)
            .blob(blob_name)
            .download_as_bytes()
        )
        return joblib.load(BytesIO(content))
    return joblib.load(os.path.abspath(MODEL_PATH))


def format_currency(value):
    return f"${value:,.0f}"


def filtered_data(data, industry, country, plan):
    result = data
    for column, selection in (
        ("industry", industry),
        ("country", country),
        ("plan_tier", plan),
    ):
        if selection and "Todos" not in selection and column in result.columns:
            result = result[result[column].isin(selection)]
    return result


st.title("📊 RavenStack: SaaS Churn Intelligence")
st.caption("Analítica de clientes y predicción de riesgo para negocios SaaS.")

try:
    df = load_data()
except (
    SQLAlchemyError,
    GoogleAPIError,
    DefaultCredentialsError,
    RuntimeError,
    ImportError,
    ValueError,
    KeyError,
) as exc:
    backend = os.getenv("APP_BACKEND", "postgres").lower()
    st.error(
        "No fue posible conectar con "
        + ("BigQuery" if backend == "bigquery" else "PostgreSQL")
        + (
            ". Confirma GCP_PROJECT_ID y las credenciales ADC."
            if backend == "bigquery"
            else (
                f" en {os.getenv('DB_HOST', 'localhost')}:"
                f"{os.getenv('DB_PORT', '5432')}. "
                "Inicia el contenedor y confirma DB_NAME, DB_USER y DB_PASSWORD."
            )
        )
    )
    st.caption(str(exc).splitlines()[0])
    st.stop()

if df.empty:
    st.warning("La tabla de clientes no contiene registros.")
    st.stop()

with st.sidebar:
    st.header("Filtros")

    def multiselect_filter(label, column):
        if column not in df.columns:
            return []
        values = sorted(df[column].dropna().astype(str).unique().tolist())
        return st.multiselect(label, ["Todos", *values], default=["Todos"])

    industries = multiselect_filter("Industria", "industry")
    countries = multiselect_filter("País", "country")
    plans = multiselect_filter("Plan", "plan_tier")
    if st.button("Actualizar datos"):
        load_data.clear()
        st.rerun()

view = filtered_data(df, industries, countries, plans)
churn_col = "is_churned"
mrr_col = "monthly_recurring_revenue"
mrr_values = pd.to_numeric(
    view[mrr_col] if mrr_col in view else pd.Series(0, index=view.index),
    errors="coerce",
).fillna(0)
if "is_active" in view.columns:
    mrr_values = mrr_values.where(view["is_active"].eq(1), 0)
churn_values = pd.to_numeric(
    view[churn_col] if churn_col in view else pd.Series(0, index=view.index),
    errors="coerce",
).fillna(0)
churn_total = churn_values.sum()
customer_count = len(view)
churn_rate = churn_total / customer_count * 100 if customer_count else 0
if "is_active" in view.columns:
    active_count = int(
        pd.to_numeric(view["is_active"], errors="coerce").fillna(0).sum()
    )
else:
    active_count = customer_count - churn_total
mrr_total = mrr_values.sum()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("MRR activo", format_currency(mrr_total))
kpi2.metric("Tasa de churn", f"{churn_rate:.1f}%")
kpi3.metric("Clientes activos", f"{active_count:,.0f}")
st.caption(f"{customer_count:,} clientes en la selección actual")

analysis_tab, simulator_tab = st.tabs(
    ["📈 Análisis de clientes", "🤖 Simulador de riesgo"]
)

with analysis_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Tasa de churn por industria")
        if {"industry", churn_col}.issubset(view.columns):
            industry_stats = view.groupby("industry", dropna=False)[churn_col].mean()
            industry_stats = industry_stats.mul(100).reset_index(
                name="Tasa de churn (%)"
            )
            fig = px.bar(
                industry_stats,
                x="industry",
                y="Tasa de churn (%)",
                color="Tasa de churn (%)",
                color_continuous_scale="Reds",
                labels={"industry": "Industria"},
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("La columna industry no está disponible en la tabla.")

    with right:
        st.subheader("Distribución del MRR")
        if mrr_col in view.columns:
            fig = px.histogram(
                view,
                x=mrr_col,
                nbins=25,
                color="plan_tier" if "plan_tier" in view.columns else None,
                labels={mrr_col: "MRR mensual", "plan_tier": "Plan"},
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("La columna monthly_recurring_revenue no está disponible.")

    st.subheader("Clientes en la selección")
    st.dataframe(view, width="stretch", hide_index=True)

    if os.getenv("ENABLE_GENAI_ENRICHMENT", "false").lower() == "true":
        st.subheader("Temas detectados en comentarios de churn")
        try:
            feedback_themes = load_feedback_themes()
        except (
            SQLAlchemyError,
            GoogleAPIError,
            DefaultCredentialsError,
            ValueError,
            RuntimeError,
            ImportError,
        ) as exc:
            st.info(
                "El mart de feedback se habilitará cuando se ejecuten el "
                "enriquecimiento de Vertex AI y el modelo dbt Gold."
            )
        else:
            if feedback_themes.empty:
                st.info("Aún no hay comentarios enriquecidos para mostrar.")
            else:
                feedback_fig = px.bar(
                    feedback_themes,
                    x="theme",
                    y="feedback_count",
                    color="sentiment",
                    labels={
                        "theme": "Tema",
                        "feedback_count": "Comentarios",
                        "sentiment": "Sentimiento",
                    },
                )
                st.plotly_chart(feedback_fig, width="stretch")

with simulator_tab:
    st.subheader("Simulador de riesgo de churn")
    st.write("Ingresa los datos de una cuenta para estimar su probabilidad de churn.")
    try:
        model = load_model()
    except (
        FileNotFoundError,
        OSError,
        ValueError,
        GoogleAPIError,
        DefaultCredentialsError,
        RuntimeError,
        ImportError,
    ) as exc:
        st.error("No se pudo cargar el modelo local o desde MODEL_GCS_URI.")
        st.exception(exc)
    else:
        validation_auc = getattr(model, "holdout_roc_auc_", None)
        if validation_auc is not None and validation_auc < 0.6:
            st.warning(
                f"El ROC-AUC de validación es {validation_auc:.2f}. "
                "La señal predictiva de los datos actuales es débil; "
                "interpreta este resultado como exploratorio, no como una "
                "decisión automática. Analízalo según el contexto, la población "
                "y el período evaluados, el objetivo de negocio y el costo de "
                "falsos positivos frente a falsos negativos; esos factores "
                "determinan el umbral de riesgo apropiado."
            )

        feature_names = list(getattr(model, "feature_names_in_", []))
        plan_features = [
            feature.removeprefix("plan_tier_")
            for feature in feature_names
            if feature.startswith("plan_tier_")
        ]
        available_plans = sorted(
            set(plan_features)
            | (
                set(df["plan_tier"].dropna().astype(str))
                if "plan_tier" in df
                else set()
            )
        )

        def median_default(column, fallback=0.0):
            if column not in df.columns:
                return fallback
            value = pd.to_numeric(df[column], errors="coerce").median()
            return float(value) if pd.notna(value) else fallback

        with st.form("risk_simulator"):
            selected_plan = st.selectbox(
                "Plan", available_plans or ["Basic", "Pro", "Enterprise"]
            )
            mrr = st.number_input(
                "MRR mensual",
                min_value=0.0,
                value=median_default("monthly_recurring_revenue", 150.0),
                step=10.0,
            )
            left, right = st.columns(2)
            feature_usage = left.number_input(
                "Usos de funcionalidades",
                min_value=0,
                value=int(median_default("total_feature_usage")),
            )
            usage_errors = right.number_input(
                "Errores de uso",
                min_value=0,
                value=int(median_default("total_usage_errors")),
            )
            support_tickets = left.number_input(
                "Tickets de soporte",
                min_value=0,
                value=int(median_default("total_support_tickets")),
            )
            resolution_time = right.number_input(
                "Resolución promedio (horas)",
                min_value=0.0,
                value=median_default("avg_resolution_time_hours"),
                step=1.0,
            )
            satisfaction = left.number_input(
                "Satisfacción promedio (0 a 5)",
                min_value=0.0,
                max_value=5.0,
                value=min(5.0, median_default("avg_satisfaction_score", 3.0)),
                step=0.1,
            )
            submitted = st.form_submit_button("Calcular riesgo")

        if submitted:
            input_row = {feature: 0 for feature in feature_names}
            numeric_inputs = {
                "monthly_recurring_revenue": mrr,
                "total_feature_usage": feature_usage,
                "total_usage_errors": usage_errors,
                "total_support_tickets": support_tickets,
                "avg_resolution_time_hours": resolution_time,
                "avg_satisfaction_score": satisfaction,
            }
            input_row.update(
                {
                    feature: value
                    for feature, value in numeric_inputs.items()
                    if feature in input_row
                }
            )
            plan_feature = f"plan_tier_{selected_plan}"
            if plan_feature in input_row:
                input_row[plan_feature] = 1
            model_input = pd.DataFrame([input_row], columns=feature_names)
            probability = float(model.predict_proba(model_input)[0][1])
            if probability >= 0.5:
                st.error(
                    f"Riesgo alto: probabilidad estimada de churn {probability:.1%}"
                )
                st.markdown(
                    "**Acciones sugeridas:** contactar al cliente, revisar tickets "
                    "abiertos y ofrecer una sesión de éxito o un plan de retención."
                )
            else:
                st.success(
                    f"Riesgo bajo: probabilidad estimada de churn {probability:.1%}"
                )
                st.markdown(
                    "**Acciones sugeridas:** mantener el seguimiento habitual y "
                    "reforzar el uso de las funciones de mayor valor."
                )
