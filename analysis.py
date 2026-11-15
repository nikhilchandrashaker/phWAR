import pandas as pd, numpy as np, json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, pickle
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
rng = np.random.default_rng(7)
MUTE_ = '#586873'
NAVY, ORG, GRY, TEAL, RED = '#1f3a5f', '#e07a1f', '#8a94a3', '#2a9d8f', '#c8553d'
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.titleweight': 'bold',
                     'axes.titlesize': 11, 'figure.dpi': 110, 'savefig.dpi': 200, 'savefig.bbox': 'tight', 'font.family': 'DejaVu Sans'})
df = pd.read_pickle('data/all_pa.pkl'); names = pd.read_csv('data/names.csv', index_col=0).name
const = pd.read_csv('data/season_constants.csv', index_col=0)
ps = pd.read_csv('data/ph_player_season.csv'); car = pd.read_csv('data/ph_career.csv')
RES = {}
ph = df[df.ph == 1]; non = df[df.ph == 0]
RES['n_pa_total'] = int(len(df)); RES['n_ph'] = int(len(ph)); RES['n_games'] = int(df.game.nunique())
RES['ph_r_pa'] = float(ph.r.mean()); RES['all_r_pa'] = float(df.r.mean()); RES['ph_li_mean'] = float(ph.li.mean()); RES['ph_li_median'] = float(ph.li.median())
RES['ph_per_game'] = float(len(ph) / df.game.nunique())
# ---------- Fig1 pipeline diagram ----------
fig, ax = plt.subplots(figsize=(11, 4.6)); ax.axis('off'); ax.set_xlim(0, 11.2); ax.set_ylim(0, 4.6)
def box(x, y, w, h, t, c, tc='white', fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.03,rounding_size=0.12', fc=c, ec='none'))
    ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', color=tc, fontsize=fs, fontweight='bold', wrap=True)
def arr(x1, y1, x2, y2): ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=12, color=GRY, lw=1.4))
box(0.1, 1.9, 1.8, 0.9, 'Retrosheet\nplay-by-play\n2010–2025', NAVY)
box(2.4, 1.9, 1.8, 0.9, 'Event parser\nbase-out state,\nscore, PH flag', NAVY)
box(4.7, 3.2, 2.0, 0.8, 'RE24 + linear\nweights (runs)', TEAL)
box(4.7, 1.9, 2.0, 0.8, 'Win expectancy\nmodel (GBM)', TEAL)
box(4.7, 0.6, 2.0, 0.8, 'Leverage index\n(E|ΔWE| model)', TEAL)
box(7.2, 3.2, 1.7, 0.8, 'Park-adj.\nrun value  r', ORG)
box(7.2, 1.9, 1.7, 0.8, 'WPA\n(validation)', ORG)
box(7.2, 0.6, 1.7, 0.8, 'LI per PA', ORG)
box(9.25, 2.6, 1.85, 1.0, 'phWAR-N\nΣ(r − repl) / RPW', RED, fs=8)
box(9.25, 0.9, 1.85, 1.0, 'phWAR\nΣ(r − repl)·LI / RPW', RED, fs=8)
for a in [(1.9, 2.35, 2.4, 2.35), (4.2, 2.45, 4.7, 3.6), (4.2, 2.35, 4.7, 2.3), (4.2, 2.25, 4.7, 1.0), (6.7, 3.6, 7.2, 3.6), (6.7, 2.3, 7.2, 2.3), (6.7, 1.0, 7.2, 1.0), (8.9, 3.5, 9.25, 3.3), (8.9, 1.0, 9.25, 1.3), (8.9, 3.45, 9.25, 1.6)]: arr(*a)
ax.set_title('Figure 1. phWAR construction pipeline', loc='left', y=1.0)
fig.savefig('figures/fig01_pipeline.png'); plt.close()
# ---------- Fig2 RE24 + linear weights ----------
re = pd.read_csv('data/re24_matrix.csv'); lw = pd.read_csv('data/linear_weights.csv')
pool = re.groupby(['outs', 'base_s']).re.mean().unstack(0)
lab = ['---', '1--', '-2-', '12-', '--3', '1-3', '-23', '123']
fig, axs = plt.subplots(1, 2, figsize=(10.5, 4), gridspec_kw={'width_ratios': [1, 1.25]})
im = axs[0].imshow(pool.values, cmap='YlOrRd', aspect='auto'); axs[0].set_yticks(range(8)); axs[0].set_yticklabels(lab); axs[0].set_xticks(range(3)); axs[0].set_xlabel('Outs')
for i in range(8):
    for j in range(3): axs[0].text(j, i, f'{pool.values[i, j]:.2f}', ha='center', va='center', fontsize=8)
