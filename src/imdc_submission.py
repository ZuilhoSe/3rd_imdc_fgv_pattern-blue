"""
IMDC 2026 — reconstrução (episcanner/Richards) + formatação/validação de submissão.
O TFT prevê descritores da temporada; aqui viram curvas semanais de casos.

Reconstrução Richards (parametrização do episcanner), t = semanas desde EW41:
    J(t) = 1 - (1 + alpha*exp(b*(t - tj)))**(-1/alpha)      [fração acumulada]
    SIR:  beta = b/alpha  ->  b = beta*alpha
    casos(t) = total * [J(t) - J(t-1)] / sum_t [J(t) - J(t-1)]
tj (peak_week) é o índice da semana de pico dentro da temporada (EW41 = 0) — a versão
anterior recebia YYYYWW, cortava em 53 e colocava todos os picos no meio da temporada.
O total é normalizado para a temporada, então a soma da curva = total previsto.

Incerteza: Monte Carlo sobre as marginais previstas (CDF inversa interpolada). No
agregado estadual, os sorteios dos municípios são correlacionados por uma cópula
gaussiana com um fator comum por UF (rho), calibrado nas validações (evaluate.py).
"""
import numpy as np
import pandas as pd
from epiweeks import Week
from scipy.stats import norm

QLEVELS = {  # nível de probabilidade de cada coluna exigida pelo desafio
    "lower_95": 0.025, "lower_90": 0.05, "lower_80": 0.10, "lower_50": 0.25,
    "pred": 0.50,
    "upper_50": 0.75, "upper_80": 0.90, "upper_90": 0.95, "upper_95": 0.975,
}
INTERVAL_ORDER = ["lower_95", "lower_90", "lower_80", "lower_50", "pred",
                  "upper_50", "upper_80", "upper_90", "upper_95"]
PARAMS = ["total_cases", "alpha", "beta", "peak_week"]


# ---------------------------------------------------------------- datas
def season_weeks(start_year):
    w, end = Week(start_year, 41, system="cdc"), Week(start_year + 1, 40, system="cdc")
    weeks = []
    while w <= end:
        weeks.append(w); w = w + 1
    return weeks


def season_sundays(start_year):
    return [w.startdate() for w in season_weeks(start_year)]


# ------------------------------------------------- reconstrução vetorizada
def _richards_frac(t, alpha, b, tj):
    return 1.0 - (1.0 + alpha * np.exp(np.clip(b * (t - tj), -50, 50))) ** (-1.0 / alpha)


def weekly_curves(start_year, total_cases, alpha, beta, peak_week):
    """Vetorizado. Entradas shape (N,) -> casos semanais shape (N, W)."""
    W = len(season_weeks(start_year))
    L = np.clip(np.asarray(total_cases, float), 0, None)[:, None]
    al = np.clip(np.asarray(alpha, float), 1e-3, 0.999)[:, None]
    b = (np.clip(np.asarray(beta, float), 1e-6, None)[:, None]) * al
    tj = np.clip(np.asarray(peak_week, float), 0, W - 1)[:, None]
    t = np.arange(W)[None, :]
    inc = _richards_frac(t, al, b, tj) - _richards_frac(t - 1, al, b, tj)
    inc = np.clip(inc, 0, None)
    s = inc.sum(axis=1, keepdims=True)
    return L * np.where(s > 0, inc / np.where(s > 0, s, 1), 1.0 / W)


# ------------------------------------------------- amostragem Monte Carlo
def _interp_rows(u, qs, V):
    """interp linear por linha. u:(M,D)  qs:(K,)  V:(M,K) valores (ordenados)."""
    qs = np.asarray(qs, float)
    j = np.clip(np.searchsorted(qs, u, side="right") - 1, 0, len(qs) - 2)
    q0, q1 = qs[j], qs[j + 1]
    v0 = np.take_along_axis(V, j, axis=1)
    v1 = np.take_along_axis(V, j + 1, axis=1)
    w = np.clip((u - q0) / (q1 - q0), 0.0, 1.0)  # caudas além de 2%/98% ficam no último quantil
    return v0 + w * (v1 - v0)


