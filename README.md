# phWAR: a pinch-hitter value metric, 2010–2025

phWAR measures how much a pinch hitter is worth, in wins, compared with a replacement-level bat. It is built from every regular-season plate appearance in Retrosheet play-by-play data for 2010–2025 (2.83 million plate appearances, 76,233 of them pinch hits).

**Headline findings**

- Pinch-hit appearances run about 2.5 runs per 100 PA below the average plate appearance. In a paired study of 741 hitters, about 0.24 of the gap comes from *who* is sent to pinch hit, 0.69 from facing relievers, and 0.98 (95% CI 0.60 to 1.36) from a residual "cold off the bench" effect, roughly 6 runs per 600 PA.
- Pinch-hit spots carry an average leverage index of 1.25, and 82% occur in the 7th inning or later.
- Managers do send somewhat better hitters into higher-leverage spots.
- Single-season pinch-hit performance is mostly noise (split-half reliability 0.18; a 40-PA season has about ±0.25 wins of sampling error). Use multi-year phWAR or report an interval.

## Contents

| Path | What it is |
|---|---|
| `phwar_dashboard.html` | Self-contained interactive dashboard (leaders, player lookup, findings). Needs internet only for Chart.js and fonts. |
| `phwar_research_paper.pdf` | Technical report with methods, validation, results and limitations |
| `phwar_slides.pptx` | 9-slide summary deck |
| `figures/*.png` | All figures and diagrams (11 PNGs, 200 dpi) |
| `data/` | The dataset (see below) |
| `code/` | Pipeline scripts, in run order |

## Dataset

| File | Rows | Description |
|---|---|---|
| `ph_plate_appearances.csv` | 76,233 | One row per pinch-hit PA with game state, outcome, run value, win probability and leverage |
| `ph_player_season.csv` | 9,078 | Player-season stats and phWAR |
| `ph_career.csv` | 2,326 | Career totals, 2010–2025 |
| `re24_matrix.csv` | 384 | Run expectancy by season, outs and base state |
| `linear_weights.csv` | 224 | Run value of each event type, by season |
| `park_factors.csv` | 480 | Park factor by home team and season |
| `season_constants.csv` | 16 | Runs per game, runs per win, PH counts |
| `results.json` | – | Every statistic quoted in the paper |
| `names.csv` | – | Retrosheet player id to name |

### `ph_plate_appearances.csv` columns

`game` Retrosheet game id · `date` · `season` · `bat_team` · `inning` · `half` (0 top, 1 bottom) · `outs` before the PA · `b1,b2,b3` runner on each base before the PA · `diff` batting team's lead before the PA · `batter`, `pitcher` Retrosheet ids (`batter_name`, `pitcher_name` too) · `reliever` 1 if the pitcher was not his team's starter · `event` outcome (`1B,2B,3B,HR,BB,IBB,HBP,K,OUT,SF,SH,FC,ROE,CI`) · `runs` scored on the play · `re24` change in run expectancy plus runs · `lw` linear-weight run value of the event · `r` park-adjusted run value (`lw` plus park adjustment) · `we_b`, `we_a` home win probability before and after · `wpa` Win Probability Added for the batting team · `li` leverage index (league average = 1).

### `ph_player_season.csv` columns

`batter` id, `name`, `season`, `team` (most frequent), `pa, ab, h, tb, hr, bb, k, hbp, sf, onbase`, `avg, obp, slg, ops`, `bat_runs` (sum of `r`), `rar` (runs above replacement), `phwar_n` (context-neutral), `phwar` (leverage-weighted), `wpa`, `avg_li`, `re24`, `runs_per_100pa`, `clutch_wins` (WPA minus leverage-weighted neutral wins).

## Method in brief

1. **Parse** Retrosheet event files into one row per batter event, tracking base-out state, score, pitcher and substitutions. A pinch-hit PA is the first PA after a substitution at the pinch-hitter position.
2. **Run values:** season RE24 matrices, then linear weights by event; subtract a shrunk three-year park adjustment to get `r`.
3. **Win probability and leverage:** gradient-boosted models (scikit-learn) trained on all plate appearances. Held-out (2023–25) Brier score 0.159 vs 0.250 baseline.
4. **phWAR:** `phWAR-N = Σ (r − ρ) / RPW` and `phWAR = Σ (r − ρ) · LI / RPW`, with ρ = −20 runs per 600 PA and RPW = 2.22 × runs per team-game.

## Reproduce

```bash
pip install pandas numpy scikit-learn matplotlib reportlab pillow
python code/fetch.py        # downloads Retrosheet event files (~175 MB)
python code/parse.py        # -> data/events_YYYY.pkl
python code/build.py        # RE24, win expectancy, leverage, WPA
python code/compute.py      # phWAR tables and CSVs
python code/analysis.py     # figures + results.json
python code/make_paper.py   # PDF (needs DejaVu fonts via matplotlib)
```

Run on one CPU in a few minutes; `build.py` needs about 3 GB of RAM.

## Limitations

phWAR is batting-only (no baserunning, defense or pinch-running). Park factors are coarse, the win-expectancy model is pooled across eras, and runs per win is linear. Handedness and pitcher quality are not modeled, so the platoon effect is absorbed into the "cold" estimate (which is probably conservative). The replacement level is borrowed from conventional WAR. Retrosheet scoring is validated but not perfect: parsed 2023 home runs and strikeouts match official totals, while small differences in minor event types are possible.

## Attribution

The information used here was obtained free of charge from and is copyrighted by Retrosheet (www.retrosheet.org), via the Chadwick Baseball Bureau redistribution. Please keep this notice with any redistribution of the data. This project is not affiliated with Baseball-Reference, FanGraphs, MLB or any club.
