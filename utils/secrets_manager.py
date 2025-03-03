import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from cryptography.fernet import Fernet

class SecretsManager:
    DEFAULT_KEY_PATH = Path.home() / '.secrets' / 'pybit' / 'secret.key'
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'secrets.yml'

    def __init__(
        self,
        config_path: Optional[Union[Path, str]] = None,
        key_path: Optional[Union[Path, str]] = None,
        env_key: str = 'PYBIT_ENCRYPTION_KEY'
    ):
        """
        Initialize SecretsManager with configuration and encryption key.
        
        Args:
            config_path: Path to YAML config file (default: project_root/config/config.yml)
            key_path: Path to encryption key file (default: ~/.secrets/pybit/secret.key)
            env_key: Environment variable name for the encryption key
        """
        if config_path is None:
            config_path = self.DEFAULT_CONFIG_PATH
        if key_path is None:
            key_path = self.DEFAULT_KEY_PATH
        self.config_path = self._ensure_path(config_path)
        self.key_path = self._ensure_path(key_path)
        self.env_key = env_key
        self.fernet = self._initialize_encryption()

    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption by getting key from environment or file."""
        key = os.environ.get(self.env_key)
        if key:
            return Fernet(key.encode())

        if self.key_path.exists():
            key = self.key_path.read_bytes()
            return Fernet(key)

        raise ValueError(
            f"No encryption key found at {self.key_path} "
            f"or in environment variable {self.env_key}"
        )
    
    @staticmethod
    def _ensure_path(path: Optional[Union[Path, str]]) -> Path:
        """Convert string or Path to Path with expanded user directory."""
        if path is None:
            raise ValueError("Path cannot be None")
        return path.expanduser() if isinstance(path, Path) else Path(path).expanduser()

    @staticmethod
    def setup_key_storage(key_path: Optional[Union[Path, str]] = None) -> str:
        """
        Set up the key storage directory and generate a new key if it doesn't exist.
        
        Args:
            key_path: Path to store the encryption key (default: ~/.secrets/pybit/secret.key)
            
        Returns:
            str: Path to the key file
        """
        if key_path is None:
            key_path = SecretsManager.DEFAULT_KEY_PATH
        key_path = self._ensure_path(key_path)
        key_dir = key_path.parent

        if not key_dir.exists():
            key_dir.mkdir(mode=0o700, parents=True)

        if not key_path.exists():
            key = Fernet.generate_key()
            key_path.write_bytes(key)
            key_path.chmod(0o600)

        return str(key_path)

    @staticmethod
    def setup_config_directory(config_path: Optional[Union[Path, str]] = None) -> str:
        """
        Set up the configuration directory structure.
        
        Args:
            config_path: Path to store the configuration file (default: project_root/config/secrets.yml)
            
        Returns:
            str: Path to the config file
        """
        if config_path is None:
            config_path = SecretsManager.DEFAULT_CONFIG_PATH
        config_path = self._ensure_path(config_path)
        config_dir = config_path.parent

        if not config_dir.exists():
            config_dir.mkdir(parents=True)

        return str(config_path)

    def load_config(self) -> Dict[str, Any]:
        """
        Load and decrypt configuration from YAML file.
        
        Returns:
            Dict containing configuration values
        """
        if not self.config_path.exists():
            return {}

        with self.config_path.open('r') as f:
            config = yaml.safe_load(f) or {}

        return self._process_config_dict(config, decrypt=True)

    def save_config(self, config: Dict[str, Any], encrypt_fields: Optional[List[str]] = None) -> None:
        """
        Save configuration to YAML file, encrypting specified fields.
        
        Args:
            config: Configuration dictionary to save
            encrypt_fields: List of field paths to encrypt (e.g., ['database.password', 'api_key'])
        """
        if encrypt_fields:
            config = self._process_config_dict(
                config,
                decrypt=False,
                fields_to_process=set(encrypt_fields)
            )

        with self.config_path.open('w') as f:
            yaml.dump(config, f)

    def _process_config_dict(
        self,
        config: Dict[str, Any],
        decrypt: bool = True,
        fields_to_process: Optional[set] = None,
        current_path: str = ''
    ) -> Dict[str, Any]:
        """
        Process configuration dictionary recursively, encrypting or decrypting values.
        
        Args:
            config: Configuration dictionary
            decrypt: If True, decrypt values; if False, encrypt values
            fields_to_process: Set of field paths to process
            current_path: Current path in the config hierarchy
            
        Returns:
            Processed configuration dictionary
        """
        result = {}
        
        for key, value in config.items():
            path = f"{current_path}.{key}" if current_path else key
            
            if isinstance(value, dict):
                if value.get('encrypted', False):
                    if decrypt:
                        encrypted_value = value['value'].encode()
                        result[key] = self.fernet.decrypt(encrypted_value).decode()
                    else:
                        result[key] = value
                else:
                    result[key] = self._process_config_dict(
                        value,
                        decrypt,
                        fields_to_process,
                        path
                    )
            else:
                if not decrypt and fields_to_process and path in fields_to_process:
                    encrypted_value = self.fernet.encrypt(str(value).encode())
                    result[key] = {
                        'encrypted': True,
                        'value': encrypted_value.decode()
                    }
                else:
                    result[key] = value
                    
        return result

    def get_secret(self, path: Union[Path, str], default: Any = None) -> Any:
        """
        Get a secret value from the configuration using dot notation.
        
        Args:
            path: Path to the secret (e.g., 'database.password')
            default: Default value if path doesn't exist
            
        Returns:
            Secret value or default if not found
        """
        config = self.load_config()
        parts = str(path).split('.')
        
        for part in parts:
            if isinstance(config, dict):
                config = config.get(part, default)
            else:
                return default
                
        return config