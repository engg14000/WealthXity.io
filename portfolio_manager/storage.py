"""
Storage abstraction layer for WealthPulse
Supports: Excel (local), Firebase Firestore (cloud), and In-Memory (browser-based)
"""
import pandas as pd
import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

# Storage mode configuration file
CONFIG_FILE = os.path.join('data', 'config.json')
DATA_FILE = os.path.join('data', 'wealthpulse.xlsx')

def get_config() -> Dict:
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {'storage_mode': 'browser', 'firebase_config': {}}

def save_config(config: Dict):
    """Save configuration to file"""
    os.makedirs('data', exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def get_collection_names(self) -> List[str]:
        """Get all collection/sheet names"""
        pass
    
    @abstractmethod
    def get_data(self, collection_name: str) -> pd.DataFrame:
        """Get data from a collection/sheet"""
        pass
    
    @abstractmethod
    def save_data(self, collection_name: str, df: pd.DataFrame):
        """Save data to a collection/sheet"""
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str):
        """Delete a collection/sheet"""
        pass

class ExcelStorage(StorageBackend):
    """Excel-based local storage"""
    
    def __init__(self, file_path: str = DATA_FILE):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create the Excel file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.file_path) if os.path.dirname(self.file_path) else '.', exist_ok=True)
        if not os.path.exists(self.file_path):
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                pd.DataFrame().to_excel(writer, sheet_name='Summary')
    
    def _get_workbook(self):
        """Get the Excel workbook"""
        return pd.ExcelFile(self.file_path)
    
    def get_collection_names(self) -> List[str]:
        """Get all sheet names"""
        wb = self._get_workbook()
        return wb.sheet_names
    
    def get_data(self, collection_name: str) -> pd.DataFrame:
        """Get data from a sheet"""
        wb = self._get_workbook()
        if collection_name in wb.sheet_names:
            return pd.read_excel(wb, sheet_name=collection_name)
        return pd.DataFrame()
    
    def save_data(self, collection_name: str, df: pd.DataFrame):
        """Save data to a sheet"""
        all_data = {}
        if os.path.exists(self.file_path):
            wb = self._get_workbook()
            for sheet in wb.sheet_names:
                if sheet != collection_name:
                    all_data[sheet] = pd.read_excel(wb, sheet_name=sheet)
        
        all_data[collection_name] = df
        
        with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
            for sheet, data in all_data.items():
                data.to_excel(writer, sheet_name=sheet, index=False)
    
    def delete_collection(self, collection_name: str):
        """Delete a sheet"""
        all_data = {}
        if os.path.exists(self.file_path):
            wb = self._get_workbook()
            for sheet in wb.sheet_names:
                if sheet != collection_name:
                    all_data[sheet] = pd.read_excel(wb, sheet_name=sheet)
        
        if all_data:
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                for sheet, data in all_data.items():
                    data.to_excel(writer, sheet_name=sheet, index=False)

class InMemoryStorage(StorageBackend):
    """In-memory storage for browser-based persistence via localStorage"""
    
    # Class-level storage to persist across instances, keyed by browser_id
    _all_browser_data: Dict[str, Dict[str, pd.DataFrame]] = {}
    _current_browser_id: Optional[str] = None
    
    def __init__(self):
        pass
    
    def _get_data_store(self) -> Dict[str, pd.DataFrame]:
        """Get the data store for current browser"""
        bid = InMemoryStorage._current_browser_id or 'default'
        if bid not in InMemoryStorage._all_browser_data:
            InMemoryStorage._all_browser_data[bid] = {'Summary': pd.DataFrame()}
        return InMemoryStorage._all_browser_data[bid]
    
    @classmethod
    def set_browser_id(cls, browser_id: str):
        """Set the current browser ID for this request"""
        cls._current_browser_id = browser_id
    
    @classmethod
    def get_browser_id(cls) -> Optional[str]:
        """Get the current browser ID"""
        return cls._current_browser_id
    
    def get_collection_names(self) -> List[str]:
        """Get all collection names"""
        return list(self._get_data_store().keys())
    
    def get_data(self, collection_name: str) -> pd.DataFrame:
        """Get data from in-memory store"""
        return self._get_data_store().get(collection_name, pd.DataFrame()).copy()
    
    def save_data(self, collection_name: str, df: pd.DataFrame):
        """Save data to in-memory store"""
        self._get_data_store()[collection_name] = df.copy()
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        store = self._get_data_store()
        if collection_name in store:
            del store[collection_name]
    
    def load_all_data(self, data: Dict[str, List[Dict]]):
        """Load all data from a dictionary (from client localStorage)"""
        bid = InMemoryStorage._current_browser_id or 'default'
        InMemoryStorage._all_browser_data[bid] = {}
        store = InMemoryStorage._all_browser_data[bid]
        for collection_name, records in data.items():
            if records:
                store[collection_name] = pd.DataFrame(records)
            else:
                store[collection_name] = pd.DataFrame()
        if 'Summary' not in store:
            store['Summary'] = pd.DataFrame()
    
    def export_all_data(self) -> Dict[str, List[Dict]]:
        """Export all data as a dictionary (for client localStorage)"""
        result = {}
        for collection_name, df in self._get_data_store().items():
            if not df.empty:
                records = df.to_dict('records')
                for record in records:
                    for k, v in record.items():
                        if pd.isna(v):
                            record[k] = None
                result[collection_name] = records
            else:
                result[collection_name] = []
        return result


