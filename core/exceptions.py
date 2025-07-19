import logging

logger = logging.getLogger(__name__)

class SanctifyError(Exception):
    """Custom exception for Sanctify Live with unique error codes."""
    def __init__(self, module: str, error_code: str, message: str):
        self.module = module
        self.error_code = error_code
        self.message = f"[{module}] {error_code}: {message}"
        super().__init__(self.message)
        logger.error(self.message, exc_info=True)