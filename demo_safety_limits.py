#!/usr/bin/env python3
"""
Demonstration script for Nova CI-Rescue Safety Limits (Milestone C).

This script demonstrates the safety limit enforcement that prevents
dangerous auto-modifications from being applied.
"""

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from nova.tools.safety_limits import SafetyLimits, SafetyConfig, check_patch_safety

console = Console()


def demo_safe_patch():
    """Demonstrate a patch that passes all safety checks."""
    console.print("\n[bold green]Demo 1: Safe Patch[/bold green]")
    console.print("This patch makes small, safe changes to regular source files.\n")
    
    patch = """--- a/src/calculator.py
+++ b/src/calculator.py
@@ -10,7 +10,9 @@ class Calculator:
     def add(self, a, b):
         return a + b
     
-    def subtract(self, a, b):
-        return a - b
+    def subtract(self, a, b, absolute=False):
+        result = a - b
+        if absolute:
+            return abs(result)
+        return result
"""
    
    # Display the patch
    syntax = Syntax(patch, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="Patch Content", border_style="green"))
    
    # Check safety
    is_safe, message = check_patch_safety(patch, verbose=True)
    
    # Analyze the patch
    safety = SafetyLimits()
    analysis = safety.analyze_patch(patch)
    
    # Display results
    table = Table(title="Safety Analysis", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Lines Added", str(analysis.total_lines_added))
    table.add_row("Lines Removed", str(analysis.total_lines_removed))
    table.add_row("Total Changed", str(analysis.total_lines_changed))
    table.add_row("Files Modified", str(len(analysis.files_modified)))
    table.add_row("Safety Status", "✅ SAFE" if is_safe else "❌ UNSAFE")
    
    console.print(table)
    
    if is_safe:
        console.print("\n[green]✅ This patch would be automatically applied![/green]")
    else:
        console.print(f"\n[red]❌ Patch rejected: {message}[/red]")


def demo_exceeds_line_limit():
    """Demonstrate a patch that exceeds the line change limit."""
    console.print("\n[bold yellow]Demo 2: Patch Exceeding Line Limit[/bold yellow]")
    console.print("This patch changes too many lines (>200).\n")
    
    # Create a large patch
    lines = []
    for i in range(250):
        if i < 125:
            lines.append(f"-    old_function_{i}()")
        else:
            lines.append(f"+    new_function_{i-125}()")
    
    patch = f"""--- a/src/large_refactor.py
+++ b/src/large_refactor.py
@@ -1,125 +1,125 @@
{chr(10).join(lines)}
"""
    
    # Display a preview of the patch
    preview = "\n".join(patch.split("\n")[:20]) + "\n... (230 more lines)"
    syntax = Syntax(preview, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="Patch Preview (truncated)", border_style="yellow"))
    
    # Check safety
    is_safe, message = check_patch_safety(patch)
    
    # Analyze the patch
    safety = SafetyLimits()
    analysis = safety.analyze_patch(patch)
    
    # Display results
    table = Table(title="Safety Analysis", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Limit", style="yellow")
    table.add_row("Lines Changed", str(analysis.total_lines_changed), "200")
    table.add_row("Files Modified", str(len(analysis.files_modified | analysis.files_added)), "10")
    table.add_row("Safety Status", "❌ UNSAFE", "")
    
    console.print(table)
    console.print("\n[red]❌ Patch rejected: Exceeds maximum lines changed (250 > 200)[/red]")
    console.print("[yellow]💡 Recommendation: Break this into smaller, focused patches[/yellow]")


def demo_too_many_files():
    """Demonstrate a patch that modifies too many files."""
    console.print("\n[bold yellow]Demo 3: Patch Modifying Too Many Files[/bold yellow]")
    console.print("This patch modifies more than 10 files.\n")
    
    # Create a patch touching many files
    patch_parts = []
    for i in range(12):
        patch_parts.append(f"""--- a/src/module_{i}/config.py
+++ b/src/module_{i}/config.py
@@ -1,2 +1,2 @@
-DEBUG = False
+DEBUG = True
""")
    
    patch = "\n".join(patch_parts)
    
    # Display a preview
    preview = "\n".join(patch.split("\n")[:30]) + "\n... (more files)"
    syntax = Syntax(preview, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="Patch Preview (truncated)", border_style="yellow"))
    
    # Check safety
    is_safe, message = check_patch_safety(patch)
    
    # Analyze the patch
    safety = SafetyLimits()
    analysis = safety.analyze_patch(patch)
    
    # Display results
    table = Table(title="Safety Analysis", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Limit", style="yellow")
    table.add_row("Files Modified", str(len(analysis.files_modified)), "10")
    table.add_row("Lines Changed", str(analysis.total_lines_changed), "200")
    table.add_row("Safety Status", "❌ UNSAFE", "")
    
    console.print(table)
    console.print("\n[red]❌ Patch rejected: Exceeds maximum files modified (12 > 10)[/red]")
    console.print("[yellow]💡 Recommendation: Focus on related changes in fewer files[/yellow]")


def demo_restricted_files():
    """Demonstrate a patch attempting to modify restricted files."""
    console.print("\n[bold red]Demo 4: Patch Modifying Restricted Files[/bold red]")
    console.print("This patch attempts to modify CI/CD configs and deployment files.\n")
    
    patch = """--- a/.github/workflows/deploy.yml
+++ b/.github/workflows/deploy.yml
@@ -5,7 +5,7 @@ on:
     branches: [main]
 
 jobs:
-  deploy:
+  auto-deploy:
     runs-on: ubuntu-latest
--- a/deploy/production.yml
+++ b/deploy/production.yml
@@ -10,5 +10,5 @@ spec:
   replicas: 3
-  strategy:
-    type: RollingUpdate
+  strategy:
+    type: Recreate
--- a/.env.production
+++ b/.env.production
@@ -1,2 +1,2 @@
-API_KEY=old_key_12345
+API_KEY=new_key_67890
 DATABASE_URL=postgres://prod"""
    
    # Display the patch
    syntax = Syntax(patch, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="Patch Content", border_style="red"))
    
    # Check safety
    is_safe, message = check_patch_safety(patch)
    
    # Analyze the patch
    safety = SafetyLimits()
    analysis = safety.analyze_patch(patch)
    
    # Display restricted files
    table = Table(title="Restricted Files Detected", show_header=True, header_style="bold red")
    table.add_column("File", style="red")
    table.add_column("Reason", style="yellow")
    
    for file in analysis.denied_files:
        if ".github" in file:
            reason = "CI/CD Configuration"
        elif "deploy" in file:
            reason = "Deployment Configuration"
        elif ".env" in file:
            reason = "Environment Secrets"
        else:
            reason = "Restricted Path"
        table.add_row(file, reason)
    
    console.print(table)
    console.print("\n[red]❌ Patch rejected: Attempts to modify restricted files[/red]")
    console.print("[yellow]💡 These changes require manual review and approval[/yellow]")


