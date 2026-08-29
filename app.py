"""
====================================================================
 E7 RD4 - Métricas de Valuación de Activos Financieros
 Dashboard Streamlit: Rentabilidad, Riesgo, CAPM y VaR
 Fuente de datos: Yahoo Finance (yfinance)
====================================================================

Cómo correr localmente:
    pip install -r requirements.txt
    streamlit run app.py

Cómo subir a GitHub y desplegar en Streamlit Community Cloud:
    Ver README.md
"""

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from scipy.stats import norm
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# 1. CONFIGURACIÓN GENERAL DE LA PÁGINA Y ESTILO (FINTECH)
# ============================================================

st.set_page_config(
    page_title="Métricas de Valuación de Activos",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Paleta Fintech: Azul / Negro / Blanco, tipografía Arial ---
AZUL_PRIMARIO = "#00AEEF"
AZUL_OSCURO = "#0B4F8A"
NEGRO_FONDO = "#0B0F1A"
NEGRO_PANEL = "#111827"
BLANCO = "#FFFFFF"
GRIS_CLARO = "#B8C2D1"
VERDE = "#00E396"
ROJO = "#FF4560"

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Arial&display=swap');

    html, body, [class*="css"], .stApp {{
        font-family: Arial, "Helvetica Neue", Helvetica, sans-serif !important;
        color: {BLANCO} !important;
    }}

    .stApp {{
        background: linear-gradient(180deg, {NEGRO_FONDO} 0%, #060810 100%);
    }}

    section[data-testid="stSidebar"] {{
        background-color: {NEGRO_PANEL};
        border-right: 1px solid {AZUL_PRIMARIO};
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: {BLANCO} !important;
        font-family: Arial, sans-serif !important;
        font-weight: 700 !important;
    }}

    .fintech-header {{
        background: linear-gradient(90deg, {NEGRO_FONDO} 0%, {AZUL_OSCURO} 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 10px;
        border: 1px solid {AZUL_PRIMARIO};
        margin-bottom: 1.2rem;
    }}
    .fintech-header h1 {{
        margin: 0;
        color: {BLANCO};
        letter-spacing: 0.5px;
    }}
    .fintech-header p {{
        margin: 0.3rem 0 0 0;
        color: {GRIS_CLARO};
        font-size: 0.95rem;
    }}

    div[data-testid="stMetric"] {{
        background-color: {NEGRO_PANEL};
        border: 1px solid {AZUL_PRIMARIO};
        border-radius: 10px;
        padding: 0.8rem 1rem;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {GRIS_CLARO} !important;
    }}
    div[data-testid="stMetricValue"] {{
        color: {AZUL_PRIMARIO} !important;
        font-family: Arial, sans-serif !important;
    }}

    .stDataFrame, .stTable {{
        background-color: {NEGRO_PANEL} !important;
    }}

    .stButton>button, .stDownloadButton>button {{
        background-color: {AZUL_PRIMARIO};
        color: {NEGRO_FONDO};
        font-weight: 700;
        border: none;
        border-radius: 6px;
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{
        background-color: {BLANCO};
        color: {NEGRO_FONDO};
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {NEGRO_PANEL};
        border-radius: 6px 6px 0 0;
        color: {GRIS_CLARO};
        padding: 8px 16px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {AZUL_OSCURO} !important;
        color: {BLANCO} !important;
    }}

    hr {{ border-color: {AZUL_OSCURO}; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="fintech-header">
        <h1>📈 Métricas de Valuación de Activos Financieros</h1>
        <p>Rentabilidad · Volatilidad · Sharpe · Treynor · Beta · CAPM · VaR &nbsp;|&nbsp;
        Datos: Yahoo Finance</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 2. PROXIES DE TASA LIBRE DE RIESGO (Yahoo Finance)
# ============================================================
# Yahoo Finance no publica tasas libres de riesgo para todos los
# países. Se ofrecen proxies para mercados con datos disponibles;
# para cualquier otro país de origen, el usuario puede ingresar
# la tasa manualmente (p.ej. CETES 28d para México, Bonos del
# Tesoro para otros mercados, etc.)

RF_PROXIES = {
    "Estados Unidos - T-Bill 13 semanas (^IRX)": "^IRX",
    "Estados Unidos - T-Note 10 años (^TNX)": "^TNX",
    "Estados Unidos - T-Bond 30 años (^TYX)": "^TYX",
    "Ingresar manualmente (cualquier país)": None,
}

INDICES_REFERENCIA = {
    "S&P 500 (Estados Unidos)": "^GSPC",
    "Dow Jones (Estados Unidos)": "^DJI",
    "Nasdaq 100 (Estados Unidos)": "^NDX",
    "IPC (México)": "^MXX",
    "Ibovespa (Brasil)": "^BVSP",
    "FTSE 100 (Reino Unido)": "^FTSE",
    "DAX (Alemania)": "^GDAXI",
    "Otro (escribir manualmente)": None,
}

PERIODICIDAD_MAP = {
    "Diaria": {"interval": "1d", "periodos_anio": 252, "dias_periodo": 1},
    "Semanal": {"interval": "1wk", "periodos_anio": 52, "dias_periodo": 5},
    "Mensual": {"interval": "1mo", "periodos_anio": 12, "dias_periodo": 21},
}

PLAZO_MAP = {
    "5 días": "5d",
    "3 meses": "3mo",
    "6 meses": "6mo",
    "YTD": "ytd",
    "12 meses": "1y",
    "1 año": "1y",
    "5 años": "5y",
}

PLAZO_VAR_MAP = {
    "1 día": 1,     # días calendario/hábiles equivalentes
    "1 mes": 21,    # ~21 días hábiles
}


# ============================================================
# 3. FUNCIONES DE DATOS Y CÁLCULO
# ============================================================

@st.cache_data(show_spinner=False, ttl=3600)
def descargar_precios(tickers, period, interval):
    """Descarga precios de cierre ajustado desde Yahoo Finance."""
    data = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
    )
    if data.empty:
        return pd.DataFrame()

    precios = pd.DataFrame()
    if isinstance(tickers, list) and len(tickers) > 1:
        for t in tickers:
            try:
                precios[t] = data[t]["Close"]
            except (KeyError, TypeError):
                pass
    else:
        col = tickers[0] if isinstance(tickers, list) else tickers
        precios[col] = data["Close"] if "Close" in data.columns else data[col]["Close"]

    return precios.dropna(how="all")


@st.cache_data(show_spinner=False, ttl=3600)
def descargar_tasa_libre_riesgo(ticker_rf):
    """Descarga la última tasa (%) publicada por Yahoo Finance para el proxy elegido."""
    try:
        hist = yf.Ticker(ticker_rf).history(period="5d")
        if hist.empty:
            return None
        ultima_tasa = hist["Close"].dropna().iloc[-1]
        return float(ultima_tasa) / 100.0  # a decimal anual
    except Exception:
        return None


def calcular_retornos(precios: pd.Series):
    """Retornos periódicos simples."""
    return precios.pct_change().dropna()


def retorno_anualizado(precios: pd.Series):
    """Retorno Anual = (Valor Final / Valor Inicial)^(1/n) - 1, n en años."""
    precios = precios.dropna()
    if len(precios) < 2:
        return np.nan
    v_inicial, v_final = precios.iloc[0], precios.iloc[-1]
    dias = (precios.index[-1] - precios.index[0]).days
    n = max(dias / 365.25, 1 / 365.25)
    if v_inicial <= 0:
        return np.nan
    return (v_final / v_inicial) ** (1 / n) - 1


def volatilidad_anualizada(retornos: pd.Series, periodos_anio: int):
    """Volatilidad Anual = sigma * sqrt(n)."""
    return retornos.std(ddof=1) * np.sqrt(periodos_anio)


def coeficiente_beta(ret_activo: pd.Series, ret_mercado: pd.Series):
    df = pd.concat([ret_activo, ret_mercado], axis=1).dropna()
    if len(df) < 2:
        return np.nan
    cov = np.cov(df.iloc[:, 0], df.iloc[:, 1])[0, 1]
    var_m = np.var(df.iloc[:, 1], ddof=1)
    if var_m == 0:
        return np.nan
    return cov / var_m


def correlacion_pearson(ret_activo: pd.Series, ret_mercado: pd.Series):
    df = pd.concat([ret_activo, ret_mercado], axis=1).dropna()
    if len(df) < 2:
        return np.nan
    return np.corrcoef(df.iloc[:, 0], df.iloc[:, 1])[0, 1]


def indice_sharpe(r_p, r_f, sigma_p):
    if sigma_p in (0, None) or np.isnan(sigma_p):
        return np.nan
    return (r_p - r_f) / sigma_p


def indice_treynor(r_a, r_f, beta_a):
    if beta_a in (0, None) or np.isnan(beta_a):
        return np.nan
    return (r_a - r_f) / beta_a


def capm(r_f, beta_i, r_m):
    return r_f + beta_i * (r_m - r_f)


def alpha_jensen(r_i, r_f, beta_i, r_m):
    return r_i - (r_f + beta_i * (r_m - r_f))


def calcular_var(retornos: pd.Series, capital: float, confianza: float,
                  horizonte_dias: int, dias_por_periodo: int):
    """
    VaR_alpha = mu + z_alpha * sigma   (fórmula del documento anexo)
    mu y sigma se escalan al horizonte de VaR solicitado (1 día / 1 mes)
    a partir de los retornos calculados con la periodicidad de precios
    elegida por el usuario.
    """
    mu_periodo = retornos.mean()
    sigma_periodo = retornos.std(ddof=1)

    # número de periodos (según periodicidad elegida) que componen el horizonte de VaR
    h = max(horizonte_dias / dias_por_periodo, 1e-9)

    mu_h = mu_periodo * h
    sigma_h = sigma_periodo * np.sqrt(h)

    nivel_significancia = 1 - confianza
    z = norm.ppf(nivel_significancia)  # valor z (típicamente negativo)

    var_periodo = mu_h + z * sigma_h          # pérdida esperada (negativa = pérdida)
    var_pct = -var_periodo                    # se expresa como % de pérdida (positivo)
    var_monto = var_pct * capital

    return {
        "nivel_significancia": nivel_significancia,
        "z": z,
        "var_pct": var_pct,
        "var_monto": var_monto,
        "mu_h": mu_h,
        "sigma_h": sigma_h,
    }


# ============================================================
# 4. BARRA LATERAL: INPUTS DEL USUARIO
# ============================================================

with st.sidebar:
    st.markdown("## ⚙️ Parámetros de Entrada")

    st.markdown("### 1. Activos a valuar")
    num_activos = st.number_input(
        "Número de activos a valuar", min_value=1, max_value=15, value=3, step=1
    )

    tickers_input = []
    cols_tickers = st.columns(1)
    default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META",
                        "JPM", "KO", "WMT", "V", "DIS", "NFLX", "BA", "XOM"]
    for i in range(int(num_activos)):
        t = st.text_input(
            f"Ticker del activo {i + 1}",
            value=default_tickers[i] if i < len(default_tickers) else "",
            key=f"ticker_{i}",
        ).strip().upper()
        if t:
            tickers_input.append(t)

    st.markdown("### 2. Índice bursátil de referencia")
    indice_label = st.selectbox("Índice de referencia", list(INDICES_REFERENCIA.keys()))
    if INDICES_REFERENCIA[indice_label] is None:
        indice_ticker = st.text_input("Ticker del índice (Yahoo Finance)", value="^GSPC").strip().upper()
    else:
        indice_ticker = INDICES_REFERENCIA[indice_label]

    st.markdown("### 3. Tasa libre de riesgo")
    pais_origen = st.text_input("País de origen de los activos", value="Estados Unidos")
    rf_label = st.selectbox("Fuente / proxy de tasa libre de riesgo", list(RF_PROXIES.keys()))
    if RF_PROXIES[rf_label] is None:
        tasa_libre_riesgo = st.number_input(
            "Tasa libre de riesgo anual (%)", min_value=0.0, max_value=100.0,
            value=5.0, step=0.05
        ) / 100.0
        rf_ticker = None
    else:
        rf_ticker = RF_PROXIES[rf_label]
        tasa_libre_riesgo = None  # se descarga más abajo

    st.markdown("### 4. Parámetros de VaR")
    monto_capital = st.number_input(
        "Monto de capital a invertir (VaR) $", min_value=0.0, value=100000.0, step=1000.0
    )
    intervalo_confianza = st.selectbox(
        "Intervalo de confianza", ["90%", "95%", "97.5%", "99%"], index=1
    )
    confianza_decimal = float(intervalo_confianza.replace("%", "")) / 100.0

    plazo_var_label = st.radio("Plazo para VaR", list(PLAZO_VAR_MAP.keys()), horizontal=True)

    st.markdown("### 5. Precios históricos")
    periodicidad_label = st.radio(
        "Periodicidad de precios", list(PERIODICIDAD_MAP.keys()), horizontal=True
    )
    plazo_calculo_label = st.selectbox("Plazo a calcular", list(PLAZO_MAP.keys()), index=4)

    st.markdown("---")
    calcular_btn = st.button("🚀 Calcular métricas", use_container_width=True)


# ============================================================
# 5. PROCESAMIENTO PRINCIPAL
# ============================================================

if calcular_btn:
    if not tickers_input:
        st.error("Ingresa al menos un ticker válido.")
        st.stop()
    if not indice_ticker:
        st.error("Ingresa un ticker válido para el índice de referencia.")
        st.stop()

    periodicidad = PERIODICIDAD_MAP[periodicidad_label]
    interval = periodicidad["interval"]
    periodos_anio = periodicidad["periodos_anio"]
    dias_periodo = periodicidad["dias_periodo"]
    period = PLAZO_MAP[plazo_calculo_label]
    horizonte_var_dias = PLAZO_VAR_MAP[plazo_var_label]

    with st.spinner("Descargando precios desde Yahoo Finance..."):
        todos_tickers = list(dict.fromkeys(tickers_input + [indice_ticker]))
        precios = descargar_precios(todos_tickers, period=period, interval=interval)

    if precios.empty:
        st.error(
            "No se pudieron descargar precios. Verifica los tickers, el plazo "
            "y la periodicidad seleccionados."
        )
        st.stop()

    faltantes = [t for t in todos_tickers if t not in precios.columns or precios[t].dropna().empty]
    if faltantes:
        st.warning(f"No se encontraron datos para: {', '.join(faltantes)}. Serán omitidos.")

    tickers_validos = [t for t in tickers_input if t in precios.columns and not precios[t].dropna().empty]
    if indice_ticker not in precios.columns or precios[indice_ticker].dropna().empty:
        st.error("No se pudieron obtener datos del índice de referencia. Intenta con otro ticker.")
        st.stop()
    if not tickers_validos:
        st.error("Ninguno de los tickers de activos tiene datos disponibles.")
        st.stop()

    # --- Tasa libre de riesgo ---
    if rf_ticker is not None:
        with st.spinner("Descargando tasa libre de riesgo..."):
            tasa_libre_riesgo = descargar_tasa_libre_riesgo(rf_ticker)
        if tasa_libre_riesgo is None:
            st.warning(
                "No fue posible descargar la tasa libre de riesgo desde Yahoo Finance. "
                "Se usará 0% temporalmente; ingrésala manualmente en la barra lateral."
            )
            tasa_libre_riesgo = 0.0

    ret_indice = calcular_retornos(precios[indice_ticker])
    r_m_anual = retorno_anualizado(precios[indice_ticker])

    resultados = []
    graficas = {}

    for tk in tickers_validos:
        precios_activo = precios[tk].dropna()
        ret_activo = calcular_retornos(precios_activo)

        r_i_anual = retorno_anualizado(precios_activo)
        vol_anual = volatilidad_anualizada(ret_activo, periodos_anio)
        beta_i = coeficiente_beta(ret_activo, ret_indice)
        corr_p = correlacion_pearson(ret_activo, ret_indice)
        sharpe = indice_sharpe(r_i_anual, tasa_libre_riesgo, vol_anual)
        treynor = indice_treynor(r_i_anual, tasa_libre_riesgo, beta_i)
        r_capm = capm(tasa_libre_riesgo, beta_i, r_m_anual)
        alpha = alpha_jensen(r_i_anual, tasa_libre_riesgo, beta_i, r_m_anual)
        var_res = calcular_var(
            ret_activo, monto_capital, confianza_decimal, horizonte_var_dias, dias_periodo
        )

        resultados.append({
            "Ticker": tk,
            "Rentabilidad Anualizada": r_i_anual,
            "Volatilidad Anualizada": vol_anual,
            "Índice Sharpe": sharpe,
            "Correlación Pearson": corr_p,
            "Beta": beta_i,
            "Índice Treynor": treynor,
            "Alpha (Jensen)": alpha,
            "CAPM (Retorno Esperado)": r_capm,
            "Tasa Libre de Riesgo": tasa_libre_riesgo,
            "Nivel de Significancia": var_res["nivel_significancia"],
            "Valor z": var_res["z"],
            "VaR %": var_res["var_pct"],
            "VaR $": var_res["var_monto"],
        })

        graficas[tk] = pd.concat(
            [ret_activo.rename(tk), ret_indice.rename(indice_ticker)], axis=1
        ).dropna()

    df_resultados = pd.DataFrame(resultados).set_index("Ticker")
    st.session_state["df_resultados"] = df_resultados
    st.session_state["graficas"] = graficas
    st.session_state["precios"] = precios
    st.session_state["indice_ticker"] = indice_ticker
    st.session_state["r_m_anual"] = r_m_anual
    st.session_state["config"] = {
        "pais_origen": pais_origen,
        "confianza": confianza_decimal,
        "plazo_var": plazo_var_label,
        "periodicidad": periodicidad_label,
        "plazo_calculo": plazo_calculo_label,
        "capital": monto_capital,
    }


# ============================================================
# 6. RESULTADOS
# ============================================================

if "df_resultados" in st.session_state:
    df_resultados = st.session_state["df_resultados"]
    graficas = st.session_state["graficas"]
    precios = st.session_state["precios"]
    indice_ticker = st.session_state["indice_ticker"]
    r_m_anual = st.session_state["r_m_anual"]
    cfg = st.session_state["config"]

    tab_resumen, tab_detalle, tab_graficas, tab_metodologia = st.tabs(
        ["📊 Resumen", "🔍 Detalle por Activo", "📉 Correlación y Regresión", "📚 Metodología"]
    )

    # --- TAB RESUMEN ---
    with tab_resumen:
        st.markdown(f"**Índice de referencia:** `{indice_ticker}` &nbsp;|&nbsp; "
                     f"**Retorno anualizado del índice:** {r_m_anual:.2%} &nbsp;|&nbsp; "
                     f"**País de origen:** {cfg['pais_origen']}")

        fmt = {
            "Rentabilidad Anualizada": "{:.2%}",
            "Volatilidad Anualizada": "{:.2%}",
            "Índice Sharpe": "{:.3f}",
            "Correlación Pearson": "{:.3f}",
            "Beta": "{:.3f}",
            "Índice Treynor": "{:.3f}",
            "Alpha (Jensen)": "{:.2%}",
            "CAPM (Retorno Esperado)": "{:.2%}",
            "Tasa Libre de Riesgo": "{:.2%}",
            "Nivel de Significancia": "{:.1%}",
            "Valor z": "{:.3f}",
            "VaR %": "{:.2%}",
            "VaR $": "${:,.2f}",
        }
        def resaltar_rentabilidad(col):
            # Resalta en azul degradado la columna de rentabilidad, sin depender
            # de matplotlib (background_gradient de pandas lo requiere y puede
            # no estar instalado en el entorno de despliegue).
            vals = col.astype(float)
            vmin, vmax = vals.min(), vals.max()
            rango = (vmax - vmin) or 1.0
            estilos = []
            for v in vals:
                intensidad = (v - vmin) / rango  # 0 a 1
                azul = int(60 + intensidad * (180 - 60))
                estilos.append(f"background-color: rgba(0, 120, {azul}, {0.15 + 0.45 * intensidad})")
            return estilos

        st.dataframe(
            df_resultados.style.format(fmt).apply(
                resaltar_rentabilidad, subset=["Rentabilidad Anualizada"]
            ),
            use_container_width=True,
            height=(len(df_resultados) + 1) * 38,
        )

        csv = df_resultados.to_csv().encode("utf-8")
        st.download_button(
            "⬇️ Descargar resultados (CSV)", data=csv,
            file_name="metricas_valuacion_activos.csv", mime="text/csv"
        )

        st.markdown("#### Comparativa entre activos")
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(
                df_resultados.reset_index(), x="Ticker", y="Rentabilidad Anualizada",
                color="Ticker", title="Rentabilidad Anualizada por Activo",
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig.update_layout(
                template="plotly_dark", paper_bgcolor=NEGRO_PANEL, plot_bgcolor=NEGRO_PANEL,
                font=dict(family="Arial", color=BLANCO), yaxis_tickformat=".1%",
            )
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = px.bar(
                df_resultados.reset_index(), x="Ticker", y="VaR $",
                color="Ticker", title=f"VaR $ por Activo (Capital: ${cfg['capital']:,.0f})",
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig2.update_layout(
                template="plotly_dark", paper_bgcolor=NEGRO_PANEL, plot_bgcolor=NEGRO_PANEL,
                font=dict(family="Arial", color=BLANCO),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # --- TAB DETALLE ---
    with tab_detalle:
        activo_sel = st.selectbox("Selecciona un activo", df_resultados.index.tolist())
        fila = df_resultados.loc[activo_sel]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rentabilidad Anualizada", f"{fila['Rentabilidad Anualizada']:.2%}")
        m2.metric("Volatilidad Anualizada", f"{fila['Volatilidad Anualizada']:.2%}")
        m3.metric("Beta", f"{fila['Beta']:.3f}")
        m4.metric("Correlación Pearson", f"{fila['Correlación Pearson']:.3f}")

        m5, m6, m7, m8 = st.columns(4)
        m5.metric("Índice Sharpe", f"{fila['Índice Sharpe']:.3f}")
        m6.metric("Índice Treynor", f"{fila['Índice Treynor']:.3f}")
        m7.metric("CAPM (Retorno Esperado)", f"{fila['CAPM (Retorno Esperado)']:.2%}")
        m8.metric("Alpha (Jensen)", f"{fila['Alpha (Jensen)']:.2%}")

        st.markdown("##### Value at Risk (VaR)")
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Nivel de Significancia", f"{fila['Nivel de Significancia']:.1%}")
        v2.metric("Valor z", f"{fila['Valor z']:.3f}")
        v3.metric("VaR %", f"{fila['VaR %']:.2%}")
        v4.metric("VaR $", f"${fila['VaR $']:,.2f}")

        st.markdown("##### Evolución del precio")
        fig_precio = go.Figure()
        fig_precio.add_trace(go.Scatter(
            x=precios.index, y=precios[activo_sel], mode="lines",
            line=dict(color=AZUL_PRIMARIO, width=2), name=activo_sel
        ))
        fig_precio.update_layout(
            template="plotly_dark", paper_bgcolor=NEGRO_PANEL, plot_bgcolor=NEGRO_PANEL,
            font=dict(family="Arial", color=BLANCO), height=350,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_precio, use_container_width=True)

    # --- TAB GRAFICAS DE CORRELACION Y REGRESION ---
    with tab_graficas:
        st.markdown("#### Correlación y regresión vs. índice de referencia")
        activo_g = st.selectbox(
            "Selecciona un activo para graficar", df_resultados.index.tolist(), key="graf_sel"
        )
        datos = graficas[activo_g]
        x = datos[indice_ticker].values
        y = datos[activo_g].values

        if len(x) > 1:
            pendiente, intercepto = np.polyfit(x, y, 1)
            x_line = np.linspace(x.min(), x.max(), 100)
            y_line = pendiente * x_line + intercepto
            r = np.corrcoef(x, y)[0, 1]

            fig_reg = go.Figure()
            fig_reg.add_trace(go.Scatter(
                x=x, y=y, mode="markers", name="Retornos",
                marker=dict(color=AZUL_PRIMARIO, size=7, opacity=0.75)
            ))
            fig_reg.add_trace(go.Scatter(
                x=x_line, y=y_line, mode="lines", name="Regresión lineal",
                line=dict(color=VERDE, width=3)
            ))
            fig_reg.update_layout(
                title=f"{activo_g} vs {indice_ticker}  |  β = {pendiente:.3f} · r = {r:.3f}",
                xaxis_title=f"Retorno {indice_ticker}",
                yaxis_title=f"Retorno {activo_g}",
                template="plotly_dark", paper_bgcolor=NEGRO_PANEL, plot_bgcolor=NEGRO_PANEL,
                font=dict(family="Arial", color=BLANCO), height=480,
                xaxis_tickformat=".1%", yaxis_tickformat=".1%",
            )
            st.plotly_chart(fig_reg, use_container_width=True)
        else:
            st.info("No hay suficientes datos para graficar la regresión.")

    # --- TAB METODOLOGIA ---
    with tab_metodologia:
        st.markdown("#### Fórmulas utilizadas")
        st.latex(r"\text{Retorno Anual} = \left(\frac{\text{Valor Final}}{\text{Valor Inicial}}\right)^{1/n} - 1")
        st.latex(r"\text{Volatilidad Anual} = \sigma \sqrt{n}")
        st.latex(r"\text{Índice Sharpe} = \frac{R_p - R_f}{\sigma_p}")
        st.latex(r"\text{Índice Treynor} = \frac{R_a - R_f}{\beta_a}")
        st.latex(r"\beta = \frac{\mathrm{Cov}(R_i, R_m)}{\sigma_m^2}")
        st.latex(r"\alpha = R_i - [R_f + \beta_i (R_m - R_f)]")
        st.latex(r"R_i = R_f + \beta_i (R_m - R_f) \quad \text{(CAPM)}")
        st.latex(r"\mathrm{VaR}_\alpha = \mu + z_\alpha \sigma")
        st.markdown(
            """
            - **n**: número de años del periodo analizado.
            - **σ**: desviación estándar de los retornos periódicos (diarios, semanales o mensuales).
            - **R_p / R_a / R_i**: retorno anualizado del activo o cartera.
            - **R_f**: tasa libre de riesgo anual (Yahoo Finance o manual).
            - **R_m**: retorno anualizado del índice de referencia.
            - **z_α**: valor crítico de la normal estándar para el nivel de significancia elegido.
            - El **VaR** se escala del periodo de precios elegido al plazo de VaR (1 día o 1 mes)
              mediante `μ_h = μ·h` y `σ_h = σ·√h`, con *h* el número de periodos equivalentes al horizonte.
            """
        )
else:
    st.info("👈 Configura los parámetros en la barra lateral y presiona **Calcular métricas**.")