axs[0].set_title('Run expectancy by base-out state\n(2010–2025 average)'); axs[0].set_ylabel('Runners on')
l = lw.groupby('event').lw.mean().sort_values(); cols = [RED if v < 0 else TEAL for v in l.values]
axs[1].barh(l.index, l.values, color=cols); axs[1].axvline(0, color='k', lw=.7); axs[1].set_xlabel('Run value per event'); axs[1].set_title('Linear weights (mean RE24 change)')
for i, v in enumerate(l.values): axs[1].text(v + (0.02 if v >= 0 else -0.02), i, f'{v:+.2f}', va='center', ha='left' if v >= 0 else 'right', fontsize=8)
axs[1].set_xlim(-0.4, 2.4); fig.suptitle('Figure 2. Run-value foundation', x=0.01, ha='left', fontweight='bold'); fig.tight_layout(); fig.savefig('figures/fig02_run_values.png'); plt.close()
# ---------- Fig3 WE calibration & heatmap ----------
h = pickle.load(open('data/we_holdout.pkl', 'rb')); RES['we_metrics'] = {k: float(v) for k, v in h['metrics'].items()}
bins = np.linspace(0, 1, 21); idx = np.digitize(h['p'], bins) - 1
cal = pd.DataFrame({'p': h['p'], 'y': h['y'], 'b': idx}).groupby('b').agg(p=('p', 'mean'), y=('y', 'mean'), n=('y', 'size'))
mods = pickle.load(open('data/models.pkl', 'rb')); we = mods['we']; lev = mods['lev']
fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.1))
axs[0].plot([0, 1], [0, 1], color=GRY, ls='--'); axs[0].scatter(cal.p, cal.y, s=np.clip(cal.n / 800, 12, 90), color=NAVY, alpha=.85)
axs[0].set_xlabel('Predicted home win probability'); axs[0].set_ylabel('Observed home win rate'); axs[0].set_title(f'Held-out calibration (2023–25)\nBrier {h["metrics"]["brier"]:.3f} vs {h["metrics"]["base_brier"]:.3f} baseline')
inn = np.arange(1, 10); dd = np.arange(-6, 7)
G = np.array([[we.predict_proba([[i, 1, 0, 0, d]])[0, 1] for i in inn] for d in dd])
im = axs[1].imshow(G, origin='lower', cmap='RdBu', vmin=0, vmax=1, aspect='auto', extent=[.5, 9.5, -6.5, 6.5]); axs[1].set_xlabel('Inning (bottom, 0 out, bases empty)'); axs[1].set_ylabel('Home lead (runs)')
axs[1].set_title('Win expectancy surface (home team)'); plt.colorbar(im, ax=axs[1], label='P(home win)')
fig.suptitle('Figure 3. Win-expectancy model', x=0.01, ha='left', fontweight='bold'); fig.tight_layout(); fig.savefig('figures/fig03_win_expectancy.png'); plt.close()
# ---------- Fig4 leverage ----------
fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.1))
Lg = np.array([[lev.predict([[i, 1, 1, 0, d]])[0] for i in inn] for d in dd]); Lg = Lg / df.wpa.abs().mean()
im = axs[0].imshow(Lg, origin='lower', cmap='magma_r', aspect='auto', extent=[.5, 9.5, -6.5, 6.5]); plt.colorbar(im, ax=axs[0], label='Leverage index'); axs[0].set_xlabel('Inning (bottom, 1 out, bases empty)'); axs[0].set_ylabel('Home lead (runs)'); axs[0].set_title('Leverage by game state')
bins = np.linspace(0, 5, 41)
axs[1].hist(non.li.clip(upper=5), bins=bins, weights=np.full(len(non), 1 / len(non)), alpha=.7, color=GRY, label=f'All other PA (mean {non.li.mean():.2f})')
axs[1].hist(ph.li.clip(upper=5), bins=bins, weights=np.full(len(ph), 1 / len(ph)), alpha=.7, color=ORG, label=f'Pinch-hit PA (mean {ph.li.mean():.2f})')
axs[1].set_xlabel('Leverage index (clipped at 5)'); axs[1].set_ylabel('Share of PA'); axs[1].legend(frameon=False); axs[1].set_title('Pinch hitters bat in higher-leverage spots')
fig.suptitle('Figure 4. Leverage', x=0.01, ha='left', fontweight='bold'); fig.tight_layout(); fig.savefig('figures/fig04_leverage.png'); plt.close()
# ---------- Fig5 PH profile ----------
fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.8))
s = ph.groupby('season').size(); axs[0].bar(s.index, s.values, color=NAVY); axs[0].set_title('Pinch-hit PA per season'); axs[0].set_xticks(range(2010, 2026, 3)); axs[0].text(2020, s[2020] + 150, '60-game\nseason', ha='center', fontsize=7.5, color=MUTE_)
RES['ph_pa_by_season'] = {int(k): int(v) for k, v in s.items()}
bi = ph.inning.clip(upper=10).value_counts(normalize=True).sort_index(); axs[1].bar(bi.index, bi.values * 100, color=ORG); axs[1].set_xticks(range(1, 11)); axs[1].set_xticklabels(list(range(1, 10)) + ['10+']); axs[1].set_title('Inning of PH appearance'); axs[1].set_ylabel('% of PH PA')
ev = ['K', 'BB', '1B', '2B', 'HR', 'OUT']; a = non.event.value_counts(normalize=True)[ev] * 100; b = ph.event.value_counts(normalize=True)[ev] * 100
x = np.arange(len(ev)); axs[2].bar(x - .2, a.values, .4, color=GRY, label='Other PA'); axs[2].bar(x + .2, b.values, .4, color=ORG, label='Pinch hit'); axs[2].set_xticks(x); axs[2].set_xticklabels(ev); axs[2].legend(frameon=False); axs[2].set_title('Outcome mix (%)')
RES['ph_k_rate'] = float((ph.event == 'K').mean()); RES['non_k_rate'] = float((non.event == 'K').mean()); RES['ph_hr_rate'] = float((ph.event == 'HR').mean()); RES['non_hr_rate'] = float((non.event == 'HR').mean())
RES['ph_late_share'] = float((ph.inning >= 7).mean())
fig.suptitle('Figure 5. What pinch hitting looks like', x=0.01, ha='left', fontweight='bold'); fig.tight_layout(); fig.savefig('figures/fig05_profile.png'); plt.close()
# ---------- Cold-bench decomposition (paired design) ----------
nb = non.groupby('batter', observed=True).agg(n_non=('r', 'size'), r_non=('r', 'mean'))
nr = non[non.reliever == 1].groupby('batter', observed=True).agg(n_rel=('r', 'size'), r_rel=('r', 'mean'))
pb = ph.groupby('batter', observed=True).agg(n_ph=('r', 'size'), r_ph=('r', 'mean'))
P = pb.join(nb).join(nr).dropna(); P = P[(P.n_ph >= 30) & (P.n_non >= 300) & (P.n_rel >= 150)]
w = P.n_ph; wm = lambda c: np.average(P[c], weights=w)
allm = df.r.mean(); parts = dict(sel=wm('r_non') - allm, rel=wm('r_rel') - wm('r_non'), cold=wm('r_ph') - wm('r_rel'))
def boot():
    out = []
    for _ in range(2000):
        S = P.sample(len(P), replace=True, random_state=int(rng.integers(1e9))); ww = S.n_ph
        f = lambda c: np.average(S[c], weights=ww)
        out.append([f('r_non') - allm, f('r_rel') - f('r_non'), f('r_ph') - f('r_rel')])
    return np.percentile(out, [2.5, 97.5], axis=0)
