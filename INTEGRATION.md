# Integrating into the existing Chakravyuh AI app

This module is additive. It does not change the existing Streamlit app's
impact scoring, map, or cascade junction detection screens.

## Steps

1. Copy `src/`, `artifacts/`, `app/closure_panel.py` into the existing
   Chakravyuh AI repository (keep the same relative paths so the imports
   in `closure_panel.py` resolve).

2. In the existing app's `app.py`, add a new tab or sidebar section:

```python
from app.closure_panel import render_closure_intelligence_panel

# inside whichever tab structure the existing app already uses, e.g.:
tab1, tab2, tab3 = st.tabs(["Map", "Impact scoring", "Closure intelligence"])

with tab3:
    render_closure_intelligence_panel()
```

3. Make sure `artifacts/` (the trained classifier, encoder, kNN index,
   scaler, and the two JSON lookup files) ships alongside the app, or
   re-run the four training scripts in the deployed environment before
   first use:

```bash
python src/features/build_features.py data/raw/astram_event_data.csv data/processed/model_df_full.csv
python src/models/train_classifier.py
python src/models/train_similarity.py
python src/inference/impact_index.py
python src/inference/cascade_indicator.py data/raw/astram_event_data.csv
```

4. If the existing app's impact-scoring screen wants to reuse the impact
   index formula from this module instead of maintaining a separate one,
   import directly:

```python
from src.inference.impact_index import impact_index
```

No other existing module needs to change. The closure intelligence panel
reads only from its own `artifacts/` directory and does not write to or
read from any state the existing app owns.