def sample_params(param_q, qs, D, seed=0, rho=0.0):
    """
    param_q: dict {param: array (M,K)} com os K quantis previstos p/ M municípios.
    rho: correlação (cópula gaussiana, fator comum) entre municípios, por parâmetro.
    Retorna dict {param: array (M,D)}.
    """
    rng = np.random.default_rng(seed)
    out = {}
    for p in PARAMS:
        V = np.sort(np.asarray(param_q[p], float), axis=1)
        M = V.shape[0]
        z = np.sqrt(rho) * rng.standard_normal((1, D)) + np.sqrt(1 - rho) * rng.standard_normal((M, D))
        out[p] = _interp_rows(norm.cdf(z), qs, V)
    return out


# ------------------------------------------------- montagem + validação
def _finalize(mat_quantis):
    """mat_quantis: (9,W) na ordem INTERVAL_ORDER -> aplica >=0 e aninhamento."""
    m = np.clip(np.asarray(mat_quantis, float), 0, None)
    return np.sort(m, axis=0)


def build_df(start_year, mat_quantis):
    dates = pd.to_datetime(season_sundays(start_year)).strftime("%Y-%m-%d")
    m = _finalize(mat_quantis)
    df = pd.DataFrame({"date": dates})
    for i, c in enumerate(INTERVAL_ORDER):
        df[c] = m[i]
    return df


def _quantile_matrix(curves):
    return np.vstack([np.quantile(curves, QLEVELS[c], axis=0) for c in INTERVAL_ORDER])


def city_submission(start_year, param_q_row, qs, D=3000, seed=0):
    """param_q_row: dict {param: array (K,)} de UM município -> df de submissão."""
    pq = {p: np.asarray(param_q_row[p], float)[None, :] for p in PARAMS}
    s = sample_params(pq, qs, D, seed)
    curves = weekly_curves(start_year, s["total_cases"][0], s["alpha"][0], s["beta"][0], s["peak_week"][0])
    return build_df(start_year, _quantile_matrix(curves))


def state_submission(start_year, param_q_uf, qs, D=1000, seed=0, rho=0.0):
    """
    param_q_uf: dict {param: array (M,K)} de TODOS os municípios de uma UF.
    Soma as curvas por sorteio (propaga incerteza p/ o total estadual) -> df.
    """
    s = sample_params(param_q_uf, qs, D, seed, rho)
    M, W = s["alpha"].shape[0], len(season_weeks(start_year))
    total = np.zeros((D, W))
    for m in range(M):
        total += weekly_curves(start_year, s["total_cases"][m], s["alpha"][m], s["beta"][m], s["peak_week"][m])
    return build_df(start_year, _quantile_matrix(total))


def validate(df, start_year, verbose=True):
    errs = []
    exp = pd.to_datetime(pd.Series(season_sundays(start_year))).dt.strftime("%Y-%m-%d").tolist()
    if list(df["date"].astype(str)) != exp:
        errs.append(f"datas != EW41/{start_year}-EW40/{start_year+1} ({len(exp)} sem. esperadas)")
    d = pd.to_datetime(df["date"])
    if not (d.dt.weekday == 6).all(): errs.append("nem todas as datas são domingos")
    if len(d) > 1 and not (d.diff().dropna().dt.days == 7).all(): errs.append("descontinuidade nas datas")
    miss = [c for c in INTERVAL_ORDER if c not in df.columns]
    if miss: errs.append(f"faltam colunas: {miss}")
    else:
        v = df[INTERVAL_ORDER].to_numpy(float)
        if np.isnan(v).any(): errs.append("há NaN")
        if (v < 0).any(): errs.append("há valores negativos")
        if (np.diff(v, axis=1) < -1e-9).any(): errs.append("intervalos não-aninhados")
    ok = not errs
    if verbose:
        print("  ✅ válido" if ok else "  ❌ inválido: " + "; ".join(errs))
    return ok, errs
