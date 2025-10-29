"""
Módulo de utilitários do sistema
"""

from .duplicate_remover import (
    DuplicateRemover, 
    DuplicateStats, 
    duplicate_remover,
    remove_duplicates_from_results,
    get_duplicate_stats
)

__all__ = [
    'DuplicateRemover',
    'DuplicateStats', 
    'duplicate_remover',
    'remove_duplicates_from_results',
    'get_duplicate_stats'
]