#!/usr/bin/env python3
"""
Generate interactive analytics dashboard from multi-repository statistics.
Creates visualizations and comparative reports.
"""

import json
from pathlib import Path
from datetime import datetime
import sys

def generate_dashboard():
    """Generate analytics dashboard from collected statistics."""
    
    base_dir = Path("all-repos-stats")
    current_file = base_dir / "current.json"
    
    if not current_file.exists():
        print("⚠️  No statistics data found. Run collection first.")
        return
    
    print("📊 Generating analytics dashboard...\n")
    
    # Load current data
    with open(current_file, 'r') as f:
        data = json.load(f)
    
    repos = data["repositories"]
    repos = [r for r in repos if "error" not in r["repository"]]  # Filter out errors
    
    # Generate various analytics
    generate_comparison_table(repos, base_dir)
    generate_trends_report(base_dir)
    generate_traffic_summary(repos, base_dir)
    
    print("\n✅ Dashboard generation complete!")

def generate_comparison_table(repos, base_dir):
    """Generate detailed comparison table of all repositories."""
    
    output_file = base_dir / "COMPARISON.md"
    
    print("📋 Creating repository comparison table...")
    
    with open(output_file, 'w') as f:
        f.write("# Repository Comparison\n\n")
        f.write(f"**Total Repositories:** {len(repos)}\n\n")
        
        # Sort options
        f.write("## Quick Links\n\n")
        f.write("- [Sort by Stars](#by-stars)\n")
        f.write("- [Sort by Forks](#by-forks)\n")
        f.write("- [Sort by Size](#by-size)\n")
        f.write("- [Sort by Activity](#by-activity)\n\n")
        
        f.write("---\n\n")
        
        # By Stars
        f.write("## By Stars\n\n")
        sorted_repos = sorted(repos, key=lambda x: x.get("metrics", {}).get("stars", 0), reverse=True)
        write_repo_table(f, sorted_repos)
        
        # By Forks
        f.write("## By Forks\n\n")
        sorted_repos = sorted(repos, key=lambda x: x.get("metrics", {}).get("forks", 0), reverse=True)
        write_repo_table(f, sorted_repos)
        
        # By Size
        f.write("## By Size\n\n")
        sorted_repos = sorted(repos, key=lambda x: x.get("metrics", {}).get("size_kb", 0), reverse=True)
        write_repo_table(f, sorted_repos, show_size=True)
        
        # By Activity
        f.write("## By Activity\n\n")
        sorted_repos = sorted(
            [r for r in repos if r["repository"].get("pushed_at")],
            key=lambda x: x["repository"]["pushed_at"],
            reverse=True
        )
        write_repo_table(f, sorted_repos, show_date=True)
    
    print(f"  ✓ Saved to {output_file}")

def write_repo_table(f, repos, show_size=False, show_date=False):
    """Helper to write repository comparison table."""
    
    headers = ["Repository", "Stars", "Forks", "Issues"]
    if show_size:
        headers.append("Size (KB)")
    if show_date:
        headers.append("Last Push")
    headers.append("Language")
    
    f.write("| " + " | ".join(headers) + " |\n")
    f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
    
    for repo in repos[:20]:  # Top 20
        name = repo["repository"]["name"]
        url = repo["repository"]["url"]
        stars = repo["metrics"]["stars"]
        forks = repo["metrics"]["forks"]
        issues = repo["metrics"]["open_issues"]
        lang = repo["repository"].get("language") or "N/A"
        
        row = [f"[{name}]({url})", f"{stars:,}", f"{forks:,}", f"{issues:,}"]
        
        if show_size:
            size = repo["metrics"]["size_kb"]
            row.append(f"{size:,}")
        
        if show_date:
            pushed = repo["repository"].get("pushed_at")
            if pushed:
                date = datetime.fromisoformat(pushed.replace('Z', '+00:00')).strftime("%Y-%m-%d")
                row.append(date)
            else:
                row.append("N/A")
        
        row.append(lang)
        
        f.write("| " + " | ".join(row) + " |\n")
    
    f.write("\n")

