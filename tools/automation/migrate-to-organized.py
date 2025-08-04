#!/usr/bin/env python3
"""
Migration tool to reorganize AI-First SDLC Framework files into .sdlc directory
"""

import os
import shutil
import sys
from pathlib import Path
import json
import argparse


class FrameworkMigrator:
    """Migrates existing framework installation to organized structure"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.sdlc_dir = self.project_root / '.sdlc'
        self.moved_files = []
        self.errors = []
        
    def check_existing_installation(self) -> bool:
        """Check if this is an existing framework installation"""
        indicators = [
            self.project_root / 'tools' / 'validate-pipeline.py',
            self.project_root / 'tools' / 'validation' / 'validate-pipeline.py',
            self.project_root / 'CLAUDE.md',
            self.project_root / 'docs' / 'feature-proposals'
        ]
        
        return any(path.exists() for path in indicators)
    
    def migrate(self, dry_run: bool = False) -> bool:
        """Perform the migration"""
        if not self.check_existing_installation():
            print("❌ No existing AI-First SDLC installation found")
            print("   Use setup-smart.py --organized for new installations")
            return False
        
        print("🔍 Analyzing existing installation...")
        
        # Create .sdlc structure
        if not dry_run:
            self._create_sdlc_structure()
        
        # Map of old locations to new locations
        migrations = {
            # Tools directory
            'tools': '.sdlc/tools',
            
            # Templates (but not in docs)
            'templates': '.sdlc/templates',
            
            # Agent files
            'claude/agents': '.sdlc/agents',
            '.claude/agents': '.sdlc/agents',
            
            # Version file
            'VERSION': '.sdlc/VERSION',
            
            # Config files that should move
            '.ai-sdlc-temp': None,  # Delete temp directory
        }
        
        # Files that should stay at root
        keep_at_root = [
            'CLAUDE.md',
            'CLAUDE-CORE.md', 
            'CLAUDE-SETUP.md',
            'CLAUDE-CONTEXT-*.md',
            'README.md',
            'CONTRIBUTING.md',
            '.gitignore',
            'docs',  # User-facing docs stay
            'plan',
            'retrospectives'
        ]
        
        if dry_run:
            print("\n🔍 DRY RUN - No files will be moved")
            print("=" * 50)
        
        # Perform migrations
        for old_path, new_path in migrations.items():
            src = self.project_root / old_path
            
            if src.exists():
                if new_path is None:
                    # Delete temp/cache directories
                    if dry_run:
                        print(f"Would delete: {old_path}")
                    else:
                        if src.is_dir():
                            shutil.rmtree(src)
                        else:
                            src.unlink()
                        print(f"✅ Deleted: {old_path}")
                else:
                    # Move to new location
                    dst = self.project_root / new_path
                    
                    if dry_run:
                        print(f"Would move: {old_path} → {new_path}")
                    else:
                        self._move_path(src, dst)
        
        # Create convenience scripts
        if not dry_run:
            self._create_convenience_scripts()
            self._update_claude_md()
            self._update_gitignore()
        
        # Summary
        print("\n" + "=" * 50)
        if dry_run:
            print("🔍 Dry run complete. Use --execute to perform migration")
        else:
            print(f"✅ Migration complete! Moved {len(self.moved_files)} items")
            print("\n📁 New structure:")
            print("   .sdlc/          # Framework tools and configs")
            print("   docs/           # Your documentation (unchanged)")
            print("   retrospectives/ # Your retrospectives (unchanged)")
            print("   plan/           # Your plans (unchanged)")
            
            if self.errors:
                print(f"\n⚠️  {len(self.errors)} errors occurred:")
                for error in self.errors:
                    print(f"   - {error}")
        
        return len(self.errors) == 0
    
    def _create_sdlc_structure(self):
        """Create the .sdlc directory structure"""
        dirs = [
            '.sdlc/tools/validation',
            '.sdlc/tools/automation',
            '.sdlc/templates/architecture', 
            '.sdlc/templates/proposals',
            '.sdlc/agents',
            '.sdlc/config'
        ]
        
        for dir_path in dirs:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)
    
    def _move_path(self, src: Path, dst: Path):
        """Move a file or directory"""
        try:
            # Create parent directory
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if src.is_dir() and dst.exists():
                # Merge directories
                for item in src.iterdir():
                    self._move_path(item, dst / item.name)
                # Remove empty source
                if not any(src.iterdir()):
                    src.rmdir()
            else:
                # Move file or entire directory
                shutil.move(str(src), str(dst))
                self.moved_files.append(f"{src.relative_to(self.project_root)} → {dst.relative_to(self.project_root)}")
                print(f"✅ Moved: {src.relative_to(self.project_root)} → {dst.relative_to(self.project_root)}")
        except Exception as e:
            error_msg = f"Failed to move {src}: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
    
    def _create_convenience_scripts(self):
        """Create wrapper scripts"""
        scripts = {
            'validate': '#!/bin/bash\npython .sdlc/tools/validation/validate-pipeline.py "$@"\n',
            'new-feature': '''#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: ./new-feature <feature-name>"
    exit 1
fi
cp .sdlc/templates/proposals/feature-proposal.md "docs/feature-proposals/$(date +%y)-$1.md"
echo "Created: docs/feature-proposals/$(date +%y)-$1.md"
''',
            'install-agents': '#!/bin/bash\npython .sdlc/tools/automation/agent-installer.py "$@"\n'
        }
        
        for name, content in scripts.items():
            script_path = self.project_root / name
            if not script_path.exists():
                with open(script_path, 'w') as f:
                    f.write(content)
                os.chmod(script_path, 0o755)
                print(f"✅ Created convenience script: {name}")
    
    def _update_claude_md(self):
        """Update CLAUDE.md to reflect new structure"""
        claude_path = self.project_root / 'CLAUDE.md'
        if claude_path.exists():
            content = claude_path.read_text()
            
            # Update tool paths
            replacements = [
                ('python tools/validate-pipeline.py', './validate'),
                ('python tools/validation/validate-pipeline.py', './validate'),
                ('tools/', '.sdlc/tools/'),
                ('templates/', '.sdlc/templates/')
            ]
            
            for old, new in replacements:
                content = content.replace(old, new)
            
            # Add migration notice
            if '## Directory Structure' in content:
                content = content.replace(
                    '## Directory Structure',
                    '''## Directory Structure (Organized)

**Note**: This project has been migrated to the organized structure.
Framework tools are now in `.sdlc/` for a cleaner project root.

## Directory Structure'''
                )
            
            claude_path.write_text(content)
            print("✅ Updated CLAUDE.md for new structure")
    
    def _update_gitignore(self):
        """Add .sdlc entries to gitignore"""
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            
            if '.sdlc/' not in content:
                with open(gitignore_path, 'a') as f:
                    f.write('\n# AI-First SDLC Framework (Organized)\n')
                    f.write('.sdlc/temp/\n')
                    f.write('.sdlc/cache/\n') 
                    f.write('.sdlc/logs/\n')
                print("✅ Updated .gitignore")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate existing AI-First SDLC installation to organized structure"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be moved without making changes'
    )
    parser.add_argument(
        '--execute',
        action='store_true', 
        help='Perform the migration'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path.cwd(),
        help='Project root directory'
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("🔍 Migration Tool for AI-First SDLC Framework")
        print("=" * 50)
        print("\nThis will reorganize framework files into .sdlc/ directory")
        print("for a cleaner project structure.")
        print("\nUsage:")
        print("  --dry-run   Show what would be moved")
        print("  --execute   Perform the migration")
        return
    
    migrator = FrameworkMigrator(args.project_root)
    success = migrator.migrate(dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()