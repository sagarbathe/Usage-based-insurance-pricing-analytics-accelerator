#!/usr/bin/env python3
"""
Collect statistics from ALL repositories in a GitHub account.
Stores data in a centralized location for cross-repository analytics.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from github import Github
import time

def fetch_all_repositories_stats():
    """Fetch statistics from all repositories in the account."""
    
    # Get environment variables
    token = os.environ.get('GITHUB_TOKEN')
    owner = os.environ.get('REPO_OWNER')
    include_private = os.environ.get('INCLUDE_PRIVATE', 'true').lower() == 'true'
    
    if not all([token, owner]):
        raise ValueError("Missing required environment variables")
    
    # Initialize GitHub client
    g = Github(token)
    user = g.get_user(owner)
    
    print(f"🔍 Discovering repositories for {owner}...")
    print(f"   Include private repos: {include_private}\n")
    
    # Get all repositories
    repos = list(user.get_repos())
    if not include_private:
        repos = [r for r in repos if not r.private]
    
    print(f"📊 Found {len(repos)} repositories to analyze\n")
    print("=" * 80)
    
    # Collect stats for each repository
    all_stats = []
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for idx, repo in enumerate(repos, 1):
        print(f"\n[{idx}/{len(repos)}] Processing: {repo.full_name}")
        print("-" * 80)
        
        try:
            stats = collect_repo_stats(repo, timestamp)
            all_stats.append(stats)
            
            # Rate limiting: sleep briefly between repos
            if idx < len(repos):
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  ⚠️  Error collecting stats: {e}")
            all_stats.append({
                "timestamp": timestamp,
                "repository": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "error": str(e)
                }
            })
    
    print("\n" + "=" * 80)
    print(f"✅ Collected statistics from {len(all_stats)} repositories")
    
    return {
        "collection_timestamp": timestamp,
        "owner": owner,
        "total_repositories": len(all_stats),
        "repositories": all_stats
    }

def collect_repo_stats(repo, timestamp):
    """Collect comprehensive statistics for a single repository."""
    
    stats = {
        "timestamp": timestamp,
        "repository": {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "url": repo.html_url,
            "private": repo.private,
            "fork": repo.fork,
            "archived": repo.archived,
            "disabled": repo.disabled,
            "language": repo.language,
            "default_branch": repo.default_branch,
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
            "network_count": repo.network_count,
            "subscribers_count": repo.subscribers_count,
        }
    }
    
    print(f"  📈 Stars: {stats['metrics']['stars']:,} | Forks: {stats['metrics']['forks']:,} | Size: {stats['metrics']['size_kb']:,} KB")
    
    # Try to fetch traffic data (only available for repos you own/admin)
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
        print(f"  👀 Views: {stats['traffic']['views']['count']:,} (unique: {stats['traffic']['views']['uniques']:,})")
    except Exception as e:
        stats["traffic"] = {"views": {"available": False, "reason": "No access or not enough permissions"}}
    
    # Try to fetch clone data
    try:
        clones = repo.get_clones_traffic(per="day")
        if "traffic" not in stats:
            stats["traffic"] = {}
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
        print(f"  📥 Clones: {stats['traffic']['clones']['count']:,} (unique: {stats['traffic']['clones']['uniques']:,})")
    except Exception as e:
        if "traffic" not in stats:
            stats["traffic"] = {}
        stats["traffic"]["clones"] = {"available": False, "reason": "No access or not enough permissions"}
    
    # Fetch languages
    try:
        languages = repo.get_languages()
        stats["languages"] = languages
        if languages:
            print(f"  💻 Languages: {', '.join(list(languages.keys())[:3])}")
    except Exception as e:
        stats["languages"] = {}
    
    # Fetch topics/tags
    try:
        topics = repo.get_topics()
        stats["topics"] = topics
        if topics:
            print(f"  🏷️  Topics: {', '.join(topics[:3])}")
    except Exception as e:
        stats["topics"] = []
    
    return stats

def save_statistics(all_data):
    """Save collected statistics in organized structure."""
    
    # Create directory structure
    base_dir = Path("all-repos-stats")
    base_dir.mkdir(exist_ok=True)
    
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Save complete snapshot
    current_file = base_dir / "current.json"
    with open(current_file, 'w') as f:
        json.dump(all_data, f, indent=2)
    print(f"\n💾 Saved current snapshot: {current_file}")
    
    # Save per-repository files
    repos_dir = base_dir / "by-repo"
    repos_dir.mkdir(exist_ok=True)
    
    for repo_stats in all_data["repositories"]:
        repo_name = repo_stats["repository"]["name"]
        repo_file = repos_dir / f"{repo_name}.json"
        
        # Load existing data or create new
        if repo_file.exists():
            with open(repo_file, 'r') as f:
                repo_history = json.load(f)
        else:
            repo_history = {
                "repository": repo_stats["repository"]["full_name"],
                "history": []
            }
        
        # Append new snapshot
        repo_history["history"].append({
            "date": date_str,
            "data": repo_stats
        })
        
        # Keep last 90 days
        repo_history["history"] = repo_history["history"][-90:]
        
        # Save
        with open(repo_file, 'w') as f:
            json.dump(repo_history, f, indent=2)
    
    print(f"💾 Updated {len(all_data['repositories'])} individual repository files")
    
    # Append to historical log (JSONL format)
    history_file = base_dir / "history.jsonl"
    with open(history_file, 'a') as f:
        f.write(json.dumps(all_data) + '\n')
    print(f"💾 Appended to historical log: {history_file}")
    
    # Save monthly summary
    year_month = datetime.now(timezone.utc).strftime("%Y-%m")
    monthly_dir = base_dir / "monthly"
    monthly_dir.mkdir(exist_ok=True)
    
    monthly_file = monthly_dir / f"{year_month}.json"
    
    if monthly_file.exists():
        with open(monthly_file, 'r') as f:
            monthly_data = json.load(f)
    else:
        monthly_data = {
            "month": year_month,
            "snapshots": []
        }
    
    monthly_data["snapshots"].append({
        "date": date_str,
        "summary": {
            "total_repos": all_data["total_repositories"],
            "total_stars": sum(r.get("metrics", {}).get("stars", 0) for r in all_data["repositories"]),
            "total_forks": sum(r.get("metrics", {}).get("forks", 0) for r in all_data["repositories"]),
        }
    })
    
    with open(monthly_file, 'w') as f:
        json.dump(monthly_data, f, indent=2)
    print(f"💾 Updated monthly summary: {monthly_file}")
    
    # Generate summary report
    generate_summary_report(all_data, base_dir)

def generate_summary_report(data, base_dir):
    """Generate a human-readable markdown summary."""
    
    report_file = base_dir / "SUMMARY.md"
    timestamp = datetime.fromisoformat(data["collection_timestamp"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    repos = data["repositories"]
    
    # Calculate aggregates
    total_stars = sum(r.get("metrics", {}).get("stars", 0) for r in repos)
    total_forks = sum(r.get("metrics", {}).get("forks", 0) for r in repos)
    total_watchers = sum(r.get("metrics", {}).get("watchers", 0) for r in repos)
    total_size = sum(r.get("metrics", {}).get("size_kb", 0) for r in repos)
    
    # Count by type
    public_count = sum(1 for r in repos if not r["repository"].get("private", False))
    private_count = sum(1 for r in repos if r["repository"].get("private", False))
    archived_count = sum(1 for r in repos if r["repository"].get("archived", False))
    
    # Top repositories by stars
    sorted_by_stars = sorted(
        [r for r in repos if "error" not in r["repository"]],
        key=lambda x: x.get("metrics", {}).get("stars", 0),
        reverse=True
    )[:10]
    
    # Language distribution
    all_languages = {}
    for repo in repos:
        for lang, bytes_count in repo.get("languages", {}).items():
            all_languages[lang] = all_languages.get(lang, 0) + bytes_count
    
    top_languages = sorted(all_languages.items(), key=lambda x: x[1], reverse=True)[:5]
    
    with open(report_file, 'w') as f:
        f.write(f"# Multi-Repository Statistics Summary\n\n")
        f.write(f"**Owner:** {data['owner']}\n\n")
        f.write(f"**Last Updated:** {timestamp}\n\n")
        f.write(f"**Total Repositories:** {data['total_repositories']}\n\n")
        
        f.write("---\n\n")
        
        # Overview
        f.write("## 📊 Overview\n\n")
        f.write(f"- **Public Repositories:** {public_count}\n")
        f.write(f"- **Private Repositories:** {private_count}\n")
        f.write(f"- **Archived Repositories:** {archived_count}\n")
        f.write(f"- **Total Size:** {total_size:,} KB ({total_size / 1024:.1f} MB)\n\n")
        
        # Aggregated metrics
        f.write("## ⭐ Aggregated Metrics\n\n")
        f.write(f"- **Total Stars:** {total_stars:,}\n")
        f.write(f"- **Total Forks:** {total_forks:,}\n")
        f.write(f"- **Total Watchers:** {total_watchers:,}\n\n")
        
        # Top repositories
        f.write("## 🏆 Top Repositories by Stars\n\n")
        f.write("| Repository | Stars | Forks | Language |\n")
        f.write("|------------|-------|-------|----------|\n")
        for repo in sorted_by_stars[:10]:
            name = repo["repository"]["name"]
            url = repo["repository"]["url"]
            stars = repo["metrics"]["stars"]
            forks = repo["metrics"]["forks"]
            lang = repo["repository"].get("language") or "N/A"
            f.write(f"| [{name}]({url}) | {stars:,} | {forks:,} | {lang} |\n")
        f.write("\n")
        
        # Language distribution
        if top_languages:
            f.write("## 💻 Language Distribution (Top 5)\n\n")
            total_bytes = sum(bytes_count for _, bytes_count in all_languages.items())
            for lang, bytes_count in top_languages:
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                f.write(f"- **{lang}:** {percentage:.1f}%\n")
            f.write("\n")
        
        # Recent activity
        f.write("## 🔄 Recently Updated\n\n")
        recent = sorted(
            [r for r in repos if "error" not in r["repository"] and r["repository"].get("pushed_at")],
            key=lambda x: x["repository"]["pushed_at"],
            reverse=True
        )[:5]
        
        f.write("| Repository | Last Push | Stars |\n")
        f.write("|------------|-----------|-------|\n")
        for repo in recent:
            name = repo["repository"]["name"]
            url = repo["repository"]["url"]
            pushed = datetime.fromisoformat(repo["repository"]["pushed_at"].replace('Z', '+00:00')).strftime("%Y-%m-%d")
            stars = repo["metrics"]["stars"]
            f.write(f"| [{name}]({url}) | {pushed} | {stars:,} |\n")
        f.write("\n")
        
        f.write("---\n\n")
        f.write("## 📁 Data Files\n\n")
        f.write("- **Current Snapshot:** `current.json` - Complete data for all repositories\n")
        f.write("- **Historical Log:** `history.jsonl` - All historical snapshots (append-only)\n")
        f.write("- **By Repository:** `by-repo/` - Individual history for each repository\n")
        f.write("- **Monthly Summaries:** `monthly/` - Aggregated monthly data\n\n")
        
        f.write("---\n")
        f.write("*Generated automatically by GitHub Actions*\n")
    
    print(f"📝 Generated summary report: {report_file}")

if __name__ == "__main__":
    try:
        print("🚀 Starting multi-repository statistics collection...\n")
        all_data = fetch_all_repositories_stats()
        save_statistics(all_data)
        print("\n✅ Successfully collected and saved statistics for all repositories!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