class FirebaseStorage(StorageBackend):
    """Firebase Firestore cloud storage"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Check if already initialized
            try:
                self.app = firebase_admin.get_app()
            except ValueError:
                # Initialize with service account
                if self.config.get('service_account_path'):
                    cred = credentials.Certificate(self.config['service_account_path'])
                    self.app = firebase_admin.initialize_app(cred)
                elif self.config.get('service_account_json'):
                    cred = credentials.Certificate(self.config['service_account_json'])
                    self.app = firebase_admin.initialize_app(cred)
                else:
                    raise ValueError("Firebase credentials not configured")
            
            self.db = firestore.client()
        except ImportError:
            raise ImportError("firebase-admin package not installed. Run: pip install firebase-admin")
        except Exception as e:
            raise Exception(f"Failed to initialize Firebase: {str(e)}")
    
    def _get_user_collection(self) -> str:
        """Get the user's collection prefix"""
        return self.config.get('user_id', 'default_user')
    
    def get_collection_names(self) -> List[str]:
        """Get all collection names for the user"""
        user_ref = self.db.collection('users').document(self._get_user_collection())
        collections = user_ref.collections()
        return [col.id for col in collections]
    
    def get_data(self, collection_name: str) -> pd.DataFrame:
        """Get data from a Firestore collection"""
        user_ref = self.db.collection('users').document(self._get_user_collection())
        docs = user_ref.collection(collection_name).stream()
        
        records = []
        for doc in docs:
            record = doc.to_dict()
            record['_doc_id'] = doc.id
            records.append(record)
        
        if records:
            df = pd.DataFrame(records)
            # Remove internal doc_id from display
            if '_doc_id' in df.columns:
                df = df.drop('_doc_id', axis=1)
            return df
        return pd.DataFrame()
    
    def save_data(self, collection_name: str, df: pd.DataFrame):
        """Save data to a Firestore collection (replaces all data)"""
        user_ref = self.db.collection('users').document(self._get_user_collection())
        collection_ref = user_ref.collection(collection_name)
        
        # Delete existing documents
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
        
        # Add new documents
        records = df.to_dict('records')
        for i, record in enumerate(records):
            # Clean NaN values
            clean_record = {k: (v if pd.notna(v) else None) for k, v in record.items()}
            collection_ref.document(f'doc_{i}').set(clean_record)
    
    def delete_collection(self, collection_name: str):
        """Delete a Firestore collection"""
        user_ref = self.db.collection('users').document(self._get_user_collection())
        collection_ref = user_ref.collection(collection_name)
        
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()

# Global storage instance
_storage_instance: Optional[StorageBackend] = None

def get_storage() -> StorageBackend:
    """Get the current storage backend instance"""
    global _storage_instance
    
    if _storage_instance is None:
        config = get_config()
        storage_mode = config.get('storage_mode', 'browser')
        
        if storage_mode == 'firebase':
            try:
                _storage_instance = FirebaseStorage(config.get('firebase_config', {}))
            except Exception as e:
                print(f"Firebase initialization failed: {e}. Falling back to browser storage.")
                _storage_instance = InMemoryStorage()
        else:
            _storage_instance = InMemoryStorage()
    
    return _storage_instance

def set_storage_mode(mode: str, firebase_config: Optional[Dict] = None):
    """Set the storage mode and reinitialize"""
    global _storage_instance
    
    config = get_config()
    config['storage_mode'] = mode
    
    if firebase_config:
        config['firebase_config'] = firebase_config
    
    save_config(config)
    _storage_instance = None  # Force reinitialization
    
    return get_storage()

def reset_storage():
    """Reset storage instance (useful for testing)"""
    global _storage_instance
    _storage_instance = None

# Convenience functions (backward compatible with old database.py)
def get_sheet_names() -> List[str]:
    """Get all sheet/collection names"""
    return get_storage().get_collection_names()

def get_data(sheet_name: str) -> pd.DataFrame:
    """Get data from a sheet/collection"""
    return get_storage().get_data(sheet_name)

def save_data(sheet_name: str, df: pd.DataFrame):
    """Save data to a sheet/collection"""
    get_storage().save_data(sheet_name, df)

# Export/Import functions for data portability
def export_to_excel(file_path: str):
    """Export all data to an Excel file"""
    storage = get_storage()
    collections = storage.get_collection_names()
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for collection in collections:
            df = storage.get_data(collection)
            if not df.empty:
                df.to_excel(writer, sheet_name=collection, index=False)
            else:
                pd.DataFrame().to_excel(writer, sheet_name=collection, index=False)

def import_from_excel(file_path: str):
    """Import all data from an Excel file"""
    storage = get_storage()
    wb = pd.ExcelFile(file_path)
    
    for sheet_name in wb.sheet_names:
        df = pd.read_excel(wb, sheet_name=sheet_name)
        storage.save_data(sheet_name, df)

# For backward compatibility
DATA_FILE = DATA_FILE

# Browser storage helper functions
def load_browser_data(data: Dict[str, List[Dict]]):
    """Load data from browser localStorage into the in-memory storage"""
    storage = get_storage()
    if isinstance(storage, InMemoryStorage):
        storage.load_all_data(data)

def export_browser_data() -> Dict[str, List[Dict]]:
    """Export all data for browser localStorage"""
    storage = get_storage()
    if isinstance(storage, InMemoryStorage):
        return storage.export_all_data()
    # For non-InMemory storage, build export from storage
    result = {}
    for collection in storage.get_collection_names():
        df = storage.get_data(collection)
        if not df.empty:
            records = df.to_dict('records')
            for record in records:
                for k, v in record.items():
                    if pd.isna(v):
                        record[k] = None
            result[collection] = records
        else:
            result[collection] = []
    return result

def is_browser_storage() -> bool:
    """Check if browser storage mode is active"""
    config = get_config()
    return config.get('storage_mode') == 'browser'
