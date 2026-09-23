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
   fits to each epidemic season. A sample whose decoder week falls in year *X*
   is labelled with the descriptors of the **next** season (EW41/*X* –
   EW40/*X+1*), so from data available up to EW25 of year *Y* the model
   predicts the upcoming *Y*/*Y+1* season.
2. **Reconstructing the weekly curve.** The predicted parameters are turned
   into a weekly incidence curve through the Richards equation (see
   *Predictive Uncertainty*). State-level forecasts are obtained by summing the
   reconstructed curves of **all** municipalities within each state.

One model is trained per forecast cut-off (the four validation tests and the
final forecast), each using only information available at that cut-off.

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
│   └── processed/                # model-ready tables (base_weekly.parquet, season_targets.parquet)
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
    ├── preprocess.py             # raw FTP files (+ 2026 updates) -> base_weekly.parquet + season_targets.parquet
    ├── common.py                 # cut-offs, features, season targets, TimeSeriesDataSet construction
    ├── train.py                  # one TFT per cut-off (test1..4, final) -> models/checkpoints/<tag>/best.ckpt
    ├── run_inference.py          # checkpoint -> Richards parameter quantiles for all 5,570 municipalities
    ├── build_submissions.py      # parameters -> weekly curves -> validated submission CSVs (city + state)
    ├── imdc_submission.py        # Richards reconstruction, Monte Carlo uncertainty, formatting & validation
    ├── evaluate.py               # WIS of the validation submissions; calibrates the state-level correlation
    ├── upload.py                 # uploads validated CSVs to the platform via mosqlient
    ├── models/                   # checkpoints/<tag>/best.ckpt + TensorBoard logs
    └── outputs/                  # parameter quantiles, submission CSVs, evaluation, upload manifests
```

---

## Libraries and Dependencies

- `python` 3.11
- `torch`, `lightning` (PyTorch Lightning)
- `pytorch-forecasting` (TFT, `TimeSeriesDataSet`, `QuantileLoss`, `MultiLoss`, `GroupNormalizer`)
- `pandas`, `numpy`, `pyarrow` (parquet I/O)
- `epiweeks` (MMWR/Brazilian epidemiological-week ↔ date conversion)
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
| Ocean/climate indices (`enso`, `iod`, `pdo`) | NOAA via Mosqlimate (weekly)    | merged, not a model input |
| Population by municipality/year | IBGE                            | `log_pop` |
| Environmental descriptors (`koppen`, `biome`) | Mosqlimate            | static categoricals |
| Health regions (`macroregion_name`, `regional_name`) | Ministry of Health / Mosqlimate | static categoricals |
| Episcanner Richards parameters (`peak_week`, `alpha`, `beta`) + observed season totals | Mosqlimate Episcanner / Infodengue | **prediction targets** |

**Engineered variables**

- Temporal: `time_idx`, `week_of_year`, `week_cycle` (season-centered so EW41→week 1),
  `sin_week_cycle`, `cos_week_cycle`, `season` (season end year, from the
  epidemiological year).
- Epidemiological: `log_casos = log1p(casos)`, `log_incidence = log1p(casos / population × 100,000)`.

**Variable roles in the TFT**

- **Static categoricals:** `uf`, `koppen`, `biome`, `macroregion_name`
- **Time-varying known reals:** `week_cycle`, `sin_week_cycle`,
  `cos_week_cycle`, `log_pop`, `forecast_temp_med`, `forecast_precip_tot`
  (`time_idx` only indexes the series; as a covariate it let the model memorise years)
- **Time-varying unknown reals:** `log_casos`, `log_incidence`, `temp_med`,
  `precip_med`, `rel_humid_med`
- **Targets (next season):** `log_total_cases` (log1p of the observed season
  total), `alpha`, `beta`, `peak_week` (index of the peak week within the
  season, EW41 = 0). `R0` and `gamma` are deterministic functions of `alpha`
  and the growth rate and are not modelled.

Seasons where Episcanner has no Richards fit (fewer than 50 cases, or failed
fit) are **kept**: they get their observed total and a shape imputed from the
median fitted shape of the municipality → health region → state → country,
computed only from seasons available at the cut-off. This lets the state
totals include every municipality.

Ocean indices (ENSO/IOD/PDO) are merged in the base table but are not model
inputs; the TDA features of earlier experiments are not used.

---

## Model Training

**Task.** Multi-output quantile regression of four season descriptors for the
upcoming season, per municipality, from a 52-week look-back window.

**Samples and leakage control.** For the cut-off EW25/*Y*:

- training samples have their decoder week in EW20–EW32 of year *X* and the
  season *X*/*X+1* as target, for seasons ending ≤ *Y*−2;
- early stopping uses the decoder at EW26 of year *Y*−2 and the last complete
  season (ending *Y*−1);
- the target normalizer (per `geocode`) is fitted only on seasons complete
  before the cut-off;
- at inference, the encoder ends at EW25/*Y* and a synthetic EW26/*Y* decoder
  row carries only known covariates.

A separate model is trained for each of the four validation cut-offs and the
final forecast (EW25/2026 → season 2026–27).

**Architecture / configuration** (`pytorch-forecasting` `TemporalFusionTransformer`):

- Encoder length: 52 weeks (min 20); prediction length: 1.
- `hidden_size=32`, `attention_head_size=2`, `dropout=0.1`, `hidden_continuous_size=16`.
- Loss: `MultiLoss` of four `QuantileLoss` heads, quantiles
  `[0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.98]`.
- Target normalization (per `geocode`, `GroupNormalizer`): none for
  `log_total_cases` and `peak_week`, `logit` for `alpha`, `log` for `beta`.

**Optimization.** Adam, `learning_rate=0.003`, `reduce_on_plateau_patience=3`,
`batch_size=256`, 400 batches per epoch, `gradient_clip_val=0.1`, `bf16-mixed`
on a single GPU; early stopping on `val_loss` and best checkpoint by `val_loss`
(max. 15 epochs for the final model, 8 for the validation models).

**Reproducing the pipeline** (run from `src/`).

```bash
python preprocess.py                 # -> data/processed/{base_weekly,season_targets}.parquet
python train.py final test1 test2 test3 test4   # -> models/checkpoints/<tag>/best.ckpt
python run_inference.py              # -> outputs/params/params_<tag>.parquet
python evaluate.py tune              # -> outputs/state_rho.json (state-level correlation)
python build_submissions.py          # -> outputs/submissions/dengue_{city,state}/<test{k}_{Y}|final_2026>/
python evaluate.py outputs/submissions   # WIS of the validation submissions
python upload.py                     # dry run; DRY_RUN=0 python upload.py to send (needs .env)
```

Validation targets follow the challenge protocol: for each season, only data up
to EW25 of the season's first year is used (2022→2022-23, 2023→2023-24,
2024→2024-25, 2025→2025-26); the final forecast uses data up to EW25/2026.

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

where `t` counts weeks from EW41, `t_j = peak_week`, `α = alpha`, and the
growth rate is recovered from the SIR mapping `β = b/α` as `b = beta · α`
(so `R0 = 1/(1−α)`). The weekly curve is the first difference
`J(t) − J(t−1)`, clipped at zero and rescaled so that the season sums to the
predicted total `L`.

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
draw** before taking percentiles. Because epidemics within a state are
correlated, the municipal draws share a common factor through a Gaussian copula
with correlation `rho`, chosen by minimising the WIS on the validation seasons
(`evaluate.py tune`).

All submissions are enforced to satisfy the platform rules: Sunday dates,
continuous weekly sequence covering EW41→EW40, non-negativity, and nested
intervals `lower_95 ≤ … ≤ lower_50 ≤ pred ≤ upper_50 ≤ … ≤ upper_95`.

**Assumptions and limitations.** Parameter marginals are sampled independently
within a municipality; Richards curves have a single peak per season.

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
