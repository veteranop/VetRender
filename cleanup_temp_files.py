"""Clean up temporary test/fix scripts before git push"""
import os

# List of temporary scripts we created during debugging
temp_scripts = [
    'check_backups.py',
    'check_build.py',
    'check_config_again.py',
    'check_indent.py',
    'check_methods.py',
    'check_rebuild_needed.py',
    'check_gitignore.py',
    'diagnose_class.py',
    'find_class_end.py',
    'find_config_methods.py',
    'fix_brace_properly.py',
    'fix_closing_brace.py',
    'fix_comma.py',
    'fix_comma_checkpoint.py',
    'fix_encoding.py',
    'fix_indent.py',
    'fix_indent2.py',
    'fix_line_245.py',
    'fresh_import_test.py',
    'remove_all_bad.py',
    'remove_bad_methods.py',
    'remove_help_callbacks.py',
    'restore_and_fix.py',
    'restore_clean.py',
    'show_line_245.py',
    'show_lines.py',
    'show_get_callbacks.py',
    'show_problem_area.py',
    'test_methods.py',
    'add_dist_old_gitignore.py',
    'add_help_integration.py',
    'help_menu_additions.py',
    'gui/main_window.py.broken'
]

print("Cleaning up temporary files...")
print("="*60)

deleted = []
not_found = []

for script in temp_scripts:
    if os.path.exists(script):
        os.remove(script)
        deleted.append(script)
        print(f"  ✓ Deleted: {script}")
    else:
        not_found.append(script)

print("\n" + "="*60)
print(f"Deleted {len(deleted)} files")
print(f"Already gone: {len(not_found)} files")
print("="*60)

print("\n✓ Repository is clean and ready!")
print("\nNext steps:")
print("  1. Run: build_all.bat  (rebuild with fixed code)")
print("  2. Test the new build")
print("  3. Git commit and push")
