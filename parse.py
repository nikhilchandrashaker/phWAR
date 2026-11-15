"""Retrosheet event-file parser -> one row per batter event (plate appearance)."""
import re, glob, sys, os
import pandas as pd
from multiprocessing import Pool

ADV = re.compile(r'([B123])([-X])([123H])(.*)')
RUNNER_ONLY = ('SB','CS','PO','PB','WP','BK','OA','DI','FLE')

def parse_event(ev, bases, batter):
    ev = re.sub(r'[!?#]', '', ev)
    main, adv = (ev.split('.', 1) + [''])[:2] if '.' in ev else (ev, '')
    mods = main.split('/')
    toks = re.split(r'[+;]', mods[0]); modset = mods[1:]
    first = toks[0]
    dest = {b: b for b in (1, 2, 3) if bases[b]}
    bdest = None; etype = None; runner_toks = toks[1:]
    if first == '' or first.startswith('NP'):
        return None
    if first.startswith(RUNNER_ONLY):
        runner_toks = toks
    else:
        if first.startswith('HP'): etype, bdest = 'HBP', 1
        elif first.startswith('H'): etype, bdest = 'HR', 'H'
        elif first.startswith('S'): etype, bdest = '1B', 1
        elif first.startswith('D'): etype, bdest = '2B', 2
        elif first.startswith('T'): etype, bdest = '3B', 3
        elif first.startswith('IW') or first == 'I': etype, bdest = 'IBB', 1
        elif first.startswith('W'): etype, bdest = 'BB', 1
        elif first.startswith('K'): etype, bdest = 'K', 'OUT'
        elif first.startswith('FC'): etype, bdest = 'FC', 1
        elif first.startswith('E'): etype, bdest = 'ROE', 1
        elif first.startswith('C'): etype, bdest = 'CI', 1
        elif first[0].isdigit():
            if 'E' in first: etype, bdest = 'ROE', 1
            else:
                marks = re.findall(r'\((.)\)', first)
                for m in marks:
                    if m in '123' and int(m) in dest: dest[int(m)] = 'OUT'
                if 'B' in marks or not first.endswith(')'):
                    etype, bdest = 'OUT', 'OUT'
                    if 'SH' in modset: etype = 'SH'
                    elif 'SF' in modset: etype = 'SF'
                else: etype, bdest = 'FC', 1
        else:
            return None
        if etype == 'HR':
            for b in dest: dest[b] = 'H'
        if etype in ('BB', 'IBB', 'HBP', 'CI'):
            if 1 in dest:
                dest[1] = 2
                if 2 in dest:
                    dest[2] = 3
                    if 3 in dest: dest[3] = 'H'
    for t in runner_toks:
        err = re.search(r'\([^)]*E[^)]*\)', t) is not None
        if t.startswith('SB'):
            b = t[2:3]
            if b == 'H':
                if 3 in dest: dest[3] = 'H'
            elif b.isdigit() and int(b) - 1 in dest: dest[int(b) - 1] = int(b)
        elif t.startswith('POCS'):
            b = t[4:5]
            if not err and b.isdigit():
                s = 3 if b == 'H' else int(b) - 1
                if s in dest: dest[s] = 'OUT'
        elif t.startswith('CS'):
            b = t[2:3]
            if not err:
                s = 3 if b == 'H' else (int(b) - 1 if b.isdigit() else 0)
                if s in dest: dest[s] = 'OUT'
        elif t.startswith('PO'):
            b = t[2:3]
            if not err and b.isdigit() and int(b) in dest: dest[int(b)] = 'OUT'
        elif t.startswith('BK'):
            for b in sorted(dest, reverse=True): dest[b] = 'H' if b == 3 else b + 1
    if etype != 'HR' or adv:
        for a in (adv.split(';') if adv else []):
            m = ADV.match(a.strip())
            if not m: continue
            src, kind, dst, rest = m.groups()
            err = 'E' in rest
            val = 'OUT' if (kind == 'X' and not err) else (dst if dst == 'H' else int(dst))
            if src == 'B':
                if etype is not None and etype != 'HR': bdest = val
            elif int(src) in dest and etype != 'HR': dest[int(src)] = val
    outs = 0; runs = 0; newb = {1: None, 2: None, 3: None}
    for s in (3, 2, 1):
        if s in dest:
            d = dest[s]
            if d == 'OUT': outs += 1
            elif d == 'H': runs += 1
            else: newb[d] = bases[s]
    if etype is not None:
        if bdest == 'OUT': outs += 1
        elif bdest == 'H': runs += 1
        elif bdest is not None: newb[bdest] = batter
    return etype, outs, runs, newb

