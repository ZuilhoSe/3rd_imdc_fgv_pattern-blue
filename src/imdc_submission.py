"""
IMDC 2026 — reconstrução (episcanner/Richards) + formatação/validação de submissão.
O TFT prevê parâmetros do episcanner por temporada; aqui viram curvas semanais de casos.

Reconstrução Richards (parametrização do episcanner):
    J(t) = L - L*(1 + alpha*exp(b*(t-tj)))**(-1/alpha)     [casos acumulados]
    SIR:  beta = b/alpha  ->  b = beta*alpha ;  R0 = 1/(1-alpha)
Só precisamos de 4 alvos: total_cases (L), alpha, beta, peak_week (tj).
R0 e gamma são redundantes (funções de alpha e b) -> descartados na reconstrução.
"""
import numpy as np
import pandas as pd
from epiweeks import Week

QLEVELS = {  # nível de probabilidade de cada coluna exigida pelo desafio
    "lower_95": 0.025, "lower_90": 0.05, "lower_80": 0.10, "lower_50": 0.25,
    "pred": 0.50,
    "upper_50": 0.75, "upper_80": 0.90, "upper_90": 0.95, "upper_95": 0.975,
}
INTERVAL_ORDER = ["lower_95","lower_90","lower_80","lower_50","pred",
                  "upper_50","upper_80","upper_90","upper_95"]
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

def _peak_index_lookup(start_year):
    """índice (na temporada) de cada semana epi do ano start_year+1; p/ ancorar o pico."""
    weeks = season_weeks(start_year)
    look = np.full(54, -1, dtype=int)
    for i, wk in enumerate(weeks):
        if wk.year == start_year + 1 and 1 <= wk.week <= 53:
            look[wk.week] = i
    return look, len(weeks)

# ------------------------------------------------- reconstrução vetorizada
def _richards_cum(t, L, alpha, b, tj):
    return L - L * (1.0 + alpha * np.exp(b * (t - tj)))**(-1.0/alpha)

def weekly_curves(start_year, total_cases, alpha, beta, peak_week):
    """
    Vetorizado. Entradas shape (N,) -> saída casos semanais shape (N, W).
    """
    L  = np.clip(np.asarray(total_cases, float), 0, None)
    al = np.clip(np.asarray(alpha, float), 1e-4, 0.999)
    be = np.clip(np.asarray(beta, float), 1e-8, None)
    tj = np.clip(np.asarray(peak_week, float), 1, 53)
    b  = be * al
    look, W = _peak_index_lookup(start_year)
    kp = look[np.clip(np.round(tj).astype(int), 1, 53)]
    kp = np.where(kp < 0, W // 2, kp)                       # fallback: meio da temporada
    idx = np.arange(W)[None, :]                             # (1,W)
    tau = idx - kp[:, None] + tj[:, None]                   # (N,W)
    cur = _richards_cum(tau,   L[:,None], al[:,None], b[:,None], tj[:,None]) \
        - _richards_cum(tau-1, L[:,None], al[:,None], b[:,None], tj[:,None])
    return np.clip(cur, 0, None)                            # (N,W)

# ------------------------------------------------- amostragem Monte Carlo
def _interp_rows(u, qs, V):
    """interp linear por linha. u:(M,D)  qs:(K,) níveis compartilhados  V:(M,K) valores."""
    qs = np.asarray(qs, float)
    j = np.clip(np.searchsorted(qs, u, side="right") - 1, 0, len(qs) - 2)  # (M,D)
    q0, q1 = qs[j], qs[j + 1]
    v0 = np.take_along_axis(V, j,     axis=1)
    v1 = np.take_along_axis(V, j + 1, axis=1)
    w = np.where(q1 > q0, (u - q0) / (q1 - q0), 0.0)
    return np.clip(v0 + w * (v1 - v0), np.minimum(v0, v1), np.maximum(v0, v1))

def sample_params(param_q, qs, D, seed=0):
    """
    param_q: dict {param: array (M,K)} com os K quantis previstos p/ M municípios.
    Retorna dict {param: array (M,D)} amostrado das marginais (interp da CDF inversa).
    """
    rng = np.random.default_rng(seed)
    out = {}
    for p in PARAMS:
        M = param_q[p].shape[0]
        u = rng.uniform(0, 1, size=(M, D))
        out[p] = _interp_rows(u, qs, param_q[p])
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

def city_submission(start_year, param_q_row, qs, D=3000, seed=0):
    """param_q_row: dict {param: array (K,)} de UM município -> df de submissão."""
    pq = {p: np.asarray(param_q_row[p], float)[None, :] for p in PARAMS}
    s = sample_params(pq, qs, D, seed)
    curves = weekly_curves(start_year, s["total_cases"][0], s["alpha"][0],
                           s["beta"][0], s["peak_week"][0])            # (D,W)
    mat = np.vstack([np.quantile(curves, QLEVELS[c], axis=0) for c in INTERVAL_ORDER])
    return build_df(start_year, mat)

def state_submission(start_year, param_q_uf, qs, D=1000, seed=0):
    """
    param_q_uf: dict {param: array (M,K)} de TODOS os municípios de uma UF.
    Soma as curvas por sorteio (propaga incerteza p/ o total estadual) -> df.
    """
    s = sample_params(param_q_uf, qs, D, seed)               # cada (M,D)
    M, W = s["alpha"].shape[0], len(season_weeks(start_year))
    total = np.zeros((D, W))
    for m in range(M):                                       # 1 município por vez (memória)
        total += weekly_curves(start_year, s["total_cases"][m], s["alpha"][m],
                               s["beta"][m], s["peak_week"][m])
    mat = np.vstack([np.quantile(total, QLEVELS[c], axis=0) for c in INTERVAL_ORDER])
    return build_df(start_year, mat)

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
