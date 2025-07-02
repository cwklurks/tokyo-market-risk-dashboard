# 🏯 Tokyo Market Risk Dashboard

> **A lightweight, Palantir-style prototype demonstrating real-time risk intelligence for Tokyo’s financial markets.**

## Why it matters

Tokyo’s capital markets sit on the world’s most active seismic zone.  This dashboard fuses live earthquake feeds with market, volatility and network analytics to illustrate how Palantir-grade data fusion can drive faster, clearer decisions for Japanese institutions.

### Key capabilities

- **Integrated data pipeline** – live P2PQuake, Yahoo Finance & BoJ endpoints with caching/fallback.
- **Graph & risk engines** – NetworkX contagion graphs + Black-Scholes pricing extended for seismic shocks.
- **Decision support** – automated action queue, bilingual (EN/JP) UI inspired by Foundry/Gotham UX.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```
Then visit `http://localhost:8501` in your browser.

## Repository layout

```text
├── app.py               # Streamlit front-end
├── config.py            # Endpoints, colours, thresholds
├── analytics/           # Risk engines  
│   ├── black_scholes.py     # Seismic-aware option pricing  
│   ├── risk_engine.py       # Integrated risk scoring  
│   └── network_analysis.py  # Graph analytics  
├── data/                # Live data providers  
│   ├── market_data.py       # Yahoo Finance wrapper  
│   └── earthquake_data.py   # P2PQuake parser  
├── ui/components.py     # Re-usable Streamlit widgets  
└── .streamlit/          # Theme config
```

## Palantir alignment

| Platform pillar | Demonstrated in this repo |
| --------------- | ------------------------- |
| **Foundry – data fusion** | Multi-source ingest & schema-on-read |
| **Gotham – graph analytics** | Risk network & contagion paths |
| **Apollo – decision layer** | Auto-generated mitigation queue + audit trail |

## Next steps

- Build ML forecasting engine (new `analytics/predictive_engine.py`)
- Containerise for Foundry workshop deployment
- Expand data ontology (transport, supply-chain, weather)

---

Built by a high-school data-engineering enthusiast – eager to see how Palantir Japan scales ideas like this to enterprise reality.
