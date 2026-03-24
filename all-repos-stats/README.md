# Multi-Repository Statistics Hub

This directory contains **centralized statistics for ALL repositories** in the GitHub account, collected and analyzed automatically.

## 🎯 What This Does

Instead of tracking statistics in each individual repository, this system:
- **Discovers** all repositories in your GitHub account
- **Collects** comprehensive statistics from each repository
- **Stores** all data in **one centralized location**
- **Generates** comparative analytics and dashboards
- **Tracks** trends over time across your entire portfolio

## 📁 Directory Structure

```
all-repos-stats/
├── current.json              # Latest snapshot of ALL repositories
├── history.jsonl             # Complete historical log (append-only)
├── SUMMARY.md               # Executive summary dashboard
├── COMPARISON.md            # Side-by-side repository comparison
├── TRENDS.md                # Growth trends and changes
├── TRAFFIC.md               # Traffic analytics summary
├── by-repo/                 # Individual repository histories
│   ├── repo1.json           # 90-day history for repo1
│   ├── repo2.json           # 90-day history for repo2
│   └── ...
└── monthly/                 # Monthly aggregated data
    ├── 2026-03.json
    ├── 2026-04.json
    └── ...
```

## 📊 Data Collected

### For Each Repository:
- ⭐ **Stars, Watchers, Forks**
- 📊 **Open Issues Count**
- 📦 **Repository Size**
- 👀 **Traffic Views** (14-day rolling window)
- 📥 **Clone Statistics** (14-day rolling window)
- 💻 **Language Distribution**
- 🏷️ **Topics/Tags**
- 📅 **Creation, Update, and Push Dates**
- 🔒 **Visibility** (public/private)
- 📝 **Description and Metadata**

### Aggregated Analytics:
- Total stars, forks, watchers across all repos
- Language distribution across your portfolio
- Traffic patterns and trends
- Most popular repositories
- Recent activity summary
- Growth trends over time

## 🤖 Automation

### Automatic Collection
- **Schedule:** Daily at 00:00 UTC
- **Workflow:** `.github/workflows/multi-repo-stats.yml`
- **Script:** `.github/scripts/collect_all_repos_stats.py`

### Manual Trigger
You can run collection manually:
1. Go to **Actions** tab in GitHub
2. Select **"Multi-Repository Statistics Collector"**
3. Click **"Run workflow"**
4. Choose whether to include private repositories
5. Click **"Run workflow"** button

## 📈 Using the Dashboard

### Quick View Reports

**[SUMMARY.md](SUMMARY.md)** - Executive overview:
- Total repositories count
- Aggregate metrics (total stars, forks, etc.)
- Top 10 repositories by stars
- Language distribution
- Recently updated repositories

**[COMPARISON.md](COMPARISON.md)** - Detailed comparison:
- All repositories sorted by stars
- All repositories sorted by forks
- All repositories sorted by size
- All repositories sorted by recent activity

**[TRENDS.md](TRENDS.md)** - Growth analysis:
- Changes in stars and forks over time
- Biggest gainers (repositories with most growth)
- Portfolio-wide trends

**[TRAFFIC.md](TRAFFIC.md)** - Traffic analytics:
- Total views and unique visitors
- Total clones and unique cloners
- Most viewed repositories
- Traffic leaderboard

### Programmatic Access

**Current Snapshot** (`current.json`):
```python
import json

with open('all-repos-stats/current.json', 'r') as f:
    data = json.load(f)

print(f"Total repositories: {data['total_repositories']}")
for repo in data['repositories']:
    print(f"{repo['repository']['name']}: {repo['metrics']['stars']} stars")
```

**Historical Analysis** (`history.jsonl`):
```python
import json

snapshots = []
with open('all-repos-stats/history.jsonl', 'r') as f:
    for line in f:
        snapshots.append(json.loads(line))

# Analyze star growth over time
for snapshot in snapshots:
    total_stars = sum(r['metrics']['stars'] for r in snapshot['repositories'])
    print(f"{snapshot['collection_timestamp']}: {total_stars} stars")
```

**Individual Repository History** (`by-repo/`):
```python
import json

with open('all-repos-stats/by-repo/your-repo-name.json', 'r') as f:
    repo_data = json.load(f)

# Plot stars over time for this specific repo
for entry in repo_data['history']:
    date = entry['date']
    stars = entry['data']['metrics']['stars']
    print(f"{date}: {stars} stars")
```

## 🎨 Customization

### Include/Exclude Repositories

Edit `.github/scripts/collect_all_repos_stats.py`:

```python
# Filter specific repositories
repos = [r for r in user.get_repos() if r.name not in ['temp-repo', 'test-repo']]
```

### Change Collection Schedule

Edit `.github/workflows/multi-repo-stats.yml`:

```yaml
schedule:
  - cron: '0 0 * * *'  # Change cron expression
```

Examples:
- `'0 */6 * * *'` - Every 6 hours
- `'0 0 * * 0'` - Weekly on Sunday
- `'0 0 1 * *'` - Monthly on 1st

### Add Custom Metrics

Edit `collect_all_repos_stats.py` to add more metrics:

```python
# Example: Collect contributor count
try:
    contributors = list(repo.get_contributors())
    stats["metrics"]["contributor_count"] = len(contributors)
except:
    pass
```

## 🔒 Privacy & Permissions

### What Has Access?
- The GitHub Actions workflow uses `GITHUB_TOKEN` (automatically provided)
- This token has access to all repositories you own or have admin access to
- Private repository data is included by default

### Controlling Visibility
- To **exclude private repos**, set `INCLUDE_PRIVATE: 'false'` in workflow
- Traffic data is only available for repos where you have admin access
- All collected data is stored in this repository

### Security Note
- No sensitive tokens or secrets are stored in the data files
- All API calls use GitHub's official API with proper authentication
- Data is stored as plain JSON - review before committing if concerned

## 📊 Example Use Cases

### Portfolio Dashboard
Create a public "portfolio stats" repository that showcases:
- Your total impact (stars, forks across all projects)
- Your most popular projects
- Your coding language preferences
- Growth trends

### Project Prioritization
Identify which repositories are:
- Getting the most traction (stars, forks, traffic)
- Most actively maintained (recent pushes)
- Need attention (high open issues)

### Historical Analysis
Track your GitHub presence over time:
- How fast your portfolio is growing
- Which projects had the biggest impact
- Traffic patterns and seasonality

### Comparative Analysis
Compare metrics across your repositories:
- Which tech stack gets more engagement?
- Correlation between size and popularity
- Language effectiveness

## 🚀 Getting Started

1. **Enable the workflow** (already done by pushing this code)

2. **Run first collection manually:**
   - Go to Actions → "Multi-Repository Statistics Collector" → "Run workflow"

3. **View results:**
   - Check `all-repos-stats/SUMMARY.md` for overview
   - Explore other generated markdown reports

4. **Automate:**
   - Collection runs automatically every day
   - Reports update automatically
   - Historical data accumulates over time

## 💡 Tips

- **Wait 2-3 days** to accumulate enough data for meaningful trend analysis
- **Check SUMMARY.md first** - it's the most readable overview
- **Use history.jsonl** for custom analysis and visualizations
- **Monitor workflow runs** in the Actions tab to ensure successful collection
- **Star growth** and **traffic data** are the most useful metrics for gauging project success

---

*Last updated: Automatically by GitHub Actions*
