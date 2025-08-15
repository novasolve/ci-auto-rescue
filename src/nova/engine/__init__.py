"""
Nova CI-Rescue Engine modules for robust patch application and source resolution.
"""

from .source_resolver import SourceResolver
from .patch_guard import preflight_patch_checks
from .patch_applier import apply_patch_with_fallback, PatchApplyError
from .post_apply_check import ast_sanity_check

__all__ = [
    'SourceResolver',
    'preflight_patch_checks',
    'apply_patch_with_fallback',
    'PatchApplyError',
    'ast_sanity_check',
]
