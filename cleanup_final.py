"""
VetRender Repository Cleanup Script
====================================
Removes unnecessary documentation and duplicate files
Keeps only essential code and build files
"""
import os
import shutil

# Files to delete
FILES_TO_DELETE = [
    # Documentation files (keeping only README.md and LICENSE)
    'AI_BUTTON_FIX.md',
    'AI_LOGGING_GUIDE.md',
    'ANTENNA_LIBRARY_IMPLEMENTATION.md',
    'ANTENNA_METADATA_EXTRACTION.md',
    'BUG_FIXES_AI_IMPORT.md',
    'DEBUG_SUMMARY.md',
    'HOW_TO_ADD_TO_PATH.txt',
    'LLM_XML_BUG_FIX.md',
    'MSI_BUILD_README.md',
    'MSI_INSTALLER_GUIDE.txt',
    'OLLAMA_TROUBLESHOOTING.md',
    'POWERSHELL_SCRIPT_UPDATE.md',
    'PYINSTALLER_QT_FIX.txt',
    'QUICK_FIX_METADATA.md',
    'RUN_THIS_TO_CLEANUP.txt',
    'START_HERE.txt',
    'WIX_V6_INSTRUCTIONS.txt',
    
    # Duplicate/old GUI files
    'gui/dialogs_FIXED.py',
    'gui/dialogs_header_fix.py',
    
    # One-time scripts
    'apply_metadata_extraction.py',
    'run_cleanup.py',
    
    # Unused deployment file
    'main_window_TO_DEPLOY.py',
    
    # Redundant batch files
    'CLEANUP_NOW.bat',
    'cleanup_repo.bat',
    'git_cleanup.bat',
]

def cleanup_repository():
    """Remove unnecessary files from repository"""
    
    print("=" * 70)
    print("VetRender Repository Cleanup")
    print("=" * 70)
    print()
    
    deleted_count = 0
    skipped_count = 0
    
    for filepath in FILES_TO_DELETE:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"[OK] DELETED: {filepath}")
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to delete {filepath}: {e}")
                skipped_count += 1
        else:
            print(f"[SKIP] {filepath} (not found)")
            skipped_count += 1
    
    print()
    print("=" * 70)
    print(f"Cleanup Complete!")
    print(f"  Files deleted: {deleted_count}")
    print(f"  Files skipped: {skipped_count}")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Review changes with: git status")
    print("  2. Rebuild executable: build_exe_only.bat")
    print("  3. Build installer: build_installer.bat")
    print()

if __name__ == "__main__":
    cleanup_repository()
