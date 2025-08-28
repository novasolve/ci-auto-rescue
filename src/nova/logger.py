"""
Structured logging for Nova CI-Rescue

Provides hierarchical, context-aware logging with multiple verbosity levels.
"""

from typing import Optional, Dict, Any, List
from enum import IntEnum
from contextlib import contextmanager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree


class LogLevel(IntEnum):
    """Logging verbosity levels"""

    NORMAL = 0  # Default - clean output only
    VERBOSE = 1  # --verbose - show operation details
    DEBUG = 2  # --debug - show implementation details
    TRACE = 3  # --trace - show everything including raw data


class NovaLogger:
    """Structured logger for Nova CI-Rescue"""

    def __init__(
        self, console: Optional[Console] = None, level: LogLevel = LogLevel.NORMAL
    ):
        self.console = console or Console()
        self.level: LogLevel
        # Ensure level is a LogLevel instance
        if isinstance(level, str):
            try:
                self.level = LogLevel[level.upper()]
            except KeyError:
                valid_levels = [lvl.name for lvl in LogLevel]
                raise ValueError(
                    f"Invalid log level string '{level}'. Valid levels are: {', '.join(valid_levels)}"
                )
        elif isinstance(level, int):
            self.level = LogLevel(level)
        else:
            self.level = level
        self._indent_level = 0
        self._section_stack: List[str] = []
        self._components_filter: Optional[List[str]] = None

    def set_components_filter(self, components: Optional[List[str]]):
        """Set which components to show debug info for"""
        self._components_filter = components

    def _should_show_component(self, component: Optional[str]) -> bool:
        """Check if we should show logs for this component"""
        if not component or not self._components_filter:
            return True
        return component.lower() in [c.lower() for c in self._components_filter]

    @contextmanager
    def section(self, title: str, emoji: str = "━━━", show_in_normal: bool = False):
        """Create a new section with visual separators"""
        self._section_stack.append(title)
        if self.level >= LogLevel.VERBOSE or show_in_normal:
            self.console.print(f"\n{emoji} {title} {emoji}")
        try:
            yield
        finally:
            self._section_stack.pop()

    @contextmanager
    def subsection(self, title: str, emoji: str = ""):
        """Create an indented subsection"""
        show = self.level >= LogLevel.VERBOSE
        if show:
            indent = "  " * self._indent_level
            # Use tree-like characters for better visual hierarchy
            if self._indent_level == 0:
                prefix = "├─"
            else:
                prefix = "└─" if emoji else "├─"
            self.console.print(
                f"{indent}{prefix} {emoji} {title}"
                if emoji
                else f"{indent}{prefix} {title}"
            )
        self._indent_level += 1
        try:
            yield
        finally:
            self._indent_level -= 1

    def info(self, message: str, emoji: str = ""):
        """Log info message (always shown)"""
        if emoji:
            self.console.print(f"{emoji} {message}")
        else:
            self.console.print(message)

    def success(self, message: str):
        """Log success message (always shown)"""
        self.console.print(f"[green]✅ {message}[/green]")

    def warning(self, message: str):
        """Log warning message (always shown)"""
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")

    def error(self, message: str):
        """Log error message (always shown)"""
        self.console.print(f"[red]❌ {message}[/red]")

    def verbose(self, message: str, component: Optional[str] = None):
        """Log verbose message (shown with --verbose)"""
        if self.level >= LogLevel.VERBOSE and self._should_show_component(component):
            indent = "  " * self._indent_level
            if component:
                self.console.print(f"{indent}[dim][{component}][/dim] {message}")
            else:
                self.console.print(f"{indent}{message}")

    def debug(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        component: Optional[str] = None,
    ):
        """Log debug message with optional data (shown with --debug)"""
        if self.level >= LogLevel.DEBUG and self._should_show_component(component):
            indent = "  " * self._indent_level
            prefix = f"[{component}]" if component else "[DEBUG]"
            self.console.print(f"{indent}[blue dim]{prefix}[/blue dim] {message}")
            if data:
                for key, value in data.items():
                    self.console.print(f"{indent}  [cyan dim]{key}:[/cyan dim] {value}")

    def trace(
        self,
        message: str,
        raw_data: Optional[str] = None,
        component: Optional[str] = None,
    ):
        """Log trace message with raw data (shown with --trace)"""
        if self.level >= LogLevel.TRACE and self._should_show_component(component):
            indent = "  " * self._indent_level
            prefix = f"[{component}]" if component else "[TRACE]"
            self.console.print(f"{indent}[magenta dim]{prefix}[/magenta dim] {message}")
            if raw_data:
                # Truncate very long data
                if len(raw_data) > 1000:
                    raw_data = (
                        raw_data[:1000]
                        + f"... (truncated, {len(raw_data)} chars total)"
                    )
                self.console.print(Panel(raw_data, title="Raw Data", style="dim"))

    def table(
        self,
        title: str,
        headers: List[str],
        rows: List[List[str]],
        show_in_normal: bool = True,
    ):
        """Display a formatted table"""
        if self.level >= LogLevel.VERBOSE or show_in_normal:
            table = Table(title=title, show_header=True, header_style="bold")
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*row)
            self.console.print(table)

    def tree(self, title: str, items: Dict[str, Any], show_in_normal: bool = False):
        """Display a tree structure"""
        if self.level >= LogLevel.VERBOSE or show_in_normal:
            tree = Tree(title)
            self._build_tree(tree, items)
            self.console.print(tree)

    def _build_tree(self, tree: Tree, items: Dict[str, Any]):
        """Recursively build a tree"""
        for key, value in items.items():
            if isinstance(value, dict):
                branch = tree.add(key)
                self._build_tree(branch, value)
            else:
                tree.add(f"{key}: {value}")

    def code_diff(
        self,
        file_path: str,
        line_start: int,
        line_end: int,
        before: List[str],
        after: List[str],
    ):
        """Show a code diff in a nice format"""
        if self.level >= LogLevel.VERBOSE:
            self.console.print(f"\n[bold]📝 {file_path}:{line_start}-{line_end}[/bold]")
            self.console.print("─" * 50)

            # Show before
            if before:
                for i, line in enumerate(before, start=line_start):
                    self.console.print(f"[red]- {i:4d} | {line}[/red]")

            # Show after
            if after:
                for i, line in enumerate(after, start=line_start):
                    self.console.print(f"[green]+ {i:4d} | {line}[/green]")

            self.console.print("─" * 50)


# Global logger instance
_logger: Optional[NovaLogger] = None


def get_logger() -> NovaLogger:
    """Get the global logger instance"""
    global _logger
    if _logger is None:
        # Default to normal unless overridden
        _logger = NovaLogger(level=LogLevel.NORMAL)
    return _logger


def set_logger(logger: NovaLogger):
    """Set the global logger instance"""
    global _logger
    _logger = logger


def create_logger(
    verbose: bool = False,
    debug: bool = False,
    trace: bool = False,
    components: Optional[List[str]] = None,
) -> NovaLogger:
    """Create a logger with the specified verbosity level"""
    if trace:
        level = LogLevel.TRACE
    elif debug:
        level = LogLevel.DEBUG
    elif verbose:
        level = LogLevel.VERBOSE
    else:
        level = LogLevel.NORMAL

    logger = NovaLogger(level=level)
    if components:
        logger.set_components_filter(components)
    return logger
