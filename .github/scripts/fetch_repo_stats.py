#!/usr/bin/env python3
"""
Fetch GitHub repository statistics including views, clones, stars, forks, and traffic data.
This script runs daily via GitHub Actions to track repository insights over time.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from github import Github

def fetch_repository_stats():
    """Fetch comprehensive repository statistics from GitHub API."""
    
    # Get environment variables
    token = os.environ.get('GITHUB_TOKEN')
    repo_owner = os.environ.get('REPO_OWNER')
    repo_name = os.environ.get('REPO_NAME')
    
    if not all([token, repo_owner, repo_name]):
        raise ValueError("Missing required environment variables")
    
    # Initialize GitHub client
    g = Github(token)
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    
    # Current timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    print(f"📊 Fetching statistics for {repo_owner}/{repo_name}...")
    
    # Fetch basic repository info
    stats = {
        "timestamp": timestamp,
        "repository": {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "url": repo.html_url,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
        },
        "metrics": {
            "stars": repo.stargazers_count,
            "watchers": repo.watchers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "size_kb": repo.size,
        }
    }
    
    # Fetch traffic views (last 14 days)
    try:
        views = repo.get_views_traffic(per="day")
        stats["traffic"] = {
            "views": {
                "count": views.get("count", 0),
                "uniques": views.get("uniques", 0),
                "daily": [
                    {
                        "date": v.timestamp.date().isoformat(),
                        "count": v.count,
                        "uniques": v.uniques
                    }
                    for v in views.get("views", [])
                ]
            }
        }
        print(f"  ✓ Views: {stats['traffic']['views']['count']} total, {stats['traffic']['views']['uniques']} unique")
    except Exception as e:
        print(f"  ⚠ Could not fetch views: {e}")
        stats["traffic"] = {"views": {"error": str(e)}}
    
    # Fetch clone traffic (last 14 days)
    try:
        clones = repo.get_clones_traffic(per="day")
        stats["traffic"]["clones"] = {
            "count": clones.get("count", 0),
            "uniques": clones.get("uniques", 0),
            "daily": [
                {
                    "date": c.timestamp.date().isoformat(),
                    "count": c.count,
                    "uniques": c.uniques
                }
                for c in clones.get("clones", [])
            ]
        }
        print(f"  ✓ Clones: {stats['traffic']['clones']['count']} total, {stats['traffic']['clones']['uniques']} unique")
    except Exception as e:
        print(f"  ⚠ Could not fetch clones: {e}")
        stats["traffic"]["clones"] = {"error": str(e)}
    
    # Fetch popular referrers (top 10)
    try:
        referrers = repo.get_top_referrers()
        stats["referrers"] = [
            {
                "referrer": r.referrer,
                "count": r.count,
                "uniques": r.uniques
            }
            for r in referrers[:10]
        ]
        print(f"  ✓ Top referrers: {len(stats['referrers'])} sources")
    except Exception as e:
        print(f"  ⚠ Could not fetch referrers: {e}")
        stats["referrers"] = []
    
    # Fetch popular content paths (top 10)
    try:
        paths = repo.get_top_paths()
        stats["popular_content"] = [
            {
                "path": p.path,
                "title": p.title,
                "count": p.count,
                "uniques": p.uniques
            }
            for p in paths[:10]
        ]
        print(f"  ✓ Popular content: {len(stats['popular_content'])} paths")
    except Exception as e:
        print(f"  ⚠ Could not fetch popular content: {e}")
        stats["popular_content"] = []
    
    return stats

def save_statistics(stats):
    """Save statistics to JSON files - both daily snapshot and historical append."""
    
    # Create stats directory if it doesn't exist
    stats_dir = Path("stats")
    stats_dir.mkdir(exist_ok=True)
    
    # Save current snapshot
    current_file = stats_dir / "current.json"
    with open(current_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\n💾 Saved current snapshot to {current_file}")
    
    # Append to historical log
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history_file = stats_dir / "history.jsonl"
    
    with open(history_file, 'a') as f:
        f.write(json.dumps(stats) + '\n')
    print(f"💾 Appended to historical log: {history_file}")
    
    # Save monthly summary
    year_month = datetime.now(timezone.utc).strftime("%Y-%m")
    monthly_dir = stats_dir / "monthly"
    monthly_dir.mkdir(exist_ok=True)
    
    monthly_file = monthly_dir / f"{year_month}.json"
    
    # Load existing monthly data or create new
    if monthly_file.exists():
        with open(monthly_file, 'r') as f:
            monthly_data = json.load(f)
    else:
        monthly_data = {
            "month": year_month,
            "snapshots": []
        }
    
    # Add current snapshot
    monthly_data["snapshots"].append({
        "date": date_str,
        "metrics": stats["metrics"],
        "traffic": stats.get("traffic", {}),
    })
    
    # Save monthly file
    with open(monthly_file, 'w') as f:
        json.dump(monthly_data, f, indent=2)
    print(f"💾 Updated monthly summary: {monthly_file}")
    
    # Generate summary report
    generate_summary_report(stats, stats_dir)

def generate_summary_report(stats, stats_dir):
    """Generate a human-readable markdown summary."""
    
    report_file = stats_dir / "SUMMARY.md"
    
    timestamp = datetime.fromisoformat(stats["timestamp"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    with open(report_file, 'w') as f:
        f.write(f"# Repository Statistics Summary\n\n")
        f.write(f"**Last Updated:** {timestamp}\n\n")
        f.write(f"**Repository:** [{stats['repository']['full_name']}]({stats['repository']['url']})\n\n")
        
        # Metrics
        f.write("## 📊 Current Metrics\n\n")
        metrics = stats["metrics"]
        f.write(f"- ⭐ **Stars:** {metrics['stars']:,}\n")
        f.write(f"- 👀 **Watchers:** {metrics['watchers']:,}\n")
        f.write(f"- 🍴 **Forks:** {metrics['forks']:,}\n")
        f.write(f"- 🐛 **Open Issues:** {metrics['open_issues']:,}\n")
        f.write(f"- 📦 **Size:** {metrics['size_kb']:,} KB\n\n")
        
        # Traffic
        if "traffic" in stats and "views" in stats["traffic"]:
            f.write("## 📈 Traffic (Last 14 Days)\n\n")
            views = stats["traffic"]["views"]
            if "count" in views:
                f.write(f"### Views\n")
                f.write(f"- **Total Views:** {views['count']:,}\n")
                f.write(f"- **Unique Visitors:** {views['uniques']:,}\n\n")
            
            if "clones" in stats["traffic"]:
                clones = stats["traffic"]["clones"]
                if "count" in clones:
                    f.write(f"### Clones\n")
                    f.write(f"- **Total Clones:** {clones['count']:,}\n")
                    f.write(f"- **Unique Cloners:** {clones['uniques']:,}\n\n")
        
        # Top referrers
        if stats.get("referrers"):
            f.write("## 🔗 Top Referrers\n\n")
            f.write("| Referrer | Views | Unique Visitors |\n")
            f.write("|----------|-------|------------------|\n")
            for ref in stats["referrers"][:5]:
                f.write(f"| {ref['referrer']} | {ref['count']:,} | {ref['uniques']:,} |\n")
            f.write("\n")
        
        # Popular content
        if stats.get("popular_content"):
            f.write("## 📄 Popular Content\n\n")
            f.write("| Path | Views | Unique Visitors |\n")
            f.write("|------|-------|------------------|\n")
            for content in stats["popular_content"][:5]:
                path = content['path'] or '/'
                f.write(f"| `{path}` | {content['count']:,} | {content['uniques']:,} |\n")
            f.write("\n")
        
        f.write("---\n")
        f.write("*Generated automatically by GitHub Actions*\n")
    
    print(f"📝 Generated summary report: {report_file}")

if __name__ == "__main__":
    try:
        print("🚀 Starting repository statistics collection...\n")
        stats = fetch_repository_stats()
        save_statistics(stats)
        print("\n✅ Successfully collected and saved repository statistics!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