def generate_trends_report(base_dir):
    """Generate trends report from historical data."""
    
    history_file = base_dir / "history.jsonl"
    
    if not history_file.exists():
        print("⚠️  No historical data available yet")
        return
    
    print("📈 Analyzing trends...")
    
    # Read historical snapshots
    snapshots = []
    with open(history_file, 'r') as f:
        for line in f:
            snapshots.append(json.loads(line))
    
    if len(snapshots) < 2:
        print("  ℹ️  Need at least 2 snapshots for trend analysis")
        return
    
    # Compare first and last snapshot
    first = snapshots[0]
    last = snapshots[-1]
    
    output_file = base_dir / "TRENDS.md"
    
    with open(output_file, 'w') as f:
        f.write("# Repository Trends\n\n")
        f.write(f"**Analysis Period:** {len(snapshots)} days\n\n")
        
        # Aggregate changes
        first_total_stars = sum(r.get("metrics", {}).get("stars", 0) for r in first["repositories"])
        last_total_stars = sum(r.get("metrics", {}).get("stars", 0) for r in last["repositories"])
        stars_change = last_total_stars - first_total_stars
        
        first_total_forks = sum(r.get("metrics", {}).get("forks", 0) for r in first["repositories"])
        last_total_forks = sum(r.get("metrics", {}).get("forks", 0) for r in last["repositories"])
        forks_change = last_total_forks - first_total_forks
        
        f.write("## 📊 Overall Changes\n\n")
        f.write(f"- **Stars:** {first_total_stars:,} → {last_total_stars:,} ({stars_change:+,})\n")
        f.write(f"- **Forks:** {first_total_forks:,} → {last_total_forks:,} ({forks_change:+,})\n")
        f.write(f"- **Repositories:** {first['total_repositories']} → {last['total_repositories']}\n\n")
        
        # Find biggest gainers
        repo_changes = []
        for repo_last in last["repositories"]:
            if "error" in repo_last["repository"]:
                continue
            
            repo_name = repo_last["repository"]["full_name"]
            
            # Find matching repo in first snapshot
            repo_first = next(
                (r for r in first["repositories"] if r["repository"].get("full_name") == repo_name),
                None
            )
            
            if repo_first:
                stars_diff = repo_last["metrics"]["stars"] - repo_first["metrics"]["stars"]
                forks_diff = repo_last["metrics"]["forks"] - repo_first["metrics"]["forks"]
                
                if stars_diff > 0 or forks_diff > 0:
                    repo_changes.append({
                        "name": repo_last["repository"]["name"],
                        "url": repo_last["repository"]["url"],
                        "stars_change": stars_diff,
                        "forks_change": forks_diff,
                    })
        
        if repo_changes:
            f.write("## 🚀 Biggest Gainers\n\n")
            
            # Sort by stars change
            top_stars = sorted(repo_changes, key=lambda x: x["stars_change"], reverse=True)[:5]
            f.write("### Most Stars Gained\n\n")
            f.write("| Repository | Stars Gained |\n")
            f.write("|------------|-------------|\n")
            for repo in top_stars:
                if repo["stars_change"] > 0:
                    f.write(f"| [{repo['name']}]({repo['url']}) | +{repo['stars_change']:,} |\n")
            f.write("\n")
            
            # Sort by forks change
            top_forks = sorted(repo_changes, key=lambda x: x["forks_change"], reverse=True)[:5]
            f.write("### Most Forks Gained\n\n")
            f.write("| Repository | Forks Gained |\n")
            f.write("|------------|-------------|\n")
            for repo in top_forks:
                if repo["forks_change"] > 0:
                    f.write(f"| [{repo['name']}]({repo['url']}) | +{repo['forks_change']:,} |\n")
            f.write("\n")
    
    print(f"  ✓ Saved to {output_file}")

def generate_traffic_summary(repos, base_dir):
    """Generate traffic summary for repositories with traffic data."""
    
    print("🚦 Analyzing traffic data...")
    
    repos_with_traffic = [
        r for r in repos 
        if r.get("traffic", {}).get("views", {}).get("available") != False
    ]
    
    if not repos_with_traffic:
        print("  ℹ️  No traffic data available")
        return
    
    output_file = base_dir / "TRAFFIC.md"
    
    with open(output_file, 'w') as f:
        f.write("# Traffic Summary\n\n")
        f.write(f"**Repositories with Traffic Data:** {len(repos_with_traffic)}\n\n")
        
        # Calculate totals
        total_views = sum(r.get("traffic", {}).get("views", {}).get("count", 0) for r in repos_with_traffic)
        total_unique_views = sum(r.get("traffic", {}).get("views", {}).get("uniques", 0) for r in repos_with_traffic)
        total_clones = sum(r.get("traffic", {}).get("clones", {}).get("count", 0) for r in repos_with_traffic)
        total_unique_clones = sum(r.get("traffic", {}).get("clones", {}).get("uniques", 0) for r in repos_with_traffic)
        
        f.write("## 📊 Aggregate Traffic (Last 14 Days)\n\n")
        f.write(f"- **Total Views:** {total_views:,}\n")
        f.write(f"- **Unique Visitors:** {total_unique_views:,}\n")
        f.write(f"- **Total Clones:** {total_clones:,}\n")
        f.write(f"- **Unique Cloners:** {total_unique_clones:,}\n\n")
        
        # Top by views
        f.write("## 👀 Most Viewed Repositories\n\n")
        sorted_by_views = sorted(
            repos_with_traffic,
            key=lambda x: x.get("traffic", {}).get("views", {}).get("count", 0),
            reverse=True
        )[:10]
        
        f.write("| Repository | Views | Unique Visitors | Clones | Unique Cloners |\n")
        f.write("|------------|-------|----------------|--------|----------------|\n")
        for repo in sorted_by_views:
            name = repo["repository"]["name"]
            url = repo["repository"]["url"]
            views = repo.get("traffic", {}).get("views", {}).get("count", 0)
            unique_views = repo.get("traffic", {}).get("views", {}).get("uniques", 0)
            clones = repo.get("traffic", {}).get("clones", {}).get("count", 0)
            unique_clones = repo.get("traffic", {}).get("clones", {}).get("uniques", 0)
            
            f.write(f"| [{name}]({url}) | {views:,} | {unique_views:,} | {clones:,} | {unique_clones:,} |\n")
        f.write("\n")
    
    print(f"  ✓ Saved to {output_file}")

if __name__ == "__main__":
    try:
        generate_dashboard()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
