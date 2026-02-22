"""
Configuration and environment management for the Adaptive Integration Layer.
Centralizes all configuration to ensure consistency and easy maintenance.
"""
import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import json

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str
    private_key: str
    client_email: str
    database_url: str
    
    @classmethod
    def from_env(cls) -> Optional['FirebaseConfig']:
        """Load Firebase config from environment variables"""
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        private_key = os.getenv('FIREBASE_PRIVATE_KEY')
        client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        database_url = os.getenv('FIREBASE_DATABASE_URL')
        
        if not all([project_id, private_key, client_email, database_url]):
            return None
            
        # Replace escaped newlines in private key
        private_key = private_key.replace('\\n', '\n')
        
        return cls(
            project_id=project_id,
            private_key=private_key,
            client_email=client_email,
            database_url=database_url
        )
    
    @classmethod
    def from_file(cls, filepath: str = 'firebase_config.json') -> Optional['FirebaseConfig']:
        """Load Firebase config from JSON file"""
        path = Path(filepath)
        if not path.exists():
            return None
            
        try:
            with open(path, 'r') as f:
                config_data = json.load(f)
                
            return cls(
                project_id=config_data.get('project_id', ''),
                private_key=config_data.get('private_key', '').replace('\\n', '\n'),
                client_email=config_data.get('client_email', ''),
                database_url=config_data.get('database_url', '')
            )
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"Error loading Firebase config: {e}")
            return None

@dataclass
class IntegrationConfig:
    """Integration layer configuration"""
    # Performance thresholds
    latency_threshold_ms: int = 5000  # 5 seconds
    error_rate_threshold: float = 0.1  # 10%
    min_samples_for_evaluation: int = 10
    
    # Adaptation settings
    adaptation_interval_minutes: int = 5
    max_failover_attempts: int = 3
    cooloff_period_seconds: int = 300  # 5 minutes
    
    # Monitoring settings
    metrics_retention_days: int = 30
    alert_window_minutes: int = 15

class ConfigManager:
    """Central configuration manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.firebase_config = None
            self.integration_config = IntegrationConfig()
            self.load_configurations()
            self.initialized = True
    
    def load_configurations(self):
        """Load all configurations with fallback strategy"""
        # Try environment variables first
        self.firebase_config = FirebaseConfig.from_env()
        
        # Fallback to file
        if not self.firebase_config:
            self.firebase_config = FirebaseConfig.from_file()
        
        # Validate Firebase config
        if not self.firebase_config:
            raise ValueError(
                "Firebase configuration not found. "
                "Set environment variables or create firebase_config.json"
            )
        
        # Validate required fields
        if not all([
            self.firebase_config.project_id,
            self.firebase_config.private_key,
            self.firebase_config.client_email,
            self.firebase_config.database_url
        ]):
            raise ValueError("Firebase configuration incomplete")
    
    def get_firebase_credentials(self) -> dict:
        """Get Firebase credentials dictionary"""
        return {
            'type': 'service_account',
            'project_id': self.firebase_config.project_id,
            'private_key': self.firebase_config.private_key,
            'client_email': self.firebase_config.client_email,
            'token_uri': 'https://oauth2.googleapis.com/token'
        }
    
    def