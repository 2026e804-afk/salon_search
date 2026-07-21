# Kanazawa Rain and Snow Explorer

Streamlit application for comparing monthly precipitation, rainy days, temperature, snowfall, and snow depth at the JMA Kanazawa station from 2015 through 2025.

## Files required for deployment

- `app.py`
- `kanazawa_weather_processed.csv`
- `requirements.txt`
- `.streamlit/config.toml`

## Local run

```bash
streamlit run app.py
```

## Streamlit Community Cloud

1. Create a GitHub repository and place every file in this directory at the repository root.
2. In Streamlit Community Cloud, select the repository, branch, and `app.py`.
3. Deploy the app and wait until all charts load.
4. Test the winter filter and the annual-comparison tab.
5. Submit the resulting `https://...streamlit.app` URL to Manaba.

Data source: Japan Meteorological Agency, Past Weather Data Search, Kanazawa station (block 47605).
