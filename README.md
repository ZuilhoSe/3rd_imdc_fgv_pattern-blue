# 3rd_imdc_fgv_pattern-blue

**3rd Infodengue–Mosqlimate Dengue Challenge (IMDC 2026)**
Tracks: Dengue — State level (mandatory) and City level (optional).

## Overview

The model forecasts weekly dengue cases for a full season
(epidemiological week 41 of one year to EW40 of the next) for all Brazilian
states except Espírito Santo (mandatory track) and for the 15 selected
municipalities (optional city track).

It follows a **two-stage, parameter-based** design:

1. **Learning epidemic descriptors.** A single global Temporal Fusion
   Transformer (TFT) is trained across all municipalities. Given 52 weeks of
   epidemiological and climatic history, it predicts the parameters of the
   Richards curve that the [Episcanner](https://api.mosqlimate.org/) pipeline
   fits to each epidemic season. The target is **shifted by one season**, so
   from data available up to EW25 of year *Y* the model predicts the descriptors
   of the upcoming *Y*/*Y+1* season.
2. **Reconstructing the weekly curve.** The predicted parameters are turned
   into a weekly incidence curve through the Richards equation (see
   *Predictive Uncertainty*). State-level forecasts are obtained by summing the
   reconstructed municipal curves within each state.

---

## Team and Contributors

- **Team leader**: Zuilho Segundo, segundozuilho@gmai.com
- **Institution**: FGV EMAp
- **Contributors**: Zuilho Segundo, Iasmim Ferreira, Flávio Codeço

| Name           | Institution | Country | Role        |
|----------------|-------------|---------|-------------|
| Zuiho Segundo  | FGV EMAp    | Brazil  | Team Leader |
| Iasmim Almeida | FGV EMAp    | Brazil  | Advisor     |
| Flávio Codeço  | FGV EMAp    | Brazil  | Professor   |


---

## Repository Structure

```
Pattern-Blue/
├── README.md
├── pyproject.toml                # Poetry project + dependency declarations
├── poetry.lock                   # locked dependency versions (reproducibility)
├── LICENSE
├── .gitignore
├── .gitattributes
├── data/
│   ├── raw/                      # inputs from the Mosqlimate FTP/API + external open sources
│   └── processed/                # model-ready tables (e.g. dataset_tft_completo.parquet)
├── Demo Notebooks/               # official platform demos, kept for reference
│   ├── Python demo.ipynb
│   ├── R demo.Rmd
│   ├── R demo.nb.html
│   ├── example_prediction.csv
│   └── example_prediction2.csv
├── notebooks/
│   ├── preprocess_infodengue.ipynb    # builds the epidemiological/climate base table
│   ├── preprocess_shape_files.ipynb   # spatial attributes
│   ├── apply_2026.ipynb               # data preparation for the 2026 challenge
│   └── bagunca_graficos.ipynb         # exploratory plots (scratch)
├── reports/
│   └── images/
│       └── target_distributions.png
├── img/
└── src/
    ├── train.py                  # TFT training (pytorch-forecasting + Lightning)
    ├── models.py                 # model/architecture definitions and helpers
    ├── run_inference.py          # checkpoint -> Episcanner/Richards parameter quantiles per municipality
    ├── build_submissions.py      # parameters -> weekly curves -> validated submission CSVs (city + state)
    ├── imdc_submission.py        # Richards reconstruction, Monte Carlo uncertainty, formatting & validation
    ├── upload.py                 # uploads validated CSVs to the platform via mosqlient
    ├── models/                   # saved checkpoints (e.g. checkpoints/tft-epoch=08-val_loss=194.65.ckpt)
    ├── outputs/                  # generated parameter quantiles + submission CSVs
    └── lightning_logs/           # training logs (TensorBoard)
```

---

## Libraries and Dependencies

- `python` 3.11
- `torch`, `lightning` (PyTorch Lightning)
- `pytorch-forecasting` (TFT, `TimeSeriesDataSet`, `QuantileLoss`, `MultiLoss`, `GroupNormalizer`)
- `pandas`, `numpy`, `pyarrow` (parquet I/O)
- `epiweeks` (MMWR/Brazilian epidemiological-week ↔ date conversion)
- `giotto-tda` (or `ripser`) — rolling persistent-homology (TDA) features on incidence
- `mosqlient` (≥ 2.5) — platform data access and prediction upload
- `python-dotenv` — loads the platform `API_KEY` from a `.env` file

Install:

```bash
poetry install          # creates the virtualenv and installs from poetry.lock
poetry run python -V     # sanity check
```

---

## Data and Variables

All data are open and cover every Brazilian state. Epidemiological, climate and
Episcanner data come from the **Mosqlimate FTP/API**; the remaining sources are
public and are shared with the organizers (see *Data Usage Restriction*).

**Sources**

| Source | Provider                        | Used for |
| --- |---------------------------------| --- |
| Weekly dengue cases (`casos`) | Infodengue / Mosqlimate         | target reconstruction input; `incidence` |
| Climate time series (`temp_med`, `precip_med`, `rel_humid_med`) | Copernicus ERA5 via Mosqlimate  | model inputs |
| Seasonal climate forecast (`forecast_temp_med`, `forecast_umid_med`, `forecast_precip_tot`) | Mosqlimate                      | known future covariates |
| Ocean/climate indices (`enso`, `iod`, `pdo`) | NOAA (monthly)                  | engineered covariates |
| Population by municipality/year | IBGE                            | `log_pop` |
| Environmental descriptors (`koppen`, `biome`) | Mosqlimate            | static categoricals |
| Health regions (`macroregion_name`, `regional_name`) | Ministry of Health / Mosqlimate | static categoricals |
| Episcanner Richards parameters (`R0`, `peak_week`, `total_cases`, `alpha`, `beta`, `gamma`) | Mosqlimate Episcanner           | **prediction targets** |

**Engineered variables**

- Temporal: `time_idx`, `week_of_year`, `week_cycle` (season-centered so EW41→week 1),
  `sin_week_cycle`, `cos_week_cycle`.
- Epidemiological: `incidence` = `casos` / population × 100,000.
- Topological (TDA): `tda_entropy_H0/H1`, `tda_amplitude_H0/H1` from rolling
  persistent homology of the incidence series.

**Variable roles in the TFT**

- **Static categoricals:** `uf`, `koppen`, `biome`, `macroregion_name`
- **Time-varying known reals:** `time_idx`, `week_cycle`, `sin_week_cycle`,
  `cos_week_cycle`, `log_pop`, `forecast_temp_med`, `forecast_precip_tot`
- **Time-varying unknown reals:** `casos`, `incidence`, `temp_med`,
  `precip_med`, `rel_humid_med`
- **Targets:** `R0`, `peak_week`, `log_total_cases`, `alpha`, `beta`, `gamma`
  (of these, only `total_cases`, `alpha`, `beta`, `peak_week` are needed for
  reconstruction — `R0` and `gamma` are deterministic functions of `alpha` and
  the growth rate and are therefore redundant).

> The pipeline also derives ocean indices and TDA features; document precisely
> which of these entered the **final** trained checkpoint, as some may be
> disabled in the training configuration.

---

## Model Training

**Task.** Multi-output regression of the six Episcanner Richards descriptors for
the upcoming season, per municipality, from a 52-week look-back window.

**Architecture / configuration** (`pytorch-forecasting` `TemporalFusionTransformer`):

- Encoder length: 52 weeks (min 20); prediction length: 1 (season-shifted target).
- `hidden_size=32`, `attention_head_size=2`, `dropout=0.1`, `hidden_continuous_size=16`.
- Loss: `MultiLoss` of six `QuantileLoss` heads (`output_size=[7,7,7,7,7,7]`),
  quantiles `[0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.98]`.
- Target normalization (per `geocode`, `GroupNormalizer`): `softplus` for
  `R0`, `peak_week`, `beta`, `gamma`; `logit` for `alpha`; none for
  `log_total_cases` (already `log1p`-transformed).

**Optimization.**

- Optimizer: Adam; `learning_rate=0.03`; `reduce_on_plateau_patience=4`.
- `batch_size=512`, up to `30` epochs, `gradient_clip_val=0.1`.
- Trainer: PyTorch Lightning, single GPU, `bf16-mixed` precision.
- Early stopping on `val_loss` (patience 5); best checkpoint by `val_loss`.

**Reproducing the pipeline.**

```bash
# 1) build the model-ready table
python src/preprocess.py            # -> data/processed/dataset_tft_completo.parquet

# 2) train
python src/train.py                 # -> models/checkpoints/tft-*.ckpt

# 3) inference: parameter quantiles per municipality, per validation cutoff
python src/run_inference.py         # -> outputs/params/params_test{1..4}.parquet

# 4) build validated submissions (city + state)
python src/build_submissions.py     # -> outputs/submissions/dengue_{city,state}/...

# 5) upload to the platform (needs .env with API_KEY=usuario:chave)
python src/upload.py                # DRY_RUN=True first, then DRY_RUN=False
```

Validation targets follow the challenge protocol: for each season, only data up
to EW25 of the season's first year is used (2022→2022-23, 2023→2023-24,
2024→2024-25, 2025→2025-26).

---

## Data Usage Restriction

All datasets used are open-access, regularly updatable, and available for every
Brazilian state, in compliance with the challenge data policy. Epidemiological
data (Infodengue), climate series (Copernicus ERA5), and the Episcanner
parameters are obtained through the Mosqlimate FTP/API. External open sources
not distributed by Mosqlimate — the seasonal climate forecast, the NOAA ocean
indices (ENSO/IOD/PDO), and IBGE population — are shared with the organizers so
that all participants can reproduce the results. No proprietary, restricted, or
non-public data were used.

---

## Predictive Uncertainty

The Episcanner Richards model represents cumulative cases as

```
J(t) = L − L · [1 + α · exp(b · (t − t_j))]^(−1/α)
```

where `L = total_cases`, `t_j = peak_week`, `α = alpha`, and the growth rate is
recovered from the SIR mapping `β = b/α` as `b = beta · α` (so
`R0 = 1/(1−α)`). Weekly incidence is the first difference `J(t) − J(t−1)`,
clipped at zero, over the season's weeks aligned so that `t_j` lands on the
predicted peak week.

**From parameters to case-level intervals.** The TFT produces predictive
quantiles for each parameter, but the challenge requires prediction intervals on
weekly cases, and the parameter→cases map is nonlinear. We therefore propagate
uncertainty by **Monte Carlo**:

1. For each municipality, sample parameter vectors by inverse-CDF interpolation
   of the per-parameter predictive quantiles.
2. Reconstruct a weekly curve for each draw.
3. Take the empirical `2.5/5/10/25/50/75/90/95/97.5` percentiles across draws to
   form the `pred` and the 50/80/90/95% intervals.

**State level.** Municipal curves are summed **within each state per Monte Carlo
draw** before taking percentiles, so state intervals reflect the aggregation
rather than a naive sum of municipal quantiles.

All submissions are enforced to satisfy the platform rules: Sunday dates,
continuous weekly sequence covering EW41→EW40, non-negativity, and nested
intervals `lower_95 ≤ … ≤ lower_50 ≤ pred ≤ upper_50 ≤ … ≤ upper_95`.

**Assumptions and limitations.** The Monte Carlo currently treats parameter
marginals (and municipalities, for state aggregation) as independent; because
epidemics are spatially and parametrically correlated, this can make aggregated
intervals narrower than ideal.

---

## References

- Coelho, F. C. et al. *Large-scale epidemiological modelling: scanning for
  mosquito-borne diseases spatio-temporal patterns in Brazil* (Episcanner).
  arXiv:2407.21286.
- Mosqlimate project. *Mosqlimate: a platform providing automatable access to
  data and forecasting models for arbovirus disease.* arXiv:2410.18945.
- Wang, X.-S., Wu, J., & Yang, Y. (2012). *Richards model revisited: validation
  by and application to infection dynamics.* Journal of Theoretical Biology.
  (SIR ↔ Richards parameter mapping.)
- Lim, B., Arık, S. Ö., Loeff, N., & Pfister, T. (2021). *Temporal Fusion
  Transformers for interpretable multi-horizon time series forecasting.*
  International Journal of Forecasting.
- Bracher, J., Ray, E. L., Gneiting, T., & Reich, N. G. (2021). *Evaluating
  epidemic forecasts in an interval format.* PLoS Computational Biology.
  (Weighted Interval Score.)
- Codeço, C. T. et al. *Infodengue: real-time dengue surveillance in Brazil.*
- Hersbach, H. et al. (2020). *The ERA5 global reanalysis.* Q. J. R.
  Meteorol. Soc.
