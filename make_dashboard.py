import pandas as pd, json, numpy as np
ps = pd.read_csv('data/ph_player_season.csv'); R = json.load(open('data/results.json')); c = pd.read_csv('data/season_constants.csv', index_col=0)
rows = [[r.name, int(r.season), r.team, int(r.pa), int(r.ab), int(r.h), int(r.hr), int(r.bb), int(r.k), round(r.avg, 3) if r.ab else None,
         round(r.obp, 3) if r.obp == r.obp else None, round(r.slg, 3) if r.slg == r.slg else None, round(r.phwar, 2), round(r.phwar_n, 2),
         round(r.wpa, 2), round(r.avg_li, 2)] for r in ps.itertuples()]
seas = ps.groupby('season').agg(pa=('pa', 'sum'), w=('phwar', 'sum'), wn=('phwar_n', 'sum')).reset_index()
li = pd.read_pickle('data/ph_pa.pkl').groupby('season').li.mean()
S = [[int(r.season), int(r.pa), round(r.w, 1), round(r.wn, 1), round(float(li[r.season]), 2)] for r in seas.itertuples()]
D = dict(rows=rows, seasons=S, cold=R['cold'], rel=R['reliability'], usage=R['usage'], noise=R['noise'], pred=R['predict'], nph=R['n_ph'], npa=R['n_pa_total'],
         phli=R['ph_li_mean'], phk=R['ph_k_rate'], nk=R['non_k_rate'], late=R['ph_late_share'])
html = open('dashboard_template.html').read().replace('/*DATA*/null', json.dumps(D, separators=(',', ':')))
open('/mnt/user-data/outputs/phwar_dashboard.html', 'w').write(html); print(len(html) // 1024, 'KB')
