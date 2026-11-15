import pandas as pd, numpy as np
df = pd.read_pickle('data/all_pa.pkl')
names = pd.read_csv('data/names.csv', index_col=0).name
const = pd.read_csv('data/season_constants.csv', index_col=0)
REPL = -20 / 600          # runs per PA vs league-average PA (standard replacement convention)
df['rpw'] = df.season.map(const.rpw)
df['rar'] = df.r - REPL                       # context-neutral runs above replacement
df['rar_lev'] = df.rar * df.li                # leverage-weighted
ph = df[df.ph == 1].copy()
ph['win_n'] = ph.rar / ph.rpw
ph['win_l'] = ph.rar_lev / ph.rpw
ev = ph.event
ph['ab'] = (~ev.isin(['BB', 'IBB', 'HBP', 'SF', 'SH', 'CI'])).astype(int)
ph['h'] = ev.isin(['1B', '2B', '3B', 'HR']).astype(int)
ph['tb'] = ev.map({'1B': 1, '2B': 2, '3B': 3, 'HR': 4}).fillna(0)
for e in ['HR', 'BB', 'K', 'IBB', 'HBP']: ph[e.lower()] = (ev == e).astype(int)
ph['onbase'] = ev.isin(['1B', '2B', '3B', 'HR', 'BB', 'IBB', 'HBP']).astype(int)
ph['sf'] = (ev == 'SF').astype(int)
ph.to_pickle('data/ph_pa.pkl')
g = ph.groupby(['batter', 'season'], observed=True)
ps = g.agg(pa=('r', 'size'), ab=('ab', 'sum'), h=('h', 'sum'), tb=('tb', 'sum'), hr=('hr', 'sum'), bb=('bb', 'sum'),
           k=('k', 'sum'), hbp=('hbp', 'sum'), sf=('sf', 'sum'), onbase=('onbase', 'sum'),
           bat_runs=('r', 'sum'), rar=('rar', 'sum'), phwar_n=('win_n', 'sum'), phwar=('win_l', 'sum'),
           wpa=('wpa', 'sum'), avg_li=('li', 'mean'), re24=('re24', 'sum'), team=('bat_team', lambda s: s.mode().iat[0])).reset_index()
ps['name'] = ps.batter.map(names)
ps['avg'] = ps.h / ps.ab.replace(0, np.nan)
ps['obp'] = ps.onbase / (ps.ab + ps.bb + ps.hbp + ps.sf).replace(0, np.nan)
ps['slg'] = ps.tb / ps.ab.replace(0, np.nan)
ps['ops'] = ps.obp + ps.slg
ps['runs_per_100pa'] = 100 * ps.bat_runs / ps.pa
ps['clutch_wins'] = ps.wpa - (ps.bat_runs * ps.avg_li / ps.season.map(const.rpw))  # WPA beyond leverage-weighted neutral runs
ps = ps.sort_values(['season', 'phwar'], ascending=[True, False])
ps.round(4).to_csv('data/ph_player_season.csv', index=False)
career = ps.groupby(['batter', 'name']).agg(seasons=('season', 'nunique'), pa=('pa', 'sum'), phwar=('phwar', 'sum'),
        phwar_n=('phwar_n', 'sum'), wpa=('wpa', 'sum'), h=('h', 'sum'), ab=('ab', 'sum'), hr=('hr', 'sum'),
        bat_runs=('bat_runs', 'sum')).reset_index()
career['avg'] = career.h / career.ab; career['runs_per_100pa'] = 100 * career.bat_runs / career.pa
career.sort_values('phwar', ascending=False).round(4).to_csv('data/ph_career.csv', index=False)
cols = ['game','date','season','bat_team','inning','half','outs','b1','b2','b3','diff','batter','pitcher','reliever','event','runs',
        're24','lw','r','we_b','we_a','wpa','li']
out = ph[cols].copy(); out['batter_name'] = out.batter.map(names); out['pitcher_name'] = out.pitcher.map(names)
out.round(4).to_csv('data/ph_plate_appearances.csv', index=False)
print(len(out), 'PH PAs;', ps.shape, 'player-seasons')
print('Population sums by season (phWAR_n, phWAR):'); print(ps.groupby('season')[['phwar_n','phwar']].sum().round(1).T.to_string())
print(career.sort_values('phwar', ascending=False).head(12)[['name','seasons','pa','phwar','phwar_n','wpa','avg']].round(2).to_string())
print(ps[ps.pa >= 40].sort_values('phwar', ascending=False).head(8)[['name','season','pa','avg','obp','slg','phwar','phwar_n','wpa','avg_li']].round(2).to_string())
print(ph.groupby('reliever').r.agg(['mean','size']))
print('mean LI of PH PAs:', ph.li.mean(), 'median', ph.li.median())