ci = boot(); tot = wm('r_ph') - allm
RES['cold'] = dict(n_players=int(len(P)), selection=float(parts['sel']), reliever=float(parts['rel']), cold=float(parts['cold']), total=float(tot),
                   ci_sel=[float(v) for v in ci[:, 0]], ci_rel=[float(v) for v in ci[:, 1]], ci_cold=[float(v) for v in ci[:, 2]],
                   cold_per600=float(parts['cold'] * 600), ph_mean_paired=float(wm('r_ph')), non_mean_paired=float(wm('r_non')))
fig, ax = plt.subplots(figsize=(8.5, 4.2)); vals = [parts['sel'], parts['rel'], parts['cold']]; lbl = ['Who gets sent\nto pinch hit\n(selection)', 'Facing relievers\ninstead of\nstarters', '“Cold off the\nbench” penalty']
cum = 0
for i, (v, c) in enumerate(zip(vals, [GRY, GRY, ORG])):
    ax.bar(i, v * 100, bottom=cum * 100, color=c, width=.6)
    ax.errorbar(i, (cum + v) * 100, yerr=[[(v - ci[0, i]) * 100], [(ci[1, i] - v) * 100]], color='k', capsize=4, lw=1.2)
    ax.text(i + .33, (cum + v / 2) * 100, f'{v * 100:+.2f}', ha='left', va='center', fontsize=9.5, fontweight='bold'); cum += v