COLS = ['game','date','bat_team','home','inning','half','outs','b1','b2','b3','diff','batter','pitcher',
        'reliever','ph','event','runs','outs_after','a1','a2','a3','inn_before','inn_total']

def parse_file(path):
    rows = []; names = {}
    lines = open(path, encoding='latin-1').read().splitlines()
    G = None
    def close_half():
        for i in range(G['hstart'], len(G['rows'])): G['rows'][i][22] = G['inn_runs']
        G['hstart'] = len(G['rows'])
    def flush():
        if G is None: return
        close_half()
        hw = int(G['score'][1] > G['score'][0])
        for k, r in enumerate(G['rows']): r.append(hw); r.append(int(k == len(G['rows']) - 1))
        rows.extend(G['rows'])
    for ln in lines:
        if ln.startswith('id,'):
            flush()
            G = dict(id=ln[3:].strip(), rows=[], score=[0, 0], pit=[None, None], starter=[None, None],
                     ph=set(), bases={1: None, 2: None, 3: None}, outs=0, cur=None, radj=[],
                     vis='', home='', date='', hstart=0, inn_runs=0)
        elif G is None: continue
        elif ln.startswith('info,visteam'): G['vis'] = ln.split(',')[2]
        elif ln.startswith('info,hometeam'): G['home'] = ln.split(',')[2]
        elif ln.startswith('info,date'): G['date'] = ln.split(',')[2]
        elif ln.startswith(('start,', 'sub,')):
            p = ln.split(',')
            pid, nm, tm, pos = p[1], p[2].strip('"'), int(p[3]), int(p[5])
            names[pid] = nm
            if pos == 1:
                G['pit'][tm] = pid
                if G['starter'][tm] is None: G['starter'][tm] = pid
            if ln.startswith('sub,') and pos == 11: G['ph'].add((tm, pid))
        elif ln.startswith('radj,'):
            p = ln.split(','); G['radj'].append((p[1], int(p[2])))
        elif ln.startswith('play,'):
            p = ln.split(',', 6)
            inn, tm, bat, ev = int(p[1]), int(p[2]), p[3], p[6]
            if G['cur'] != (inn, tm):
                if G['cur'] is not None: close_half()
                G['inn_runs'] = 0
                G['cur'] = (inn, tm); G['outs'] = 0
                G['bases'] = {1: None, 2: None, 3: None}
                for pid, b in G['radj']: G['bases'][b] = pid
                G['radj'] = []
            bases = G['bases']
            res = parse_event(ev, bases, bat)
            if res is None: continue
            etype, outs, runs, newb = res
            if etype is not None:
                isph = (tm, bat) in G['ph']
                if isph: G['ph'].discard((tm, bat))
                pit = G['pit'][1 - tm]
                G['rows'].append([G['id'], G['date'], G['home'] if tm else G['vis'], G['home'], inn, tm, G['outs'],
                    int(bool(bases[1])), int(bool(bases[2])), int(bool(bases[3])), G['score'][tm] - G['score'][1 - tm],
                    bat, pit, int(pit != G['starter'][1 - tm]), int(isph), etype, runs, G['outs'] + outs,
                    int(bool(newb[1])), int(bool(newb[2])), int(bool(newb[3])), G['inn_runs'], 0])
            else:
                pass
            G['score'][tm] += runs; G['inn_runs'] += runs
            G['outs'] += outs
            G['bases'] = newb
    flush()
    return rows, names

if __name__ == '__main__':
    import pickle
    names = {}
    for y in range(2010, 2026):
        rows = []
        for f in sorted(glob.glob(f'raw/{y}???.EV?')):
            if re.search(r'(AS|WS|CS|D\d|W\d)\.EVE', f): continue
            r, n = parse_file(f); rows += r; names.update(n)
        df = pd.DataFrame(rows, columns=COLS + ['home_win', 'last'])
        df['season'] = y
        df.to_pickle(f'data/events_{y}.pkl')
        print(y, df.shape, df.runs.sum() / df.game.nunique() / 2, flush=True)
        del rows, df
    pd.Series(names).to_frame('name').to_csv('data/names.csv')
