"""Build RE24, linear weights, win-expectancy, leverage, WPA and phWAR from parsed events."""
import pandas as pd, numpy as np, pickle
from sklearn.ensemble import HistGradientBoostingClassifier as HGC, HistGradientBoostingRegressor as HGR
from sklearn.metrics import log_loss, brier_score_loss

parts = []
for y in range(2010, 2026):
    d = pd.read_pickle(f'data/events_{y}.pkl')
    for c in ['game', 'date', 'bat_team', 'home', 'batter', 'pitcher', 'event']: d[c] = d[c].astype('category')
    for c in ['inning', 'half', 'outs', 'b1', 'b2', 'b3', 'diff', 'reliever', 'ph', 'runs', 'outs_after', 'a1', 'a2', 'a3',
              'inn_before', 'inn_total', 'home_win', 'last', 'season']: d[c] = d[c].astype('int16')
    parts.append(d)
df = pd.concat(parts, ignore_index=True); del parts
df['game'] = df.game.astype(str); 
for c in ['bat_team','home','batter','pitcher','event','date']: df[c] = df[c].astype(str).astype('category')
print(df.shape, flush=True)

# ---- run expectancy (RE24), per season, excluding walk-off-truncated innings ----
df['base_s'] = df.b1 + 2 * df.b2 + 4 * df.b3
df['base_a'] = df.a1 + 2 * df.a2 + 4 * df.a3
df['rest'] = df.inn_total - df.inn_before
ok = ~((df.half == 1) & (df.inning >= 9))
RE = df[ok].groupby(['season', 'outs', 'base_s']).rest.mean().rename('re').reset_index()
RE.to_csv('data/re24_matrix.csv', index=False)
reL = RE.set_index(['season', 'outs', 'base_s']).re
df['re_b'] = reL.reindex(pd.MultiIndex.from_arrays([df.season, df.outs, df.base_s])).values
aft = np.where(df.outs_after >= 3, 0.0,
               reL.reindex(pd.MultiIndex.from_arrays([df.season, df.outs_after.clip(upper=2), df.base_a])).values)
df['re_a'] = aft
df['re24'] = df.re_a - df.re_b + df.runs

# ---- linear weights by event & season (context-neutral run value) ----
LW = df.groupby(['season', 'event']).re24.mean().rename('lw').reset_index()
LW.to_csv('data/linear_weights.csv', index=False)
df = df.merge(LW, on=['season', 'event'], how='left')

# ---- park factors (3-yr window, shrunk 50%) ----
g = df.groupby('game', observed=True).agg(tot=('runs', 'sum'), home=('home', 'first'), season=('season', 'first'),
                                           vis=('bat_team', lambda s: None)).reset_index()
vis = df[df.half == 0].groupby('game', observed=True).bat_team.first().rename('vis')
g = g.drop(columns='vis').merge(vis, on='game')
pf = []
for y in range(2010, 2026):
    w = g[(g.season >= y - 1) & (g.season <= y + 1) & (g.season != 2020 if y != 2020 else True)]
    for t in sorted(g[g.season == y].home.unique()):
        h = w[w.home == t].tot.mean(); a = w[w.vis == t].tot.mean()
        pf.append((y, t, 1 + 0.5 * (h / a - 1)))
PF = pd.DataFrame(pf, columns=['season', 'home', 'pf']); PF.to_csv('data/park_factors.csv', index=False)
df = df.merge(PF, on=['season', 'home'], how='left')
rpp = df.groupby('season').runs.sum() / df.groupby('season').size()
df['park_adj'] = -(df.pf - 1) * df.season.map(rpp)
df['r'] = df.lw + df.park_adj      # context-neutral, park-adjusted runs vs league-average PA

# ---- win expectancy model (home-team perspective) ----
def feats(inn, half, outs, bs, hd):
    return np.c_[np.minimum(inn, 12), half, outs, bs, np.clip(hd, -12, 12)]
hd_b = np.where(df.half == 1, df['diff'], -df['diff'])
X = feats(df.inning, df.half, df.outs, df.base_s, hd_b); y = df.home_win.values
mono = [0, 0, 0, 0, 1]
tr = (df.season <= 2022).values
m_eval = HGC(max_iter=250, learning_rate=0.08, monotonic_cst=mono, random_state=0).fit(X[tr], y[tr])
p = m_eval.predict_proba(X[~tr])[:, 1]
we_metrics = dict(logloss=log_loss(y[~tr], p), brier=brier_score_loss(y[~tr], p), base_brier=brier_score_loss(y[~tr], np.full(p.shape, y[tr].mean())))
print('WE holdout', we_metrics, flush=True)
pickle.dump(dict(p=p, y=y[~tr], metrics=we_metrics), open('data/we_holdout.pkl', 'wb'))
we = HGC(max_iter=250, learning_rate=0.08, monotonic_cst=mono, random_state=0).fit(X, y)
df['we_b'] = we.predict_proba(X)[:, 1]
# after-state
diff_a = df['diff'] + df.runs
hd_a = np.where(df.half == 1, diff_a, -diff_a)
end = (df.outs_after >= 3).values
inn_a = np.where(end & (df.half == 1), df.inning + 1, df.inning)
half_a = np.where(end, 1 - df.half, df.half)
outs_a = np.where(end, 0, df.outs_after); bs_a = np.where(end, 0, df.base_a)
df['we_a'] = we.predict_proba(feats(inn_a, half_a, outs_a, bs_a, hd_a))[:, 1]
df.loc[df['last'] == 1, 'we_a'] = df.loc[df['last'] == 1, 'home_win']
sgn = np.where(df.half == 1, 1.0, -1.0)
df['wpa'] = sgn * (df.we_a - df.we_b)
# ---- leverage index ----
Xb = feats(df.inning, df.half, df.outs, df.base_s, hd_b)
lev = HGR(max_iter=200, learning_rate=0.08, random_state=0).fit(Xb, df.wpa.abs())
li = lev.predict(Xb); df['li'] = li / li.mean()
pickle.dump(dict(we=we, lev=lev), open('data/models.pkl', 'wb'))
print('WPA mean', df.wpa.mean(), 'LI mean', df.li.mean(), flush=True)

# ---- season constants ----
tg = df.groupby('season').apply(lambda x: x.groupby(['game', 'inning', 'half']).inn_total.first().sum() / (2 * x.game.nunique()))
const = pd.DataFrame({'runs_per_team_game': tg}); const['rpw'] = 2.22 * const.runs_per_team_game
const['runs_per_pa'] = rpp
ph = df[df.ph == 1]
const['ph_pa'] = ph.groupby('season').size()
const['ph_r_per_pa'] = ph.groupby('season').r.mean()
const['all_r_per_pa'] = df.groupby('season').r.mean()
const.to_csv('data/season_constants.csv'); print(const.round(3))
keep = ['game', 'date', 'season', 'bat_team', 'home', 'inning', 'half', 'outs', 'b1', 'b2', 'b3', 'diff', 'batter', 'pitcher',
        'reliever', 'ph', 'event', 'runs', 'outs_after', 'a1', 'a2', 'a3', 're_b', 're_a', 're24', 'lw', 'pf', 'r', 'we_b', 'we_a', 'wpa', 'li', 'home_win']
df[keep].to_pickle('data/all_pa.pkl')
print('saved', flush=True)