ax.bar(3, tot * 100, color=NAVY, width=.6); ax.text(3.33, tot * 50, f'{tot * 100:+.2f}', ha='left', va='center', fontsize=9.5, fontweight='bold')
ax.set_xlim(-.5, 4.0)
ax.set_xticks(range(4)); ax.set_xticklabels(lbl + ['Total PH gap\nvs league avg PA'], fontsize=8.5); ax.axhline(0, color='k', lw=.7); ax.set_ylabel('Runs per 100 PA (vs league-avg PA)')
ax.set_title(f'Figure 6. Why pinch hitters underperform  (paired design, n = {len(P)} hitters)', loc='left'); fig.tight_layout(); fig.savefig('figures/fig06_cold_bench.png'); plt.close()
# ---------- Reliability & prediction ----------
def split_half(sub, minpa, reps=100):
    cors = []
    for _ in range(reps):
        a, b = [], []
        for _, g in sub:
            if len(g) < minpa: continue
            v = g.r.values; p = rng.permutation(len(v)); k = len(v) // 2
            a.append(v[p[:k]].mean()); b.append(v[p[k:2 * k]].mean())
        cors.append(np.corrcoef(a, b)[0, 1])
    return float(np.mean(cors)), len(a)
rp, n1 = split_half(ph.groupby('batter', observed=True), 60)
# non-PH matched to same PA counts
phn = ph.groupby('batter', observed=True).size(); elig = phn[phn >= 60].index
nsub = non[non.batter.isin(elig)].groupby('batter', observed=True)
def split_matched(reps=100):
    cors = []
    for _ in range(reps):
        a, b = [], []
        for bt in elig:
            v = nsub.get_group(bt).r.values; k = phn[bt] // 2; p = rng.permutation(len(v))
            a.append(v[p[:k]].mean()); b.append(v[p[k:2 * k]].mean())
        cors.append(np.corrcoef(a, b)[0, 1])
    return float(np.mean(cors))
rn = split_matched()
sb = lambda r: 2 * r / (1 + r)
RES['reliability'] = dict(n=n1, ph_half=rp, ph_full=sb(rp), non_half=rn, non_full=sb(rn))
# year-to-year prediction
S = ph.groupby(['batter', 'season'], observed=True).agg(n_ph=('r', 'size'), r_ph=('r', 'mean')).reset_index()
N = non.groupby(['batter', 'season'], observed=True).agg(n_non=('r', 'size'), r_non=('r', 'mean')).reset_index()
M = S.merge(N, on=['batter', 'season']); M = M[M.n_non >= 100]
nx = M.copy(); nx['season'] -= 1; Z = M.merge(nx[['batter', 'season', 'n_ph', 'r_ph']], on=['batter', 'season'], suffixes=('', '_next'))
Z = Z[(Z.n_ph >= 15) & (Z.n_ph_next >= 15) & ~Z.season.isin([2019, 2020])].reset_index(drop=True)
Z['fold'] = rng.integers(0, 5, len(Z)); y = Z.r_ph_next.values; ww = Z.n_ph_next.values
def wls(X, y, w): 
    W = np.sqrt(w); return np.linalg.lstsq(X * W[:, None], y * W, rcond=None)[0]
def cv(cols):
    pred = np.zeros(len(Z))
    for f in range(5):
        tr = Z.fold != f; X = np.c_[np.ones(len(Z)), Z[cols].values] if cols else np.ones((len(Z), 1))
        b = wls(X[tr], y[tr], ww[tr]); pred[~tr] = X[~tr] @ b
    return float(np.sqrt(np.average((pred - y) ** 2, weights=ww))), pred
