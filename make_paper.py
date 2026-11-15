import json, pandas as pd, matplotlib, os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
fd = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data/fonts/ttf')
for n, f in [('Serif', 'DejaVuSerif.ttf'), ('Serif-B', 'DejaVuSerif-Bold.ttf'), ('Serif-I', 'DejaVuSerif-Italic.ttf'), ('Sans', 'DejaVuSans.ttf'), ('Sans-B', 'DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(n, f'{fd}/{f}'))
pdfmetrics.registerFontFamily('Serif', normal='Serif', bold='Serif-B', italic='Serif-I', boldItalic='Serif-B')
R = json.load(open('data/results.json')); ps = pd.read_csv('data/ph_player_season.csv'); c = pd.read_csv('data/season_constants.csv', index_col=0)
B = ParagraphStyle('b', fontName='Serif', fontSize=9.4, leading=14, spaceAfter=7, alignment=4)
H1 = ParagraphStyle('h1', fontName='Sans-B', fontSize=13, leading=16, spaceBefore=12, spaceAfter=6, keepWithNext=1, textColor=colors.HexColor('#1f3a5f'))
H2 = ParagraphStyle('h2', fontName='Sans-B', fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=4, keepWithNext=1, textColor=colors.HexColor('#1f3a5f'))
T = ParagraphStyle('t', fontName='Sans-B', fontSize=19, leading=23, spaceAfter=4, textColor=colors.HexColor('#1f3a5f'))
AU = ParagraphStyle('au', fontName='Sans', fontSize=9, leading=12, textColor=colors.HexColor('#586873'), spaceAfter=10)
AB = ParagraphStyle('ab', parent=B, fontSize=9, leading=13, leftIndent=18, rightIndent=18)
CP = ParagraphStyle('cp', fontName='Sans', fontSize=8, leading=10.5, textColor=colors.HexColor('#444444'), spaceAfter=10)
EQ = ParagraphStyle('eq', fontName='Serif-I', fontSize=10, leading=14, alignment=1, spaceAfter=8)
TC = ParagraphStyle('tc', fontName='Sans', fontSize=7.8, leading=9.5)
P = lambda t, s=B: Paragraph(t, s)
def fig(n, cap, w=6.4):
    from PIL import Image as PI
    im = PI.open(f'figures/{n}'); r = im.height / im.width
    return KeepTogether([Image(f'figures/{n}', width=w * inch, height=w * r * inch), P(cap, CP)])
def tbl(data, widths, hdr=True):
    t = Table([[Paragraph(str(x), TC) for x in r] for r in data], colWidths=[w * inch for w in widths], repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f3a5f')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('LINEBELOW', (0, 0), (-1, -1), .25, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    for i in range(len(data[0])): pass
    return t
cd, rl, pr, us, nz, we = R['cold'], R['reliability'], R['predict'], R['usage'], R['noise'], R['we_metrics']
wsum = ps.phwar.sum(); wnsum = ps.phwar_n.sum()
S = []
S += [P('phWAR: A Leverage-Aware Value Metric for Pinch Hitters, Built from Retrosheet Play-by-Play, 2010–2025', T),
      P('Technical report accompanying the phWAR dataset, dashboard and code', AU)]
S += [P('<b>Abstract.</b> Pinch hitting is the one offensive role that standard Wins Above Replacement does not isolate: a pinch-hit plate appearance is simply folded into a player’s season total. We construct phWAR, a pinch-hitter-specific value metric, from every plate appearance in Retrosheet event files for 2010–2025 '
         f'({R["n_pa_total"]:,} plate appearances, of which {R["n_ph"]:,} are pinch-hit appearances). phWAR converts park-adjusted linear-weight run values into wins above a replacement-level bat and weights each appearance by a model-based leverage index. '
         f'Pinch-hit appearances run about {abs(R["ph_r_pa"] - R["all_r_pa"]) * 100:.1f} runs per 100 plate appearances below the average plate appearance. Using a paired design on {cd["n_players"]} hitters, we attribute about {abs(cd["selection"]) * 100:.2f} of that gap to who is chosen to pinch hit, {abs(cd["reliever"]) * 100:.2f} to facing relievers, and '
         f'{abs(cd["cold"]) * 100:.2f} (95% CI {abs(cd["ci_cold"][1]) * 100:.2f} to {abs(cd["ci_cold"][0]) * 100:.2f}) to a residual cold-off-the-bench effect. Season-level pinch-hit performance is barely repeatable (split-half reliability {rl["ph_full"]:.2f}), so single-season phWAR carries large uncertainty; we recommend reporting it with an interval.', AB)]
S += [P('1. Introduction', H1),
      P('Wins Above Replacement (WAR) estimates a player’s total contribution relative to a freely available replacement. Baseball-Reference’s version builds position-player value from batting runs, baserunning, fielding, a positional adjustment and league and park context, then converts runs to wins. Pinch hitters have no positional role, so their value is spread across the same batting-runs term as everyone else’s. A manager’s decision to use a bat in the eighth inning with the tying run on base is a different act from a regular’s routine third plate appearance, yet neither WAR variant separates them.'),
      P('This report builds a stand-alone metric for pinch hitters and uses the resulting dataset to answer four questions. How large is the pinch-hit performance gap, and what drives it? How much leverage do pinch-hit appearances carry? Do managers allocate better hitters to higher-leverage spots? And how much of a player’s single-season pinch-hit record reflects repeatable skill?')]
S += [P('2. Data', H1),
      P(f'We parse Retrosheet event files, as redistributed by the Chadwick Baseball Bureau, for every regular-season game from 2010 through 2025. Postseason and all-star files are excluded. A custom parser tracks the base-out state, score, inning, active pitcher and lineup substitutions through every game, and emits one row per batter event. A plate appearance is flagged as pinch hitting when the batter entered through a substitution recorded at the pinch-hitter position and the appearance is his first after entering. '
        f'Validation against published totals is close: the 2023 parse yields 5,868 home runs and 41,843 strikeouts, matching the official league totals, and parsed runs per team-game are within about 1% of official figures in every season. The 2020 season has only 60 games and is retained with its own run environment. The resulting file contains {R["n_games"]:,} games.')]
S += [P('3. Method', H1), P('3.1 Run values', H2),
      P('For each season we compute run expectancy (RE24) from the 24 base-out states, using runs scored in the remainder of the half-inning and excluding walk-off-truncated innings. The change in run expectancy plus runs scored gives the RE24 value of every plate appearance. Averaging RE24 by event type and season yields linear weights, and each plate appearance receives the weight of its event as its context-neutral run value. We subtract a simple park adjustment based on a three-year, 50%-shrunk home/away run ratio. The result, <i>r</i>, is a park-adjusted run value relative to the league-average plate appearance.'),
      fig('fig02_run_values.png', 'Figure 2. Run expectancy by base-out state (left) and linear weights by event (right).'),
      P('3.2 Win expectancy and leverage', H2),
      P(f'We fit a gradient-boosted classifier for the probability that the home team wins from the state (inning, half, outs, base occupancy, score difference), with a monotonic constraint on score difference. Trained on 2010–2022 and tested on 2023–2025, it attains a Brier score of {we["brier"]:.3f} against {we["base_brier"]:.3f} for a constant predictor and a log-loss of {we["logloss"]:.3f}. We then refit on all seasons. Win Probability Added (WPA) for each plate appearance is the change in the batting team’s win probability. '
        'The leverage index of a state is the expected absolute win-probability swing of a plate appearance there, estimated with a second gradient-boosted model and normalized so that the average plate appearance has leverage 1.'),
      fig('fig03_win_expectancy.png', 'Figure 3. Held-out calibration of the win-expectancy model (left) and its surface for the home team in the bottom half with no outs and bases empty (right).'),
      fig('fig04_leverage.png', 'Figure 4. Leverage by game state (left) and the distribution of leverage for pinch-hit versus other plate appearances (right).')]
S += [P('3.3 Definition of phWAR', H2),
      P('Let <i>r<sub>i</sub></i> be the park-adjusted run value of pinch-hit appearance <i>i</i>, <i>ρ</i> the replacement rate, <i>LI<sub>i</sub></i> its leverage index and <i>RPW</i> the season’s runs per win. We define two quantities:'),
      P('phWAR-N = Σ (r<sub>i</sub> − ρ) / RPW &nbsp;&nbsp;&nbsp;&nbsp; phWAR = Σ (r<sub>i</sub> − ρ) · LI<sub>i</sub> / RPW', EQ),
      P('phWAR-N is the context-neutral value of the bat; phWAR is its value in the situations the manager actually used it, since a run produced at leverage 2 changes the win probability about twice as much as a run at leverage 1. We set <i>ρ</i> = −20 runs per 600 plate appearances relative to the average plate appearance, the standard replacement convention, and take RPW = 2.22 times season runs per team-game (about 9.0 to 10.7 across the sample). '
        f'Because pinch hitters as a group average roughly {R["ph_r_pa"] * 600:.0f} runs per 600 PA, the average pinch hitter sits slightly above this replacement line. By construction, phWAR is a batting-only quantity: it excludes the baserunning, defense and positional terms of full WAR.')]
S += [P('4. Results', H1), P('4.1 What pinch hitting looks like', H2),
      P(f'Teams averaged {R["ph_per_game"]:.2f} pinch-hit plate appearances per game (both teams combined), {R["ph_late_share"] * 100:.0f}% of them in the seventh inning or later. Pinch hitters strike out {R["ph_k_rate"] * 100:.1f}% of the time against {R["non_k_rate"] * 100:.1f}% for other plate appearances, and their mean leverage is {R["ph_li_mean"]:.2f}, although the median is only {R["ph_li_median"]:.2f}: many pinch-hit spots are routine, a minority are extremely high-leverage.'),
      fig('fig05_profile.png', 'Figure 5. Pinch-hit usage by season and inning, and outcome mix versus other plate appearances.', 6.6)]
top = [['Player', 'Seasons', 'PH PA', 'phWAR', 'phWAR-N', 'WPA']] + [[r['name'], r['seasons'], r['pa'], f'{r["phwar"]:+.2f}', f'{r["phwar_n"]:+.2f}', f'{r["wpa"]:+.2f}'] for r in R['top_career']]
ts = [['Player', 'Season', 'PH PA', 'AVG/OBP/SLG', 'phWAR', 'phWAR-N', 'WPA']] + [[r['name'], r['season'], r['pa'], f'{r["avg"]:.3f}/{r["obp"]:.3f}/{r["slg"]:.3f}', f'{r["phwar"]:+.2f}', f'{r["phwar_n"]:+.2f}', f'{r["wpa"]:+.2f}'] for r in R['top_seasons']]
S += [P('4.2 Leaders', H2),
      P(f'Across {R["n_player_seasons"]:,} player-seasons, league-wide pinch-hit value sums to {wsum:+.0f} phWAR ({wnsum:+.0f} context-neutral) over sixteen seasons, which is small: pinch hitting is a modest part of the game. Leaders are mostly bench specialists with long careers (Table 1) and a few unusually productive seasons (Table 2). Leverage and neutral value correlate at {R["corr"]["n_vs_l"]:.2f} across player-seasons with at least 20 PH PA, while phWAR tracks observed WPA more closely ({R["corr"]["l_vs_wpa"]:.2f}).'),
      P('<b>Table 1.</b> Career phWAR leaders, 2010–2025.', CP), tbl(top, [1.9, .7, .7, .8, .9, .7]), Spacer(1, 8),
      P('<b>Table 2.</b> Best single seasons (minimum 25 PH PA).', CP), tbl(ts, [1.5, .6, .6, 1.4, .7, .8, .6]), Spacer(1, 8),
      fig('fig08_leaderboards.png', 'Figure 8. Career and single-season leaders. Bars are phWAR; dots are context-neutral phWAR-N.', 6.6), fig('fig09_relationships.png', 'Figure 9. Context-neutral versus leverage-weighted value (left) and phWAR versus observed WPA (right). Marker area scales with plate appearances.')]
S += [P('4.3 Why pinch hitters underperform', H2),
      P(f'A pinch hitter differs from the average batter in three ways: he is a particular kind of hitter (selection), he usually faces a reliever rather than the starter (opponent), and he enters without having batted earlier in the game (the “cold” effect). We separate them with a paired design on {cd["n_players"]} hitters (a somewhat better-than-typical group, so the total gap here, {abs(cd["total"]) * 100:.2f} runs per 100 PA, is smaller than the all-hitter gap) with at least 30 PH PA, 300 other PA and 150 other PA against relievers. For each hitter we compare his pinch-hit run value with his run value in non-pinch-hit appearances against relievers, and weight by pinch-hit PA. '
        f'Selection accounts for {cd["selection"] * 100:+.2f} runs per 100 PA, relievers {cd["reliever"] * 100:+.2f}, and the residual cold effect {cd["cold"] * 100:+.2f} (95% bootstrap interval {cd["ci_cold"][0] * 100:+.2f} to {cd["ci_cold"][1] * 100:+.2f}), or about {abs(cd["cold_per600"]):.0f} runs over 600 PA. '
        'The cold estimate is probably conservative: managers often choose pinch hitters for a favorable platoon matchup, which would raise their performance, and we do not observe handedness.'),
      fig('fig06_cold_bench.png', 'Figure 6. Decomposition of the pinch-hit performance gap, runs per 100 PA, with 95% bootstrap intervals.', 5.6)]
S += [P('4.4 Do managers use better hitters in bigger spots?', H2),
      P(f'Yes, modestly. Sorting pinch-hit appearances into leverage quintiles, the hitters’ own non-pinch-hit run value rises monotonically from {us["talent_by_li_quintile"][0] * 100:+.2f} in the lowest quintile to {us["talent_by_li_quintile"][-1] * 100:+.2f} runs per 100 PA in the highest (Figure 11). The relationship at the appearance level is weak (correlation {us["corr"]:.2f}), so most variation in leverage reflects the game rather than choices about whom to send.'),
      fig('fig11_usage.png', 'Figure 11. Quality of the hitter by leverage quintile of the pinch-hit appearance.', 4.3)]
S += [P('4.5 How repeatable is pinch-hit performance?', H2),
      P(f'Randomly splitting each hitter’s pinch-hit appearances into halves (hitters with at least 60 PH PA, n = {rl["n"]}) gives a Spearman–Brown reliability of {rl["ph_full"]:.2f}; for the same number of randomly chosen non-pinch-hit appearances it is {rl["non_full"]:.2f}. Both are low because run value per plate appearance is noisy (standard deviation {nz["sd_r_per_pa"]:.2f} runs). '
        f'In a season-to-season forecast of pinch-hit run value ({pr["n"]} paired seasons, five-fold cross-validation), neither last year’s pinch-hit rate, last year’s overall rate, nor a blend improved on the league mean (out-of-sample RMSE about {pr["rmse"]["League PH mean"] * 100:.2f} runs per 100 PA in every case). '
        f'The standard error of phWAR-N for a 40-PA season is about {nz["se_phwar_40pa"]:.2f} wins, comparable to the whole value of a good bench season.'),
      fig('fig07_reliability.png', 'Figure 7. Split-half reliability (left) and out-of-sample forecast error (right).', 6.4)]
sr = R['sum_by_repl']
S += [P('4.6 Sensitivity to replacement level', H2),
      P(f'The location of the replacement line moves the league total (from {sr["0"]:+.0f} phWAR at 0 runs per 600 PA to {sr["-40"]:+.0f} at −40) but barely reorders players: Spearman correlations of career rankings against the baseline range from {min(R["sensitivity"].values()):.2f} to 1.00 (Figure 10). Rankings are therefore robust, while the absolute scale is a convention.'),
      fig('fig10_sensitivity.png', 'Figure 10. Total phWAR and ranking stability under alternative replacement levels.', 6.2)]
S += [P('5. Discussion and limitations', H1),
      P('phWAR answers “what was this bat worth in the spots it was used,” which blends skill and opportunity. phWAR-N isolates the skill-like component but is not the better measure of value delivered; managers’ allocation of leverage is part of what a team gets from its bench. Several limitations matter. The run values are batting-only, so a pinch hitter’s baserunning is ignored, as are the pinch runner and the defensive replacement who often follow. '
        'Park factors are coarse, the win-expectancy model pools sixteen run environments, and runs-per-win is a linear approximation. Handedness, pitcher quality and times-through-the-order are not modeled, so the opponent effect in Section 4.3 is measured only as reliever versus starter. Pinch-hit status is inferred from substitution records and covers only the first appearance after entry. '
        'Finally, the −20 runs per 600 PA replacement level is borrowed from conventional WAR rather than estimated for bench bats.'),
      P('The practical conclusion is cautious. Career and multi-year phWAR identify real bench specialists, but a single season rarely distinguishes a good pinch hitter from an average one, and team decisions about whom to use are better informed by a hitter’s overall quality than by his pinch-hit record alone.'),
      P('6. Reproducibility', H1),
      P('All code and derived tables are provided: <i>fetch.py</i> downloads the event files, <i>parse.py</i> produces plate-appearance rows, <i>build.py</i> computes RE24, win expectancy, leverage and WPA, <i>compute.py</i> aggregates phWAR, and <i>analysis.py</i> produces the figures and statistics. The data are used under Retrosheet’s terms: the information was obtained free of charge from, and is copyrighted by, Retrosheet (www.retrosheet.org).'),
      P('References', H1)]
for r in ['Baseball-Reference. “WAR Explained.” Baseball-Reference.com.', 'Retrosheet. Play-by-play event files. www.retrosheet.org; Chadwick Baseball Bureau redistribution, github.com/chadwickbureau/retrosheet.',
          'Tango, T., Lichtman, M. and Dolphin, A. (2007). <i>The Book: Playing the Percentages in Baseball</i>. Potomac Books.', 'Pedregosa, F. et al. (2011). Scikit-learn: Machine learning in Python. <i>Journal of Machine Learning Research</i> 12, 2825–2830.']:
    S.append(P(r, ParagraphStyle('r', parent=B, fontSize=8.5, leading=12, leftIndent=12, firstLineIndent=-12, alignment=0)))
def foot(cv, d):
    cv.saveState(); cv.setFont('Sans', 7.5); cv.setFillColor(colors.HexColor('#777777')); cv.drawCentredString(letter[0] / 2, .5 * inch, f'phWAR technical report · page {d.page}'); cv.restoreState()
doc = SimpleDocTemplate('/mnt/user-data/outputs/phwar_research_paper.pdf', pagesize=letter, leftMargin=.95 * inch, rightMargin=.95 * inch, topMargin=.85 * inch, bottomMargin=.85 * inch, title='phWAR: A Leverage-Aware Value Metric for Pinch Hitters', author='phWAR project')
doc.build([S[0], S[1]] + S[2:], onFirstPage=foot, onLaterPages=foot); print('built')
