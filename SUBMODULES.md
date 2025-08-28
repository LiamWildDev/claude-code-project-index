# Git Submodules Support for PROJECT_INDEX

This document explains how to use PROJECT_INDEX with Git submodules to maintain separate indexes for parent projects and their submodules.

## Overview

When working with Git submodules, you often want to maintain architectural awareness of both the parent project and submodules separately. This prevents the index from becoming too large and keeps clear boundaries between different codebases.

## Quick Start

### Option 1: Using the Interactive Menu (Recommended)

```bash
# Navigate to your parent project
cd /path/to/parent-project

# Run the interactive submodule manager
/index-submodules
```

This will present you with options to:
1. Index parent project only (excluding submodules)
2. Index specific submodules
3. Index all submodules at once
4. Index everything (parent + all submodules)
5. Show index status for all modules

### Option 2: Manual Indexing with Flags

```bash
# Index parent project only (excludes submodules)
/index --exclude-submodules

# Navigate to a submodule and index it separately
cd submodule-directory
/index

# Go back to parent
cd ..
```

## How It Works

### Submodule Detection

The indexer automatically detects Git submodules by:
1. Checking for `.gitmodules` file in the project root
2. Parsing submodule paths from the configuration
3. Verifying each submodule exists and is initialized

### Index Structure

After setting up indexes for a project with submodules, you'll have:

```
your-project/
├── PROJECT_INDEX.json           # Parent project index (excludes submodules)
├── .submodule_indexes.json      # Metadata tracking all indexes
├── submodule1/
│   └── PROJECT_INDEX.json       # Submodule 1's own index
└── submodule2/
    └── PROJECT_INDEX.json       # Submodule 2's own index
```

### Index Metadata

Each index contains metadata about its type:
- **Parent Index**: `"index_type": "parent_only"` and lists excluded submodules
- **Submodule Index**: `"index_type": "submodule"` with submodule name

## Usage Patterns

### 1. Working on Parent Project Code

When working on the parent project:
```
# Load parent project architecture
@PROJECT_INDEX.json what functions handle authentication?

# The parent index excludes submodule code, keeping focus on parent logic
```

### 2. Working on Submodule Code

When working inside a submodule:
```
# Load specific submodule's architecture
@libs/auth-module/PROJECT_INDEX.json show me all auth functions

# Or navigate to submodule first
cd libs/auth-module
@PROJECT_INDEX.json list all exported functions
```

### 3. Cross-Module Work

When working across boundaries:
```
# Load both indexes when needed
@PROJECT_INDEX.json how does the parent call the auth module?
@libs/auth-module/PROJECT_INDEX.json what's the auth module's public API?
```

## Workflow Examples

### Initial Setup for Existing Project with Submodules

```bash
# 1. Clone project with submodules
git clone --recursive https://github.com/user/project.git
cd project

# 2. Run interactive indexer
/index-submodules

# 3. Choose option 4: "Index everything"
# This creates indexes for parent and all submodules

# 4. Verify indexes were created
ls PROJECT_INDEX.json
ls submodule1/PROJECT_INDEX.json
ls submodule2/PROJECT_INDEX.json
```

### Adding a New Submodule

```bash
# 1. Add the submodule
git submodule add https://github.com/user/new-module.git libs/new-module

# 2. Index just the new submodule
/index-submodules
# Choose option 2: "Index specific submodule"
# Select: libs/new-module

# 3. Update parent index to exclude the new submodule
/index --exclude-submodules
```

### Updating All Indexes

```bash
# Use the interactive menu
/index-submodules

# Choose option 4: "Index everything"
# This will refresh all indexes at once
```

## Best Practices

### 1. Keep Indexes Separate
- Always use `--exclude-submodules` when indexing the parent
- Each module should have its own PROJECT_INDEX.json
- This keeps indexes focused and manageable in size

### 2. Reference the Right Index
- Use `@PROJECT_INDEX.json` for parent project work
- Use `@submodule_path/PROJECT_INDEX.json` for submodule work
- Load multiple indexes when working across boundaries

