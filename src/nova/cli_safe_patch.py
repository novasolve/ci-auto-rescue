#!/usr/bin/env python3
"""
Nova CI-Rescue Safe Patching CLI
=================================

Command-line interface for the comprehensive Safe Patching system.

Usage:
    python -m nova.cli_safe_patch apply <patch_file> [--context <context_file>] [--no-critic]
    python -m nova.cli_safe_patch review <patch_file> [--context <context_file>]
    python -m nova.cli_safe_patch rollback [--hard] [--count <n>]
    python -m nova.cli_safe_patch status

Examples:
    # Apply a patch with full safety checks and critic review
    python -m nova.cli_safe_patch apply fix.patch --context failing_tests.txt
    
    # Review a patch without applying
    python -m nova.cli_safe_patch review fix.patch
    
    # Rollback the last patch (preserving history)
    python -m nova.cli_safe_patch rollback
    
    # Rollback the last 3 patches using hard reset
    python -m nova.cli_safe_patch rollback --hard --count 3
    
    # Show rollback history status
    python -m nova.cli_safe_patch status
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from nova.engine.safe_patching import (
    PatchSafetyGuard,
    PatchSafetyConfig,
    ApplyPatchTool,
    CriticReviewTool,
    RollbackManager
)
from nova.engine.rollback import get_rollback_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nova.cli_safe_patch")


def cmd_apply(args):
    """Apply a patch with full safety checks."""
    # Read patch file
    patch_file = Path(args.patch_file)
    if not patch_file.exists():
        print(f"ERROR: Patch file not found: {patch_file}")
        return 1
    
    patch_text = patch_file.read_text()
    
    # Read context if provided
    context = None
    if args.context:
        context_file = Path(args.context)
        if context_file.exists():
            context = context_file.read_text()
        else:
            print(f"WARNING: Context file not found: {context_file}")
    
    # Initialize components
    safety_config = PatchSafetyConfig()
    safety_guard = PatchSafetyGuard(config=safety_config, verbose=True)
    applier = ApplyPatchTool(repo_path=args.repo)
    rollback_mgr = get_rollback_manager(args.repo)
    
    # Step 1: Safety checks
    print("Step 1: Running safety checks...")
    is_safe, violations = safety_guard.validate_patch(patch_text)
    
    if not is_safe:
        print("\n❌ SAFETY CHECK FAILED:")
        for violation in violations:
            print(f"  • {violation}")
        return 1
    
    print("✅ Safety checks passed")
    
    # Step 2: Critic review (unless skipped)
    if not args.no_critic:
        print("\nStep 2: Running critic review...")
        critic = CriticReviewTool(safety_guard=safety_guard, verbose=True)
        approved, rationale = critic.review_patch(patch_text, context=context)
        
        if not approved:
            print(f"\n❌ CRITIC REJECTED PATCH: {rationale}")
            return 1
        
        print(f"✅ Critic approved: {rationale}")
    else:
        print("\nStep 2: Skipping critic review (--no-critic flag)")
    
    # Step 3: Create backup branch
    print("\nStep 3: Creating backup branch...")
    success, branch_name = rollback_mgr.create_backup_branch()
    if success:
        print(f"✅ Created backup branch: {branch_name}")
    else:
        print(f"⚠️  Failed to create backup branch: {branch_name}")
    
    # Step 4: Apply patch
    print("\nStep 4: Applying patch...")
    success, message = applier.apply_patch(patch_text)
    
    if success:
        print(f"✅ {message}")
        
        # Record commit for rollback
        commit_id = ""
        if "commit" in message:
            commit_id = message.split()[-1].strip(")")
            rollback_mgr.record_patch_commit(commit_id)
            print(f"✅ Recorded commit {commit_id} for potential rollback")
        
        print("\n🎉 Patch applied successfully!")
        return 0
    else:
        print(f"\n❌ FAILED TO APPLY PATCH: {message}")
        return 1


def cmd_review(args):
    """Review a patch without applying it."""
    # Read patch file
    patch_file = Path(args.patch_file)
    if not patch_file.exists():
        print(f"ERROR: Patch file not found: {patch_file}")
        return 1
    
    patch_text = patch_file.read_text()
    
    # Read context if provided
    context = None
    if args.context:
        context_file = Path(args.context)
        if context_file.exists():
            context = context_file.read_text()
    
    # Initialize components
    safety_config = PatchSafetyConfig()
    safety_guard = PatchSafetyGuard(config=safety_config, verbose=True)
    critic = CriticReviewTool(safety_guard=safety_guard, verbose=True)
    
    print("Running comprehensive patch review...\n")
    
    # Safety checks
    print("1. Safety Analysis:")
    is_safe, violations = safety_guard.validate_patch(patch_text)
    
    if is_safe:
        print("   ✅ No safety violations detected")
    else:
        print("   ❌ Safety violations found:")
        for violation in violations:
            print(f"      • {violation}")
    
    # Critic review
    print("\n2. Critic Review:")
    approved, rationale = critic.review_patch(patch_text, context=context)
    
    if approved:
        print(f"   ✅ APPROVED: {rationale}")
    else:
        print(f"   ❌ REJECTED: {rationale}")
    
    # Patch statistics
    print("\n3. Patch Statistics:")
    lines = patch_text.splitlines()
    added = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
    removed = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
    files = set()
    for line in lines:
        if line.startswith('+++') or line.startswith('---'):
            parts = line.split()
            if len(parts) >= 2:
                file_path = parts[1]
                if file_path.startswith('a/') or file_path.startswith('b/'):
                    file_path = file_path[2:]
                files.add(file_path)
    
    print(f"   • Lines added: {added}")
    print(f"   • Lines removed: {removed}")
    print(f"   • Files affected: {len(files)}")
    if files:
        print("   • Files:")
        for f in sorted(files):
            print(f"     - {f}")
    
    return 0 if is_safe and approved else 1


def cmd_rollback(args):
    """Rollback applied patches."""
    rollback_mgr = get_rollback_manager(args.repo)
    
    # Show preview first
    preview = rollback_mgr.get_rollback_preview()
    if not preview:
        print("No patches to rollback.")
        return 0
    
    print("Patches that will be rolled back:")
    for i, info in enumerate(preview[:args.count], 1):
        print(f"\n{i}. Commit: {info['hash']}")
        print(f"   Message: {info['message']}")
        if info['files']:
            print(f"   Files: {', '.join(info['files'][:3])}", end="")
            if len(info['files']) > 3:
                print(f" ... (+{len(info['files'])-3} more)")
            else:
                print()
    
    # Confirm
    if not args.yes:
        response = input(f"\nRollback {min(args.count, len(preview))} commit(s)? [y/N] ")
        if response.lower() != 'y':
            print("Rollback cancelled.")
            return 0
    
    # Perform rollback
    preserve_history = not args.hard
    results = rollback_mgr.rollback_multiple_commits(args.count, preserve_history=preserve_history)
    
    # Report results
    print(f"\nRollback Results ({'git revert' if preserve_history else 'git reset --hard'}):")
    for i, (success, message) in enumerate(results, 1):
        if success:
            print(f"  {i}. ✅ {message}")
        else:
            print(f"  {i}. ❌ {message}")
            break  # Stop on first failure
    
    return 0 if all(r[0] for r in results) else 1


def cmd_status(args):
    """Show rollback history status."""
    rollback_mgr = get_rollback_manager(args.repo)
    
    # Current branch
    branch = rollback_mgr.get_current_branch()
    print(f"Current branch: {branch}")
    
    # Patch history
    history = rollback_mgr.get_patch_history()
    if not history:
        print("\nNo patches in rollback history.")
        return 0
    
    print(f"\nRollback history ({len(history)} patches):")
    preview = rollback_mgr.get_rollback_preview()
    
    for info in preview:
        print(f"\n• {info['hash'][:8]}: {info['message']}")
        if info['files']:
            print(f"  Files: {', '.join(info['files'][:5])}", end="")
            if len(info['files']) > 5:
                print(f" ... (+{len(info['files'])-5} more)")
            else:
                print()
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Nova CI-Rescue Safe Patching CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--repo', 
        default='.',
        help='Repository path (default: current directory)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Apply command
    apply_parser = subparsers.add_parser('apply', help='Apply a patch with safety checks')
    apply_parser.add_argument('patch_file', help='Path to patch file')
    apply_parser.add_argument('--context', help='Path to context file (e.g., failing tests)')
    apply_parser.add_argument('--no-critic', action='store_true', help='Skip critic review')
    
    # Review command
    review_parser = subparsers.add_parser('review', help='Review a patch without applying')
    review_parser.add_argument('patch_file', help='Path to patch file')
    review_parser.add_argument('--context', help='Path to context file')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback applied patches')
    rollback_parser.add_argument('--hard', action='store_true', help='Use git reset --hard instead of revert')
    rollback_parser.add_argument('--count', type=int, default=1, help='Number of patches to rollback (default: 1)')
    rollback_parser.add_argument('-y', '--yes', action='store_true', help='Skip confirmation prompt')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show rollback history status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command handler
    command_map = {
        'apply': cmd_apply,
        'review': cmd_review,
        'rollback': cmd_rollback,
        'status': cmd_status
    }
    
    handler = command_map.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