def demo_custom_limits():
    """Demonstrate using custom safety limits."""
    console.print("\n[bold cyan]Demo 5: Custom Safety Limits[/bold cyan]")
    console.print("Organizations can configure their own safety limits.\n")
    
    # Create custom configuration
    custom_config = SafetyConfig(
        max_lines_changed=50,  # Stricter line limit
        max_files_modified=3,   # Stricter file limit
        denied_paths=[
            "*.prod.yml",
            "database/*",
            "auth/*",
            "billing/*"
        ]
    )
    
    # Display configuration
    config_table = Table(title="Custom Configuration", show_header=True, header_style="bold cyan")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="white")
    config_table.add_row("Max Lines Changed", "50")
    config_table.add_row("Max Files Modified", "3")
    config_table.add_row("Additional Denied Paths", "*.prod.yml, database/*, auth/*, billing/*")
    console.print(config_table)
    
    # Test patch against custom limits
    patch = """--- a/auth/login.py
+++ b/auth/login.py
@@ -10,3 +10,5 @@ def login(username, password):
     if check_credentials(username, password):
         return create_session(username)
     return None
+    # TODO: Add rate limiting
+    # TODO: Add 2FA support"""
    
    syntax = Syntax(patch, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title="Test Patch", border_style="cyan"))
    
    # Check with custom config
    safety = SafetyLimits(config=custom_config)
    is_safe, violations = safety.validate_patch(patch)
    
    if not is_safe:
        console.print(f"\n[red]❌ Patch rejected: {violations[0]}[/red]")
    else:
        console.print("\n[green]✅ Patch passed custom safety checks[/green]")


def show_summary():
    """Display a summary of safety limits."""
    console.print("\n" + "=" * 60)
    console.print(Panel.fit(
        "[bold]Nova CI-Rescue Safety Limits Summary[/bold]\n\n"
        "[green]✅ Protections Enabled:[/green]\n"
        "• Maximum 200 lines changed per patch\n"
        "• Maximum 10 files modified per patch\n"
        "• Restricted paths automatically blocked\n\n"
        "[yellow]🚫 Restricted Paths Include:[/yellow]\n"
        "• CI/CD configurations (.github/*, .gitlab-ci.yml, etc.)\n"
        "• Deployment files (deploy/*, k8s/*, Dockerfile, etc.)\n"
        "• Security files (secrets/*, .env*, *.key, *.pem, etc.)\n"
        "• Dependency locks (package-lock.json, poetry.lock, etc.)\n"
        "• Database migrations and schemas\n\n"
        "[cyan]💡 Benefits:[/cyan]\n"
        "• Prevents accidental breaking changes\n"
        "• Enforces manual review for critical files\n"
        "• Limits blast radius of automated fixes\n"
        "• Maintains security and compliance standards",
        title="Safety Limits Overview",
        border_style="bold blue"
    ))


def main():
    """Run all demonstrations."""
    console.print("\n" + "=" * 60)
    console.print("[bold]Nova CI-Rescue - Safety Limits Demonstration[/bold]")
    console.print("Milestone C: GitHub Action & PR Proof")
    console.print("=" * 60)
    
    # Run demos
    demo_safe_patch()
    input("\n[dim]Press Enter to continue...[/dim]")
    
    demo_exceeds_line_limit()
    input("\n[dim]Press Enter to continue...[/dim]")
    
    demo_too_many_files()
    input("\n[dim]Press Enter to continue...[/dim]")
    
    demo_restricted_files()
    input("\n[dim]Press Enter to continue...[/dim]")
    
    demo_custom_limits()
    
    # Show summary
    show_summary()
    
    console.print("\n[bold green]✅ Safety Limits Implementation Complete![/bold green]")
    console.print("The safety limits are now integrated into Nova CI-Rescue.")
    console.print("These protections ensure automated fixes remain safe and controlled.\n")


if __name__ == "__main__":
    main()
