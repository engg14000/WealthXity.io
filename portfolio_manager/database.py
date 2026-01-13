"""
WealthPulse Database Module
Provides backward-compatible interface to storage layer
"""
from portfolio_manager.storage import (
    get_sheet_names,
    get_data,
    save_data,
    export_to_excel,
    import_from_excel,
    get_storage,
    set_storage_mode,
    get_config,
    save_config,
    DATA_FILE
)

# Re-export all functions for backward compatibility
__all__ = [
    'get_sheet_names',
    'get_data', 
    'save_data',
    'export_to_excel',
    'import_from_excel',
    'get_storage',
    'set_storage_mode',
    'get_config',
    'save_config',
    'DATA_FILE'
]

