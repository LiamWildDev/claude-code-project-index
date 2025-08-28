#!/usr/bin/env python3
"""
Git Submodule Index Manager for Claude Code
Manages separate PROJECT_INDEX.json files for parent projects and their submodules.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import the main indexer
from project_index import build_index, compress_index_if_needed, print_summary


def detect_git_submodules(root_dir: Path) -> List[Dict[str, str]]:
    """Detect all Git submodules in the current project."""
    submodules = []
    gitmodules_file = root_dir / '.gitmodules'
    
    if not gitmodules_file.exists():
        return submodules
    
    try:
        # Use git submodule status to get accurate info
        result = subprocess.run(
            ['git', 'submodule', 'status', '--recursive'],
            capture_output=True,
            text=True,
            cwd=root_dir
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Parse git submodule status output
                    # Format: [+/-/U/ ]<commit> <path> [(branch/tag)]
                    parts = line.split()
                    if len(parts) >= 2:
                        path = parts[1]
                        submodule_path = root_dir / path
                        if submodule_path.exists():
                            submodules.append({
                                'path': path,
                                'full_path': str(submodule_path),
                                'has_index': (submodule_path / 'PROJECT_INDEX.json').exists()
                            })
    except subprocess.CalledProcessError:
        # Fallback: parse .gitmodules file directly
        try:
            with open(gitmodules_file, 'r') as f:
                content = f.read()
                # Simple parser for .gitmodules
                current_module = None
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('[submodule'):
                        current_module = {}
                    elif line.startswith('path =') and current_module is not None:
                        path = line.split('=', 1)[1].strip()
                        submodule_path = root_dir / path
                        if submodule_path.exists():
                            submodules.append({
                                'path': path,
                                'full_path': str(submodule_path),
                                'has_index': (submodule_path / 'PROJECT_INDEX.json').exists()
                            })
                        current_module = None
        except Exception as e:
            print(f"⚠️  Error parsing .gitmodules: {e}")
    
    return submodules


def is_path_in_submodule(file_path: Path, submodule_paths: List[Path]) -> bool:
    """Check if a path is inside any submodule directory."""
    try:
        for submodule_path in submodule_paths:
            if submodule_path in file_path.parents or file_path == submodule_path:
                return True
    except Exception:
        pass
    return False


def build_index_excluding_submodules(root_dir: str, submodules: List[Dict[str, str]]) -> Tuple[Dict, int]:
    """Build index for parent project, excluding submodule directories."""
    # Temporarily add submodule paths to ignored directories
    from index_utils import IGNORE_DIRS, should_index_file
    
    # Save original IGNORE_DIRS
    original_ignore = IGNORE_DIRS.copy()
    
    # Add submodule directories to ignore list
    for submodule in submodules:
        # Add the submodule directory name to ignore
        submodule_dir = Path(submodule['path']).name
        IGNORE_DIRS.add(submodule_dir)
        # Also add the full relative path
        IGNORE_DIRS.add(submodule['path'])
    
    try:
        # Build index with submodules excluded
        print("📊 Building index for parent project (excluding submodules)...")
        index, skipped_count = build_index(root_dir)
        
        # Add metadata about excluded submodules
        index['excluded_submodules'] = [s['path'] for s in submodules]
        index['index_type'] = 'parent_only'
        
        return index, skipped_count
    finally:
        # Restore original IGNORE_DIRS
        IGNORE_DIRS.clear()
        IGNORE_DIRS.update(original_ignore)


def build_submodule_index(submodule_path: str, submodule_name: str) -> Tuple[Optional[Dict], int]:
    """Build index for a specific submodule."""
    print(f"📊 Building index for submodule: {submodule_name}")
    
    # Change to submodule directory and build index
    original_dir = os.getcwd()
    try:
        os.chdir(submodule_path)
        index, skipped_count = build_index('.')
        
        # Add metadata
        index['index_type'] = 'submodule'
        index['submodule_name'] = submodule_name
        
        return index, skipped_count
    except Exception as e:
        print(f"❌ Error indexing submodule {submodule_name}: {e}")
        return None, 0
    finally:
        os.chdir(original_dir)


def save_index_metadata(root_dir: Path, metadata: Dict):
    """Save metadata about all indexes in the project."""
    metadata_file = root_dir / '.submodule_indexes.json'
    metadata['updated_at'] = datetime.now().isoformat()
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Index metadata saved to: {metadata_file}")


def interactive_menu(submodules: List[Dict[str, str]]) -> str:
    """Display interactive menu for indexing options."""
    print("\n🔧 Git Submodule Index Manager")
    print("=" * 50)
    
    if not submodules:
        print("ℹ️  No Git submodules detected in this project")
        return "parent"
    
    print(f"📦 Found {len(submodules)} submodule(s):")
    for i, sub in enumerate(submodules, 1):
        status = "✅ indexed" if sub['has_index'] else "❌ not indexed"
        print(f"   {i}. {sub['path']} ({status})")
    
    print("\n📋 Choose an option:")
    print("   1. Index parent project only (exclude submodules)")
    print("   2. Index a specific submodule")
    print("   3. Index all submodules")
    print("   4. Index everything (parent + all submodules)")
    print("   5. Show index status")
    print("   0. Cancel")
    
    while True:
        try:
            choice = input("\n👉 Enter your choice (0-5): ").strip()
            if choice == '0':
                return "cancel"
            elif choice == '1':
                return "parent"
            elif choice == '2':
                return "specific"
            elif choice == '3':
                return "all_submodules"
            elif choice == '4':
                return "everything"
            elif choice == '5':
                return "status"
            else:
                print("⚠️  Invalid choice. Please enter 0-5.")
        except KeyboardInterrupt:
            print("\n👋 Cancelled")
            return "cancel"


def choose_submodule(submodules: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Let user choose a specific submodule to index."""
    print("\n📦 Select a submodule to index:")
    for i, sub in enumerate(submodules, 1):
        print(f"   {i}. {sub['path']}")
    
    while True:
        try:
            choice = input(f"\n👉 Enter submodule number (1-{len(submodules)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(submodules):
                return submodules[idx]
            else:
                print(f"⚠️  Please enter a number between 1 and {len(submodules)}")
        except (ValueError, KeyboardInterrupt):
            print("\n👋 Cancelled")
            return None


def show_index_status(root_dir: Path, submodules: List[Dict[str, str]]):
    """Display the status of all indexes in the project."""
    print("\n📊 Index Status Report")
    print("=" * 50)
    
    # Check parent index
    parent_index = root_dir / 'PROJECT_INDEX.json'
    if parent_index.exists():
        try:
            with open(parent_index, 'r') as f:
                data = json.load(f)
                indexed_at = data.get('indexed_at', 'unknown')
                file_count = data.get('stats', {}).get('total_files', 0)
                index_type = data.get('index_type', 'unknown')
                print(f"\n🏠 Parent Project:")
                print(f"   ✅ Indexed: {indexed_at}")
                print(f"   📄 Files: {file_count}")
                print(f"   🏷️  Type: {index_type}")
        except Exception as e:
            print(f"\n🏠 Parent Project: ⚠️  Error reading index: {e}")
    else:
        print(f"\n🏠 Parent Project: ❌ Not indexed")
    
    # Check submodule indexes
    if submodules:
        print(f"\n📦 Submodules ({len(submodules)}):")
        for sub in submodules:
            sub_index = Path(sub['full_path']) / 'PROJECT_INDEX.json'
            if sub_index.exists():
                try:
                    with open(sub_index, 'r') as f:
                        data = json.load(f)
                        indexed_at = data.get('indexed_at', 'unknown')
                        file_count = data.get('stats', {}).get('total_files', 0)
                        print(f"\n   📁 {sub['path']}:")
                        print(f"      ✅ Indexed: {indexed_at}")
                        print(f"      📄 Files: {file_count}")
                except Exception as e:
                    print(f"\n   📁 {sub['path']}: ⚠️  Error reading index")
            else:
                print(f"\n   📁 {sub['path']}: ❌ Not indexed")
    
    # Check metadata file
    metadata_file = root_dir / '.submodule_indexes.json'
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                print(f"\n📋 Metadata last updated: {data.get('updated_at', 'unknown')}")
        except Exception:
            pass


def main():
    """Main entry point for submodule index manager."""
    root_dir = Path.cwd()
    
    # Detect submodules
    submodules = detect_git_submodules(root_dir)
    
    # Show interactive menu
    choice = interactive_menu(submodules)
    
    if choice == "cancel":
        print("👋 Operation cancelled")
        return
    
    elif choice == "status":
        show_index_status(root_dir, submodules)
        return
    
    elif choice == "parent":
        # Index parent only
        index, skipped_count = build_index_excluding_submodules(str(root_dir), submodules)
        
        # Compress if needed
        index = compress_index_if_needed(index)
        
        # Save parent index
        output_path = root_dir / 'PROJECT_INDEX.json'
        with open(output_path, 'w') as f:
            json.dump(index, f, indent=2)
        
        print_summary(index, skipped_count)
        print(f"\n💾 Parent index saved to: {output_path}")
        
        # Save metadata
        save_index_metadata(root_dir, {
            'parent_indexed': True,
            'submodules': submodules
        })
    
    elif choice == "specific":
        # Index specific submodule
        selected = choose_submodule(submodules)
        if selected:
            index, skipped_count = build_submodule_index(
                selected['full_path'], 
                selected['path']
            )
            
            if index:
                # Compress if needed
                index = compress_index_if_needed(index)
                
                # Save submodule index
                output_path = Path(selected['full_path']) / 'PROJECT_INDEX.json'
                with open(output_path, 'w') as f:
                    json.dump(index, f, indent=2)
                
                print_summary(index, skipped_count)
                print(f"\n💾 Submodule index saved to: {output_path}")
    
    elif choice == "all_submodules":
        # Index all submodules
        for sub in submodules:
            index, skipped_count = build_submodule_index(
                sub['full_path'],
                sub['path']
            )
            
            if index:
                # Compress if needed
                index = compress_index_if_needed(index)
                
                # Save submodule index
                output_path = Path(sub['full_path']) / 'PROJECT_INDEX.json'
                with open(output_path, 'w') as f:
                    json.dump(index, f, indent=2)
                
                print(f"✅ Indexed submodule: {sub['path']}")
        
        print(f"\n✨ All {len(submodules)} submodules indexed successfully!")
    
    elif choice == "everything":
        # Index parent and all submodules
        print("\n🚀 Indexing parent project and all submodules...")
        
        # Index parent
        index, skipped_count = build_index_excluding_submodules(str(root_dir), submodules)
        index = compress_index_if_needed(index)
        output_path = root_dir / 'PROJECT_INDEX.json'
        with open(output_path, 'w') as f:
            json.dump(index, f, indent=2)
        print(f"✅ Parent project indexed")
        
        # Index all submodules
        for sub in submodules:
            index, skipped_count = build_submodule_index(
                sub['full_path'],
                sub['path']
            )
            
            if index:
                index = compress_index_if_needed(index)
                output_path = Path(sub['full_path']) / 'PROJECT_INDEX.json'
                with open(output_path, 'w') as f:
                    json.dump(index, f, indent=2)
                print(f"✅ Submodule indexed: {sub['path']}")
        
        # Save metadata
        save_index_metadata(root_dir, {
            'parent_indexed': True,
            'submodules': submodules
        })
        
        print(f"\n✨ Complete indexing finished!")
        print(f"   🏠 Parent project: ✅")
        print(f"   📦 Submodules: {len(submodules)} indexed")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)