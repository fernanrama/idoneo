# MCP público de MyInvestor: herramientas y mapeo al perfil del cliente

> Hechos verificados el 8 nov 2026. Los datos de catálogo pueden cambiar.

Fecha: 2026-11-08. Endpoint: `https://mcp.myinvestor.es/mcp` (Streamable HTTP, sin auth, responde en SSE).
Servidor `myinvestor` v2.0.0, protocolo 2025-06-18. **No devuelve `Mcp-Session-Id`** (sin estado); `notifications/initialized` → HTTP 202.
Catálogo: 2.410 fondos, 13 carteras robo (6 MyInvestor + 7 Finanbest), ~1.050 ETFs, ~6.000 acciones.

Consultado a mano desde el portátil de Alex (5 llamadas de exploración). Los JSON en bruto no se suben al repo: los términos prohíben redistribuir los datos del catálogo.

## ⚠️ Condiciones de uso (lo más importante)

`https://mcp.myinvestor.es/es/terms` permite el uso personal desde Claude, ChatGPT, Perplexity y Grok, y "tolera" el uso razonable desde agentes de desarrollo con IA. **Prohíbe** expresamente:
- el acceso automatizado o programático (scripts, bots, scrapers, crawlers);
- la extracción o indexación masiva del catálogo, fichas o series de precios;
- reutilizar o redistribuir los datos, o construir con ellos bases de datos o productos derivados.

Consecuencia: un backend de la app del hackathon que llame al MCP por código, o una caché local del catálogo, incumple los términos salvo permiso explícito de MyInvestor (preguntar a la organización/patrocinador). La vía permitida es usarlo como conector de Claude en la conversación. Paré tras 5 llamadas de exploración.

## Herramientas (12)

| Herramienta | Parámetros (req. en negrita) | Devuelve |
|---|---|---|
| `search_funds` | `query` str≤200, `isins` str[1-10], `asset_type` enum{Renta Variable, Renta Fija, Monetario, Mixto}, `geography` str, `sector` str, `management_type` enum{Active, Index/Passive}, `market_cap` str, `fixed_income_type` str, `credit_quality` str, `currency` str, `distributing` bool, `esg_only` bool, `max_ter` num≥0, `max_risk` int 1-7, `min_return_1y` num, `min_return_3y` num, `order_by` enum{ytd_desc, return_1y_desc, return_3y_desc, return_5y_desc, ter_asc, risk_asc, volatility_3y_asc, relevance}, `limit` int ≤10 | `total_found`, `funds[]` con ficha completa (ver abajo). **Máx. 10, sin paginación/offset.** |
| `get_funds` | **`isins`** str[1-10] | `funds[]` ficha completa + `price_series` (sin widget) |
| `list_facets` | `dimensions` enum[]{asset_type, geography, sector, management_type, management_company, currency, fixed_income_type, region}, `top` int 1-500, `min_count` int | `total_funds`, `facets{dim:{total, values[{value,count}]}}` |
| `resolve_funds` | **`names`** str[1-5] | `groups[{query, confidence: high/ambiguous, ambiguity_reason, candidates[{isin,name,manager,asset_type,currency,dist_acc,ter,return_3y}]}]` |
| `compare_instruments` | **`refs`** str[2-3] (ISIN fondo / ticker o ISIN ETF-acción) | `items[]` con ficha por tipo |
| `search_portfolios` | `query`, `profile` enum{CONSERVADOR, MODERADO, DINAMICO, AGRESIVO, MUY_AGRESIVO}, `risk_max` int **0-5** (escala propia, no SRRI 1-7), `family` enum{myinvestor, finanbest}, `management` enum{passive, active, mixed}, `order_by` enum{relevance, ytd, profitability, cumulitive_profitability, risk, name}, `limit` ≤10 | `portfolios[{name_id, profile, risk, family, management, variable_income, fixed_income, ytd, profitability, composition[], funds[{isin,...,percentage}], commissions[{tier,min_capital,max_capital,ter,custody,management}], historic_yearly[]}]` |
| `compare_portfolios` | **`refs`** str[2-3] (≥1 cartera) | igual que arriba, por ítem |
| `backtest_portfolio` | **`holdings`** [{`ref`, **`weight_pct`** 0-100}] ≤10 | serie acumulada, rentab. anual/mensual, volatilidad, máx. caída, Sharpe, composición. Pesos constantes, ≤5 años, sin comisiones de custodia |
| `search_etfs` | `query`, `sector`, `geography`, `currency`, `asset_type`, `management_type`, `market_cap`, `max_ter`, `min_return_1y/3y`, `include_leveraged` bool, `order_by` enum{r_ytd_desc, r_1y_desc, r_3y_desc, r_5y_desc, ter_asc, aum_desc, vol_3y_asc, relevance}, `limit` | `instruments[]`: ticker, isin, ter, aum, n_positions, distribution_type, r_*, vol_*, markets[]… **sin SRRI ni SFDR** |
| `search_stocks` | `query`, `sector`, `geography`, `currency`, `min_return_1y/3y`, `min_dividend_yield`, `min_marketcap`, `order_by`, `limit` | igual (per_ttm, dividend_yield, marketcap…) |
| `get_instruments` | **`tickers`** str[1-10] | ficha completa ETF/acción |
| `list_instrument_facets` | `product_type` enum{etf, stock}, `dimensions` enum[]{geography, sector, currency, asset_type, management_type, management_company}, `top`, `min_count` | recuentos |