rm = {'League PH mean': cv([])[0], 'Last year’s PH rate': cv(['r_ph'])[0], 'Last year’s non-PH rate': cv(['r_non'])[0], 'Blend of both': cv(['r_ph', 'r_non'])[0]}
Xf = np.c_[np.ones(len(Z)), Z.r_ph, Z.r_non]; bfull = wls(Xf, y, ww)
RES['predict'] = dict(n=int(len(Z)), rmse=rm, coef=dict(intercept=float(bfull[0]), ph=float(bfull[1]), non=float(bfull[2])))
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.9))
axs[0].bar(['Pinch-hit\nPA', 'Matched non-PH\nPA'], [sb(rp), sb(rn)], color=[ORG, GRY]); axs[0].set_ylim(0, 0.4); axs[0].set_ylabel('Split-half reliability (Spearman–Brown)'); axs[0].set_title('How much of a PH rate is repeatable skill?')
for i, v in enumerate([sb(rp), sb(rn)]): axs[0].text(i, v + .008, f'{v:.2f}', ha='center', fontweight='bold')
k = list(rm); v = [rm[i] * 100 for i in k]; axs[1].barh(k[::-1], v[::-1], color=NAVY); axs[1].set_xlim(0, max(v) * 1.15); axs[1].text(0.5, -0.32, 'No predictor beats the league mean at this sample size', transform=axs[1].transAxes, ha='center', fontsize=8.5, color=RED); axs[1].set_xlabel('Out-of-sample RMSE, next-season PH runs per 100 PA'); axs[1].set_title('Forecasting next year’s PH performance')
for i, vv in enumerate(v[::-1]): axs[1].text(vv + .1, i, f'{vv:.2f}', va='center', fontsize=9)
fig.suptitle('Figure 7. Season-level pinch-hit performance is mostly noise', x=0.01, ha='left', fontweight='bold'); fig.tight_layout(); fig.savefig('figures/fig07_reliability.png'); plt.close()
# ---------- Manager usage: talent vs leverage ----------
tal = non.groupby('batter', observed=True).r.agg(['mean', 'size']); tal = tal[tal['size'] >= 300]['mean']
q = ph.assign(tal=ph.batter.map(tal)).dropna(subset=['tal'])
q['liq'] = pd.qcut(q.li, 5, labels=False, duplicates='drop')
t = q.groupby('liq').agg(tal=('tal', 'mean'), li=('li', 'mean'), n=('tal', 'size'))
RES['usage'] = dict(talent_by_li_quintile=[float(v) for v in t.tal], li_by_quintile=[float(v) for v in t.li], slope_per_li=float(np.polyfit(q.li.clip(upper=4), q.tal, 1)[0]), corr=float(np.corrcoef(q.li.clip(upper=4), q.tal)[0, 1]))
# ---------- Fig8 leaderboards ----------
top = car.sort_values('phwar', ascending=False).head(12).iloc[::-1]; s2 = ps[ps.pa >= 25].sort_values('phwar', ascending=False).head(12).iloc[::-1]
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
axs[0].barh(top.name, top.phwar, color=NAVY); axs[0].scatter(top.phwar_n, top.name, color=ORG, zorder=3, label='phWAR-N (context-neutral)'); axs[0].set_title('Career phWAR, 2010–2025'); axs[0].legend(frameon=False, loc='lower right', fontsize=8)
lb = [f'{n} {int(sn)}' for n, sn in zip(s2.name, s2.season)]; axs[1].barh(lb, s2.phwar, color=TEAL); axs[1].scatter(s2.phwar_n, lb, color=ORG, zorder=3); axs[1].set_title('Best single seasons (≥25 PH PA)')
for a in axs: a.set_xlabel('phWAR')
fig.suptitle('Figure 8. Leaderboards (bars = leverage-weighted phWAR; dots = context-neutral)', x=0.01, ha='left', fontweight='bold'); fig.tight_layout(); fig.savefig('figures/fig08_leaderboards.png'); plt.close()
# ---------- Fig9 phWAR relations ----------
big = ps[ps.pa >= 20]
fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.1))
axs[0].scatter(big.phwar_n, big.phwar, s=big.pa / 2.5, alpha=.35, color=NAVY); lim = [big.phwar_n.min() - .1, big.phwar_n.max() + .1]; axs[0].plot(lim, lim, color=GRY, ls='--'); axs[0].set_xlabel('phWAR-N (context-neutral)'); axs[0].set_ylabel('phWAR (leverage-weighted)'); axs[0].set_title('Leverage re-weights value')
axs[1].scatter(big.phwar, big.wpa, s=big.pa / 2.5, alpha=.35, color=TEAL); axs[1].set_xlabel('phWAR'); axs[1].set_ylabel('Win Probability Added (wins)'); axs[1].set_title('phWAR vs. observed WPA')
RES['corr'] = dict(n_vs_l=float(big.phwar_n.corr(big.phwar)), l_vs_wpa=float(big.phwar.corr(big.wpa)), n_vs_wpa=float(big.phwar_n.corr(big.wpa)), n=int(len(big)))
fig.suptitle('Figure 9. Relationships among value measures (player-seasons, ≥20 PH PA)', x=0.01, ha='left', fontweight='bold'); fig.tight_layout(); fig.savefig('figures/fig09_relationships.png'); plt.close()
# ---------- Fig10 sensitivity ----------
base = ph.assign(rpw=ph.season.map(const.rpw)); res = {}
for rl in [0, -10, -20, -30, -40]:
    res[rl] = ((base.r - rl / 600) * base.li / base.rpw).groupby(base.batter, observed=True).sum()
