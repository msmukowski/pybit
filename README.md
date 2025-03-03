# pybit

## Development Setup

### Python Environment

1. **Prerequisites**: Install [pyenv](https://github.com/pyenv/pyenv) with [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

2. **Setup virtual environment**:
   ```bash
   # Create virtualenv (only needed once)
   pyenv virtualenv 3.10.0 pybit  # Replace with your preferred Python version
   
   # Activate the environment
   pyenv local pybit
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Run Jupyter**:
   ```bash
   jupyter notebook
   ```

## Secrets Management

The project uses a secure secrets management system that encrypts sensitive configuration values. The system stores encryption keys in `~/.secrets/pybit/` and configuration in `config/secrets.yml`.

### Usage

```python
from utils.secrets_manager import SecretsManager

# Initialize
secrets = SecretsManager()

# Get a secret
db_password = secrets.get_secret('database.password')
api_key = secrets.get_secret('api.key')
```

### Security Notes

- Encryption key is stored in `~/.secrets/pybit/secret.key`
- Configuration file and keys are excluded from git
- Directory permissions are set to 700 (user access only)
- Key file permissions are set to 600 (user read/write only)

For more details, see `utils/secrets_manager.py`.