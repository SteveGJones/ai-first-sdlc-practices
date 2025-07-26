#!/usr/bin/env python3
"""
Validates instruction file sizes meet compression targets.
"""
import sys
from pathlib import Path

# Size limits (in lines)
LIMITS = {
    "CLAUDE-CORE.md": 200,
    "CLAUDE-SETUP.md": 150,
    "CLAUDE-CONTEXT-architecture.md": 200,
    "CLAUDE-CONTEXT-validation.md": 150,
    "CLAUDE-CONTEXT-update.md": 100,
    "CLAUDE-CONTEXT-language-validators.md": 200,
}

# Target compression ratio
TARGET_COMPRESSION = 0.70  # 70% reduction

def count_lines(filepath):
    """Count non-empty lines in a file."""
    try:
        with open(filepath, 'r') as f:
            return sum(1 for line in f if line.strip())
    except FileNotFoundError:
        return 0

def check_file_sizes():
    """Check all instruction files against size limits."""
    violations = []
    total_lines = 0
    
    print("Checking instruction file sizes...")
    print("-" * 50)
    
    for filename, limit in LIMITS.items():
        filepath = Path(filename)
        if not filepath.exists():
            filepath = Path("..") / ".." / filename  # Try from validation dir
        
        if filepath.exists():
            lines = count_lines(filepath)
            total_lines += lines
            status = "✅" if lines <= limit else "❌"
            print(f"{status} {filename}: {lines}/{limit} lines")
            
            if lines > limit:
                violations.append(f"{filename} exceeds limit by {lines - limit} lines")
        else:
            print(f"⚠️  {filename}: NOT FOUND")
    
    return violations, total_lines

def check_compression_ratio(new_total):
    """Check if compression target is met."""
    # Original default load (full CLAUDE.md)
    original_default = 897
    
    # New default load (only CLAUDE-CORE.md)
    core_file = Path("CLAUDE-CORE.md")
    if not core_file.exists():
        core_file = Path("..") / ".." / "CLAUDE-CORE.md"
    
    new_default = count_lines(core_file) if core_file.exists() else 0
    default_compression = (original_default - new_default) / original_default
    
    # Total footprint analysis
    original_total = 897 + 183 + 175 + 60  # All original files
    total_compression = (original_total - new_total) / original_total
    
    print("\nCompression Analysis:")
    print("-" * 50)
    print("Default Load (what AI sees by default):")
    print(f"  Original: {original_default} lines (full CLAUDE.md)")
    print(f"  New: {new_default} lines (CLAUDE-CORE.md only)")
    print(f"  Compression: {default_compression:.1%}")
    print(f"  Target: {TARGET_COMPRESSION:.1%}")
    print("\nTotal Footprint (all instruction files):")
    print(f"  Original: {original_total} lines")
    print(f"  New: {new_total} lines")
    print(f"  Compression: {total_compression:.1%}")
    
    return default_compression >= TARGET_COMPRESSION

def main():
    """Main validation function."""
    print("AI-First SDLC Instruction Compression Validator")
    print("=" * 50)
    
    # Check individual file sizes
    violations, total_lines = check_file_sizes()
    
    # Check overall compression
    compression_met = check_compression_ratio(total_lines)
    
    # Summary
    print("\nSummary:")
    print("-" * 50)
    
    if violations:
        print("❌ Size limit violations:")
        for violation in violations:
            print(f"   - {violation}")
    else:
        print("✅ All files within size limits")
    
    if compression_met:
        print("✅ Compression target achieved")
    else:
        print("❌ Compression target not met")
    
    # Exit code
    if violations or not compression_met:
        print("\n❌ Validation FAILED")
        return 1
    else:
        print("\n✅ Validation PASSED")
        return 0

if __name__ == "__main__":
    sys.exit(main())