R = pd.DataFrame(res); R20 = R[-20]; 
sens = {rl: float(R[rl].corr(R20, method='spearman')) for rl in R}
RES['sensitivity'] = {str(k): v for k, v in sens.items()}; RES['sum_by_repl'] = {str(k): float(R[k].sum()) for k in R}
fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.8))
axs[0].plot(list(R.columns), [R[k].sum() for k in R], marker='o', color=NAVY); axs[0].axhline(0, color=GRY, lw=.7); axs[0].set_xlabel('Replacement level (runs per 600 PA vs avg PA)'); axs[0].set_ylabel('League total phWAR, 2010–2025'); axs[0].set_title('Total pinch-hit value depends on the baseline')
axs[1].bar([str(k) for k in R], [sens[k] for k in R], color=ORG); axs[1].set_ylim(.8, 1.01); axs[1].set_xlabel('Replacement level'); axs[1].set_ylabel('Spearman ρ of career rankings vs. −20'); axs[1].set_title('Rankings barely move')
fig.suptitle('Figure 10. Sensitivity to replacement level', x=0.01, ha='left', fontweight='bold'); fig.tight_layout(); fig.savefig('figures/fig10_sensitivity.png'); plt.close()
# ---------- Fig11 usage ----------
fig, ax = plt.subplots(figsize=(6.5, 3.8)); ax.bar(range(len(t)), t.tal * 100, color=ORG); ax.set_xticks(range(len(t))); ax.set_xticklabels([f'Q{i + 1}\n(LI {l:.2f})' for i, l in enumerate(t.li)])
ax.set_ylabel('Hitter’s non-PH runs per 100 PA'); ax.set_xlabel('Leverage quintile of pinch-hit PA'); ax.set_title('Figure 11. Managers send better hitters in bigger spots', loc='left', fontsize=10)
fig.tight_layout(); fig.savefig('figures/fig11_usage.png'); plt.close()
# ---------- season summary & top tables to JSON ----------
RES['top_career'] = car.sort_values('phwar', ascending=False).head(10)[['name', 'seasons', 'pa', 'phwar', 'phwar_n', 'wpa']].round(2).to_dict('records')
RES['top_seasons'] = ps[ps.pa >= 25].sort_values('phwar', ascending=False).head(10)[['name', 'season', 'pa', 'avg', 'obp', 'slg', 'phwar', 'phwar_n', 'wpa']].round(3).to_dict('records')
RES['n_player_seasons'] = int(len(ps)); RES['n_players'] = int(car.shape[0])
json.dump(RES, open('data/results.json', 'w'), indent=1, default=float)
print(json.dumps({k: RES[k] for k in ['cold', 'reliability', 'predict', 'usage', 'corr', 'sensitivity', 'sum_by_repl', 'ph_k_rate', 'non_k_rate', 'ph_li_mean', 'ph_late_share', 'we_metrics']}, indent=1))
