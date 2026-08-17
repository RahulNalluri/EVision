# EV Energy Consumption Dataset

- Source: Kaggle
- Owner: `ziya07`
- Slug: `ziya07/ev-energy-consumption-dataset`
- License: CC0: Public Domain
- URL: https://www.kaggle.com/datasets/ziya07/ev-energy-consumption-dataset
- Records used by EVision: 5,000
- Target: `Energy_Consumption_kWh`

The CSV in `files/` is the unmodified Kaggle source. EVision creates its model-ready table with:

```powershell
python -m backend.data.prepare_kaggle_dataset
```

To download it again with the Kaggle CLI:

```powershell
kaggle datasets download -d ziya07/ev-energy-consumption-dataset -p data/raw/kaggle_ev_energy
Expand-Archive data/raw/kaggle_ev_energy/ev-energy-consumption-dataset.zip data/raw/kaggle_ev_energy/files -Force
```