**Campos de la ficha de fondo** (`search_funds`/`get_funds`): isin, name, management_company, currency, asset_type, geography, sector_or_theme, management_type, fixed_income_type, fixed_income_term, fixed_income_credit_quality, market_capitalisation, style, **sustainability_article** (6/8/9), distributing, **ter**, management_fee, performance_fee, **risk_indicator** (SRRI 1-7), volatility_1y/3y/5y, ytd, return_1y/3y/5y, return_past_1y…5y, alloc_equity/bond/cash/other, market, operation_mode, nav, nav_date, inception_date, **min_initial, min_followup, min_redemption, cutoff_time, subscription_lag_days, redemption_lag_days, nav_lag_days**, description, warning_text, top_sectors[], top_regions[], price_series.

## ¿Existen los campos pedidos?

| Concepto | Fondos | ETFs/acciones | Carteras |
|---|---|---|---|
| Riesgo SRI 1-7 | ✅ filtro `max_risk`, campo `risk_indicator`, orden `risk_asc` | ❌ solo volatilidad (`vol_3y_asc`) | ⚠️ `risk_max` 0-5 + `profile` (pueden divergir) |
| ESG / SFDR | ⚠️ filtro `esg_only` = art. 8 **o** 9 (no distingue); campo `sustainability_article` sí distingue | ❌ | solo por nombre ("Sostenible") |
| Horizonte | ❌ no existe. Indirecto: `fixed_income_term` (p.ej. "Corto plazo", solo salida), SRRI, volatilidad, `asset_type=Monetario` | ❌ | `profile` |
| Liquidez | ❌ sin filtro. Campos de salida: `redemption_lag_days`, `subscription_lag_days`, `cutoff_time`, `min_redemption` | cotizan (diaria) | ❌ |
| Divisa | ✅ filtro `currency` (EUR 2.009, USD 350, GBP 29, CHF 13, JPY 7…) | ✅ `currency` | por fondo subyacente |

Ejemplo verificado: `search_funds{asset_type:"Renta Fija", max_risk:3, esg_only:true, max_ter:0.5, currency:"EUR", order_by:"ter_asc"}` → 23 fondos; top: iShares Screened Global Corp Bond (SRRI 3, art. 8, TER 0,14%, reembolso 3 días), DWS Euro Ultra Short (SRRI 1, art. 8, 0,15%, 2 días), Groupama Ultra Short Term (SRRI 1, art. 8, 0,18%, 1 día).

## Mapeo perfil del cliente → filtros

| Restricción | En el servidor | Post-filtro en nuestro lado (sobre la ficha) |
|---|---|---|
| Riesgo máximo | `max_risk` (fondos), `risk_max`/`profile` (carteras) | ETFs: umbral de `vol_3y` como proxy |
| Horizonte | — | Regla nuestra: horizonte → SRRI máx. y mezcla de `asset_type`; corto plazo → Monetario / RF `fixed_income_term="Corto plazo"` |
| Liquidez | — | `redemption_lag_days ≤ N`, `cutoff_time`, `min_redemption` |
| Coste | `max_ter`, `order_by: ter_asc` | `performance_fee` nulo/0; carteras: tramo de `commissions` según capital |
| Exclusiones ESG | `esg_only` | Solo art. 9: `sustainability_article == 9` |
| Exclusiones sectoriales (armas, tabaco…) | ❌ solo hay filtro de inclusión `sector` | excluir por `sector_or_theme` y `top_sectors[].pct`; no hay datos de holdings concretos |
| Divisa / sin riesgo divisa | `currency: "EUR"` | los "EUR Hedged" se detectan solo por el nombre |
| Alto rendimiento | `credit_quality: "Alto rendimiento"` (inclusión) | excluir por `fixed_income_credit_quality` |
| Distribución/acumulación | `distributing` | — |
| Importe mínimo | — | `min_initial` (string "1.00 EUR", hay que parsear) |

## Rarezas a tener en cuenta
- `management_type` se envía en inglés (`Active`, `Index/Passive`) pero la ficha y las facetas lo devuelven en español (`Activo`, `Índice/pasivo`).
- Tope de 10 resultados sin paginación: imposible recorrer el catálogo (y además lo prohíben los términos). Hay que filtrar mucho en el servidor y post-filtrar esos 10.
- `asset_type` puede ser compuesto ("Mixto, Renta Fija"); `fixed_income_type` también ("Agregado, Corporativo").
- Las instrucciones del servidor piden no mostrar al usuario nombres de parámetros ni ISIN.
