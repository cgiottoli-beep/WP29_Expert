#!/usr/bin/env python3
"""
Version Bump Script for WP29 Expert
Automatically increments version in config.py and updates CHANGELOG.md
Supports: major, minor, patch versioning
"""
import re
import sys
from datetime import datetime
from pathlib import Path


def get_current_version(config_path: Path) -> tuple[str, str]:
    """Extract current version and date from config.py"""
    content = config_path.read_text(encoding='utf-8')
    
    version_match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
    date_match = re.search(r'APP_DATE\s*=\s*["\']([^"\']+)["\']', content)
    
    if not version_match:
        raise ValueError("Could not find APP_VERSION in config.py")
    
    current_version = version_match.group(1)
    current_date = date_match.group(1) if date_match else None
    
    return current_version, current_date


def bump_version(version: str, bump_type: str) -> str:
    """Increment version based on bump_type (major, minor, patch)"""
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    
    major, minor, patch = map(int, parts)
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use major, minor, or patch")
    
    return f"{major}.{minor}.{patch}"


def update_config(config_path: Path, new_version: str, new_date: str, dry_run: bool = False):
    """Update config.py with new version and date"""
    content = config_path.read_text(encoding='utf-8')
    
    # Replace version
    content = re.sub(
        r'APP_VERSION\s*=\s*["\'][^"\']+["\']',
        f'APP_VERSION = "{new_version}"',
        content
    )
    
    # Replace date
    content = re.sub(
        r'APP_DATE\s*=\s*["\'][^"\']+["\']',
        f'APP_DATE = "{new_date}"',
        content
    )
    
    if dry_run:
        print(f"[DRY RUN] Would update {config_path.name}:")
        print(f"  Version: {new_version}")
        print(f"  Date: {new_date}")
    else:
        config_path.write_text(content, encoding='utf-8')
        print(f"✓ Updated {config_path.name}")
        print(f"  Version: {new_version}")
        print(f"  Date: {new_date}")


def get_commit_messages_since_last_tag() -> list[str]:
    """Get all commit messages since the last version tag"""
    import subprocess
    
    try:
        # Get the latest tag
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            last_tag = result.stdout.strip()
            # Get commits since last tag
            result = subprocess.run(
                ['git', 'log', f'{last_tag}..HEAD', '--pretty=format:%s'],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            # No tags yet, get all commits
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%s'],
                capture_output=True,
                text=True,
                check=True
            )
        
        commits = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return commits
    except subprocess.CalledProcessError:
        return []


def update_changelog(changelog_path: Path, new_version: str, new_date: str, 
                     commits: list[str], dry_run: bool = False):
    """Add new version section to CHANGELOG.md"""
    
    # Categorize commits
    features = []
    fixes = []
    breaking = []
    other = []
    
    for commit in commits:
        if commit.startswith('feat:') or commit.startswith('feat('):
            features.append(commit)
        elif commit.startswith('fix:') or commit.startswith('fix('):
            fixes.append(commit)
        elif 'BREAKING CHANGE' in commit or commit.startswith('!:'):
            breaking.append(commit)
        elif not any(commit.startswith(p) for p in ['docs:', 'chore:', 'style:', 'refactor:', 'test:']):
            other.append(commit)
    
    # Build new changelog entry
    new_entry = f"## [{new_version}] - {new_date}\n\n"
    
    if breaking:
        new_entry += "### ⚠️ BREAKING CHANGES\n"
        for commit in breaking:
            new_entry += f"- {commit}\n"
        new_entry += "\n"
    
    if features:
        new_entry += "### Added\n"
        for commit in features:
            # Remove feat: prefix
            msg = re.sub(r'^feat(\([^)]+\))?:\s*', '', commit)
            new_entry += f"- {msg}\n"
        new_entry += "\n"
    
    if fixes:
        new_entry += "### Fixed\n"
        for commit in fixes:
            # Remove fix: prefix
            msg = re.sub(r'^fix(\([^)]+\))?:\s*', '', commit)
            new_entry += f"- {msg}\n"
        new_entry += "\n"
    
    if other:
        new_entry += "### Changed\n"
        for commit in other:
            new_entry += f"- {commit}\n"
        new_entry += "\n"
    
    if dry_run:
        print(f"\n[DRY RUN] Would add to {changelog_path.name}:")
        print("---")
        print(new_entry)
        print("---")
    else:
        # Read existing changelog
        if changelog_path.exists():
            content = changelog_path.read_text(encoding='utf-8')
            
            # Find where to insert (after # Changelog header)
            lines = content.split('\n')
            insert_index = 0
            
            for i, line in enumerate(lines):
                if line.strip().startswith('## ['):
                    insert_index = i
                    break
            
            if insert_index > 0:
                # Insert before first version entry
                lines.insert(insert_index, new_entry)
            else:
                # No version entries yet, add after header
                for i, line in enumerate(lines):
                    if line.strip() == '# Changelog':
                        lines.insert(i + 2, new_entry)
                        break
            
            new_content = '\n'.join(lines)
        else:
            new_content = f"# Changelog\n\n{new_entry}"
        
        changelog_path.write_text(new_content, encoding='utf-8')
        print(f"✓ Updated {changelog_path.name}")


def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python bump_version.py [major|minor|patch] [--dry-run]")
        print("\nOr let it auto-detect from git commits:")
        print("  python bump_version.py auto [--dry-run]")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    # Paths
    script_dir = Path(__file__).parent
    config_path = script_dir / 'config.py'
    changelog_path = script_dir / 'CHANGELOG.md'
    
    # Get current version
    current_version, _ = get_current_version(config_path)
    print(f"Current version: {current_version}")
    
    # Auto-detect bump type from commits
    if bump_type == 'auto':
        commits = get_commit_messages_since_last_tag()
        if not commits:
            print("No commits found since last tag. Defaulting to patch bump.")
            bump_type = 'patch'
        else:
            # Check for breaking changes or major keywords
            has_breaking = any('BREAKING CHANGE' in c or c.startswith('!:') for c in commits)
            has_feat = any(c.startswith('feat:') or c.startswith('feat(') for c in commits)
            
            if has_breaking:
                bump_type = 'major'
                print(f"Detected BREAKING CHANGE => major bump")
            elif has_feat:
                bump_type = 'minor'
                print(f"Detected feat commits => minor bump")
            else:
                bump_type = 'patch'
                print(f"Detected fixes/other => patch bump")
    
    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    new_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"New version: {new_version} ({bump_type} bump)")
    
    # Get commits for changelog
    commits = get_commit_messages_since_last_tag()
    
    # Update files
    update_config(config_path, new_version, new_date, dry_run)
    update_changelog(changelog_path, new_version, new_date, commits, dry_run)
    
    if not dry_run:
        print(f"\n✅ Version bumped from {current_version} to {new_version}")
        print(f"Next steps:")
        print(f"  1. Review the changes")
        print(f"  2. Commit: git add config.py CHANGELOG.md")
        print(f"  3. Commit: git commit -m 'chore: Release v{new_version}'")
        print(f"  4. Tag: git tag v{new_version}")
        print(f"  5. Push: git push && git push --tags")


if __name__ == '__main__':
    main()
