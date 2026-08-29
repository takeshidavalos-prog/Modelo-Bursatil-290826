# 📈 Métricas de Valuación de Activos Financieros

Dashboard en Streamlit para calcular indicadores de desempeño y riesgo de
activos financieros (renta variable) a partir de datos de Yahoo Finance:
rentabilidad y volatilidad anualizada, Índice Sharpe, Beta, Correlación de
Pearson, Índice Treynor, CAPM, Alpha y Value at Risk (VaR).

## Contenido del repositorio

```
.
├── app.py                  # Aplicación Streamlit (todo el código)
├── requirements.txt        # Dependencias de Python
├── .streamlit/config.toml  # Tema visual (azul/negro, fintech)
└── README.md
```

## 1. Correr en local

```bash
git clone https://github.com/<tu-usuario>/<tu-repo>.git
cd <tu-repo>
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

La app abrirá en `http://localhost:8501`.

## 2. Subir el proyecto a GitHub

```bash
cd valuacion_activos
git init
git add .
git commit -m "Dashboard de métricas de valuación de activos"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/<tu-repo>.git
git push -u origin main
```

## 3. Desplegar en Streamlit Community Cloud

1. Entra a https://share.streamlit.io/ e inicia sesión con tu cuenta de GitHub.
2. Clic en **"New app"**.
3. Selecciona el repositorio, la rama (`main`) y el archivo principal `app.py`.
4. Clic en **"Deploy"**. Streamlit instalará automáticamente lo indicado en
   `requirements.txt`.
5. En unos minutos la app estará disponible en una URL pública tipo
   `https://<tu-app>.streamlit.app`.

## 4. Uso de la aplicación

En la barra lateral se configuran los inputs:

- **Número de activos** y **tickers** (formato Yahoo Finance, ej. `AAPL`, `WALMEX.MX`, `NVDA`).
- **Índice bursátil de referencia** (S&P 500, IPC, etc., o un ticker manual).
- **País de origen** y **fuente de la tasa libre de riesgo**: proxies de EE.UU.
  disponibles en Yahoo Finance (`^IRX`, `^TNX`, `^TYX`) o ingreso manual para
  cualquier otro país/mercado (p. ej. CETES 28 días para México).
- **Monto de capital**, **intervalo de confianza** y **plazo** para el cálculo del VaR.
- **Periodicidad de precios** (diaria, semanal, mensual) y **plazo histórico** a analizar
  (5 días, 3 meses, 6 meses, YTD, 12 meses, 1 año, 5 años).

Al presionar **"Calcular métricas"** la app descarga los precios de cierre
ajustado desde Yahoo Finance y muestra:

- Tabla resumen con todos los indicadores por activo (descargable en CSV).
- Detalle individual por activo con métricas y evolución del precio.
- Gráficas de dispersión y regresión lineal vs. el índice de referencia
  (con Beta y coeficiente de correlación).
- Pestaña de metodología con las fórmulas utilizadas.

## 5. Notas metodológicas

- Los retornos se calculan como variación porcentual simple entre precios
  de cierre ajustado, según la periodicidad elegida.
- La rentabilidad y volatilidad se anualizan con las fórmulas del documento
  anexo: `Retorno Anual = (V_final/V_inicial)^(1/n) - 1` y
  `Volatilidad Anual = σ√n`.
- El VaR se calcula como `VaR_α = μ + z_α·σ`, escalando μ y σ del periodo de
  precios elegido al horizonte de VaR solicitado (1 día o 1 mes).
- Yahoo Finance no publica tasas libres de riesgo para todos los países;
  si el mercado del activo no cuenta con un proxy disponible, se recomienda
  ingresar la tasa manualmente.

## Autor / uso académico

Basado en el documento *"E12 RD4 Indicadores de desempeño de activos
financieros"* (Mercados Financieros, Renta Variable), con fines académicos.
