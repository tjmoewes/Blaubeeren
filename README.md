# Blueberry Costa Rica — modelo Black–Litterman espacial

Aplicación básica en Python/Streamlit para priorizar áreas candidatas para la plantación de moras azules en Costa Rica. El modelo trata cada área candidata como un “activo” y combina:

1. un prior agronómico transparente, construido con variables normalizadas entre 0 y 1;
2. views relativas o absolutas del usuario;
3. una matriz de covarianzas regularizada para evitar resultados inestables;
4. una asignación con límites de concentración y hectáreas disponibles.

El resultado es una herramienta de priorización, no una certificación de aptitud agronómica. Antes de invertir deben verificarse en campo el drenaje, la calidad del agua, el pH, la disponibilidad legal del predio, la logística y la respuesta varietal. Las moras azules requieren manejo técnico intensivo; una puntuación alta no sustituye un estudio de suelo ni un diseño de riego.

## Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

La aplicación abre con datos demostrativos incluidos en `data/sample_candidates.csv`. Estos datos son sintéticos para probar el código; no representan mediciones reales de predios.

## Estructura de datos

El archivo de áreas debe ser CSV y contener:

| Campo | Unidad / rango | Interpretación |
|---|---:|---|
| `candidate_id` | texto | Identificador único |
| `canton`, `province` | texto | Ubicación administrativa |
| `latitude`, `longitude` | grados decimales | Coordenadas del punto o centroide |
| `area_ha` | hectáreas | Área potencialmente utilizable |
| `climate_score` | 0–1 | Compatibilidad climática |
| `elevation_score` | 0–1 | Compatibilidad de elevación |
| `soil_score` | 0–1 | Suelo, pH, textura, drenaje y materia orgánica |
| `water_score` | 0–1 | Disponibilidad y calidad potencial del agua |
| `slope_score` | 0–1 | Facilidad de establecimiento y mecanización |
| `access_score` | 0–1 | Acceso, distancia a caminos y centros de acopio |
| `legal_score` | 0–1 | Ausencia de restricciones legales o ambientales |

Los scores deben construirse fuera del modelo a partir de datos geoespaciales y reglas agronómicas explícitas. Para cualquier variable donde un valor alto sea desfavorable —por ejemplo, pendiente, distancia o riesgo de restricción— conviértala antes a un score favorable entre 0 y 1.

El archivo de views debe contener:

| Campo | Ejemplo | Interpretación |
|---|---|---|
| `view_id` | `v1` | Identificador |
| `view_type` | `relative` / `absolute` | Tipo de view |
| `asset_a` | `CR-01` | Área principal |
| `asset_b` | `CR-02` o vacío | Área de comparación; vacío para view absoluta |
| `q` | `0.08` | Diferencia esperada o score esperado |
| `confidence` | `0.70` | Confianza entre 0 y 1 |

Ejemplo: `relative, CR-01, CR-02, 0.08, 0.70` expresa que CR-01 debería superar a CR-02 en 0.08 unidades de score. Una view absoluta sobre CR-01 se expresa dejando `asset_b` vacío.

## Datos públicos recomendados

El repositorio no descarga automáticamente rásteres ni datos administrativos: así se evita ocultar cambios de versión, licencias o fallas de APIs. La siguiente tabla indica fuentes públicas que pueden convertirse en los campos del CSV:

| Fuente | Uso recomendado | Enlace |
|---|---|---|
| WorldClim | Temperatura mínima/máxima y precipitación mensual; normales y series históricas | [WorldClim](https://worldclim.org/data/monthlywth.html) |
| NASA POWER | Validación climática y series meteorológicas por coordenada | [NASA POWER Docs](https://power.larc.nasa.gov/docs/) |
| ISRIC SoilGrids | pH, carbono orgánico, textura, densidad y CEC; incluir la incertidumbre | [SoilGrids](https://docs.isric.org/globaldata/soilgrids/index.html) |
| NASADEM/SRTM | Elevación y pendiente derivada | [NASA Earthdata](https://www.earthdata.nasa.gov/data/catalog/lpcloud-nasadem-001) |
| OpenStreetMap | Acceso vial, distancias y conectividad logística | [OpenStreetMap](https://www.openstreetmap.org/) |
| SINAC/MINAE | Áreas silvestres protegidas y restricciones ambientales | [SINAC](https://www.sinac.go.cr/ES/norasppne/Paginas/default.aspx) |
| SNIT | Capas territoriales y ambientales de Costa Rica | [SNIT](https://www.snitcr.go.cr/) |

Conserve en un archivo de metadatos la fecha de descarga, resolución espacial, unidad, transformación aplicada, versión y licencia de cada capa. No mezcle resoluciones sin documentarlo. SoilGrids publica incertidumbre de predicción; conviene penalizar `soil_score` o reducir la confianza de la view cuando dicha incertidumbre sea alta.

## Interpretación del Black–Litterman

La implementación usa una adaptación deliberadamente sencilla para un problema espacial:

* `prior`: score agronómico ponderado por el usuario;
* `Sigma`: covarianza entre áreas, derivada de sus perfiles de variables y regularizada;
* `P`, `Q`, `Omega`: views, magnitud de la view y su incertidumbre según la confianza indicada;
* `posterior`: prior actualizado por las views.

La covarianza aquí mide similitud y dependencia del perfil de las áreas, no volatilidad financiera observada. Por ello, el resultado debe leerse como ranking/selección bajo incertidumbre, no como un rendimiento financiero esperado. La asignación final limita la concentración por área y respeta el área disponible.

## Limitaciones importantes

* No incorpora precio, rendimiento, costes, agua concesionada, enfermedades, variedad, mano de obra ni riesgo de mercado.
* No debe utilizarse para decidir compra de tierras sin verificación legal y agronómica.
* La geolocalización de un centroide no prueba que toda el área sea homogénea.
* El Black–Litterman no elimina el riesgo de datos sesgados ni la incertidumbre de cambio climático.

## Pruebas

```bash
pytest -q
```