### 3. Update Strategy
- Update parent index when parent code changes significantly
- Update submodule indexes when pulling submodule updates
- Use `/index-submodules` status option to check freshness

### 4. CLAUDE.md Configuration
For projects with submodules, consider this CLAUDE.md pattern:

```markdown
# Project Context

## Parent Project
@PROJECT_INDEX.json

## Submodules
- Auth Module: @libs/auth/PROJECT_INDEX.json  
- UI Components: @libs/ui/PROJECT_INDEX.json

Load the appropriate index based on the area being worked on.
```

## Automatic Hooks

The existing hooks work with submodules:
- PostToolUse hooks update the index where the file was edited
- Stop hooks detect changes in both parent and submodules
- Each index is maintained independently

## Troubleshooting

### Problem: Index includes submodule files

**Solution**: Rebuild parent index with exclusion flag
```bash
/index --exclude-submodules
```

### Problem: Submodule not detected

**Solution**: Ensure submodule is initialized
```bash
git submodule update --init --recursive
/index-submodules
```

### Problem: Can't find submodule index

**Solution**: Index the specific submodule
```bash
cd path/to/submodule
/index
```

### Problem: Index too large even with exclusions

**Solution**: Consider excluding more directories or file types
```python
# Edit ~/.claude-code-project-index/scripts/index_utils.py
IGNORE_DIRS = {
    # ... existing dirs ...
    'vendor',  # Add vendor directory
    'node_modules',  # Already included
    'large_assets'  # Add any large directories
}
```

## Advanced Configuration

### Custom Submodule Detection

If your project uses non-standard submodule configuration, you can modify the detection logic in:
```
~/.claude-code-project-index/scripts/submodule_index.py
```

### Excluding Specific Submodules

To always exclude certain submodules from parent indexing, add them to IGNORE_DIRS:
```python
# In ~/.claude-code-project-index/scripts/index_utils.py
IGNORE_DIRS = {
    # ... existing dirs ...
    'third_party/large_sdk',  # Specific submodule to always skip
}
```

## Command Reference

### /index-submodules
Interactive menu for managing submodule indexes with options:
- Index parent only
- Index specific submodule  
- Index all submodules
- Index everything
- Show status

### /index --exclude-submodules
Create index for current directory, excluding any Git submodules.

### Standard /index
Creates index for current directory (includes everything unless in a submodule).

## Status Checking

The `/index-submodules` command's status option shows:
- Parent index status (exists, last updated, file count)
- Each submodule's index status
- Metadata file status
- Which submodules are indexed vs not indexed

Example output:
```
📊 Index Status Report
==================================================

🏠 Parent Project:
   ✅ Indexed: 2024-01-15T10:30:00
   📄 Files: 234
   🏷️ Type: parent_only

📦 Submodules (3):

   📁 libs/auth:
      ✅ Indexed: 2024-01-15T10:31:00
      📄 Files: 45

   📁 libs/ui:
      ❌ Not indexed

   📁 vendor/sdk:
      ✅ Indexed: 2024-01-14T15:20:00
      📄 Files: 1250
```

## Integration with Existing Workflow

The submodule support integrates seamlessly with existing PROJECT_INDEX features:
- Automatic hook updates still work
- Call graphs track within each module
- Directory purposes identified per module
- Language parsing works the same

The key difference is scope - each index only covers its own module, providing cleaner architectural boundaries.

## Performance Considerations

Separate indexes provide several performance benefits:
1. **Smaller Context**: Each index is smaller, using fewer tokens
2. **Faster Updates**: Hook updates only touch the relevant index
3. **Parallel Work**: Can index submodules in parallel
4. **Selective Loading**: Only load indexes for modules you're working on

## Summary

The submodule support for PROJECT_INDEX enables:
- ✅ Clean separation between parent and submodule code
- ✅ Independent architectural awareness for each module
- ✅ Flexible indexing strategies (all at once or individually)
- ✅ Smaller, more focused indexes
- ✅ Better performance with large projects
- ✅ Clear module boundaries

Use `/index-submodules` to get started with your multi-module project!