# Git Patch Creator Script

Cross-platform bash script to create git patch files from all pending changes (both staged and unstaged).

## Files

- create-patch.sh` - Universal bash script for all platforms

## Features

- ✅ Cross-platform compatibility (Windows Git Bash, macOS, Linux)
- ✅ Automatically stages all changes (including untracked files)
- ✅ Creates timestamped patch files
- ✅ Colored output for better readability (with fallback for unsupported terminals)
- ✅ Command line options for custom output filename
- ✅ Built-in help system
- ✅ Error handling and validation
- ✅ Shows patch statistics
- ✅ Provides usage instructions for applying patches

## Usage

### All Platforms (Bash/Git Bash)

```bash
# Make script executable (first time only on Unix/Linux/macOS)
chmod +x create-patch.sh

# Run the script with default timestamped filename
./create-patch.sh

# Run with custom output filename
./create-patch.sh -o my-changes.patch
./create-patch.sh --output my-changes.patch

# Show help
./create-patch.sh -h
./create-patch.sh --help
```

### Windows Users

Use Git Bash (comes with Git for Windows) to run the script:

```bash
# In Git Bash terminal
./create-patch.sh
```

## What the Scripts Do

1. **Verify Git Repository** - Checks if you're in a valid git repository
2. **Check for Changes** - Scans for modified, added, or untracked files
3. **Stage All Changes** - Runs `git add -A` to stage everything
4. **Create Patch File** - Generates a patch file with timestamp: `changes_YYYYMMDD_HHMMSS.patch`
5. **Show Statistics** - Displays file changes summary
6. **Provide Instructions** - Shows commands to apply the patch

## Output

The scripts create a patch file named `changes_YYYYMMDD_HHMMSS.patch` containing all your changes.

Example output:

```
[INFO] Creating git patch file: changes_20241204_143205.patch
[INFO] Checking git status...
[INFO] Staging all changes...
[INFO] Creating patch file from staged changes...
[INFO] Patch file statistics:
 src/app/component.ts | 25 +++++++++++++++++++++++++
 src/app/service.ts   | 15 +++++++++++++++
 2 files changed, 40 insertions(+)
[SUCCESS] Patch file created successfully: changes_20241204_143205.patch
[SUCCESS] File size: 2048 bytes
```

## Applying Patches

Once you have a patch file, you can apply it using:

```bash
# Standard apply
git apply changes_20241204_143205.patch

# Apply ignoring whitespace changes
git apply --ignore-whitespace changes_20241204_143205.patch

# Apply with 3-way merge (safer for conflicts)
git apply --3way changes_20241204_143205.patch
```

## Error Handling

The scripts handle common scenarios:

- Not in a git repository
- No changes to patch
- Empty patch files
- File creation failures

## Requirements

- Git installed and available in PATH
- Bash shell (Git Bash on Windows, Terminal on macOS/Linux)
- Write permissions in the current directory

## Notes

- The scripts automatically stage all changes before creating the patch
- Untracked files are included in the patch
- The original git status is preserved (files remain staged after script execution)
- Patch files use UTF-8 encoding for cross-platform compatibility
