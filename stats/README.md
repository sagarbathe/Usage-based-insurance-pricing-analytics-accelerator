# Repository Statistics

This directory contains automated statistics collection for the repository, updated daily by GitHub Actions.

## 📁 File Structure

```
stats/
├── current.json          # Latest snapshot of all statistics
├── history.jsonl         # Append-only log of all daily snapshots (JSON Lines format)
├── SUMMARY.md           # Human-readable summary report
└── monthly/
    ├── 2026-03.json     # Monthly aggregated data
    ├── 2026-04.json
    └── ...
```

## 📊 Data Collected

### Repository Metrics
- ⭐ Stars
- 👀 Watchers
- 🍴 Forks
- 🐛 Open Issues
- 📦 Repository Size

### Traffic Data (14-day rolling window)
- **Views**: Total and unique page views
- **Clones**: Total and unique repository clones
- Daily breakdown of views and clones

### Popularity Insights
- **Top Referrers**: Where visitors are coming from
- **Popular Content**: Most viewed files and paths

## 🤖 Automation

Statistics are collected automatically via GitHub Actions:
- **Schedule**: Daily at 00:00 UTC
- **Workflow**: `.github/workflows/repo-stats.yml`
- **Script**: `.github/scripts/fetch_repo_stats.py`
- **Manual Trigger**: Available via GitHub Actions UI

## 📈 Using the Data

### View Current Stats
Check `SUMMARY.md` for a human-readable report or `current.json` for programmatic access.

### Historical Analysis
The `history.jsonl` file contains all historical snapshots in JSON Lines format. Each line is a complete snapshot.

Example Python code to analyze trends:
```python
import json
from datetime import datetime

views_over_time = []
with open('stats/history.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        views_over_time.append({
            'date': data['timestamp'],
            'views': data['traffic']['views']['count']
        })

print(f"Total snapshots: {len(views_over_time)}")
```

### Monthly Reports
Check `monthly/` directory for month-by-month aggregated data.

## 🔒 Privacy & Access

- Traffic statistics are only available to repository owners/admins
- The GitHub Actions workflow uses `GITHUB_TOKEN` (automatically provided)
- No sensitive data is collected or stored

---

*Last updated: Automated by GitHub Actions*
