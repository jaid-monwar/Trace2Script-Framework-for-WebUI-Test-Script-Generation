import base64
import logging
import os
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApiKeyDecrypterService:
    
    def __init__(self, private_key_path: str = "private_key.pem"):
        self.private_key_path = private_key_path
        self._private_key = None
    
    def _load_private_key(self):
        try:
            if not os.path.exists(self.private_key_path):
                raise FileNotFoundError(f"Private key file not found: {self.private_key_path}")
            
            with open(self.private_key_path, "rb") as key_file:
                self._private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
            logger.info(f"Private key loaded successfully from {self.private_key_path}")
            
        except Exception as e:
            logger.error(f"Failed to load private key from {self.private_key_path}: {e}")
            raise
    
    def decrypt_api_key(self, base64_encrypted: str) -> Optional[str]:
        try:
            if self._private_key is None:
                self._load_private_key()
            
            encrypted_data = base64.b64decode(base64_encrypted)
            logger.info(f"Encrypted data length: {len(encrypted_data)} bytes")
            
            pad_scheme = padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
            
            decrypted = self._private_key.decrypt(encrypted_data, pad_scheme)
            
            decrypted_api_key = decrypted.decode("utf-8")
            logger.info("API key decrypted successfully")
            return decrypted_api_key
            
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            return None
    
    def is_encrypted(self, api_key: str) -> bool:
        if not api_key:
            return False
        
        try:
            decoded = base64.b64decode(api_key, validate=True)
            return len(decoded) > 50
        except Exception:
            return False
    
    def decrypt_if_encrypted(self, api_key: str) -> str:
        if not api_key:
            return api_key
        
        if self.is_encrypted(api_key):
            logger.info("API key appears to be encrypted, attempting to decrypt")
            decrypted = self.decrypt_api_key(api_key)
            return decrypted if decrypted else api_key
        else:
            logger.debug("API key appears to be plain text, returning as-is")
            return api_key


_decrypter_service = None


def get_api_key_decrypter(private_key_path: str = "private_key.pem") -> ApiKeyDecrypterService:
    global _decrypter_service
    if _decrypter_service is None:
        _decrypter_service = ApiKeyDecrypterService(private_key_path)
    return _decrypter_service


if __name__ == "__main__":
    decrypter = ApiKeyDecrypterService()
    
    example_encrypted = "LGpgyCyf9fCOCPaK6XVCryiCINJiqs36+GNJyit6cP9Vh+YSOqg0sLyRbE6x0UQLJi1O6K7EZx6ij7acDfVijeMXNdDY2e1YoNPBfZMP1ndS5ffW0DyANipVnsqHbzlq+PwDjl23sDVZma2afJaKqW7MgtdSYwpxKLLYQlaENVIVAaGTFTNcLUnN04Jb0NvK06yspQlr7wwAoxdB6hvGuz0XdnN8HIxu9Ade0WGyUKsH0FiREuyrGkm4Zz/DLrPZJdzoSL1KWPPbxVPtad5SbKJXjYKKuHuRZInfLMjNCx+hTOR/lCBO+JrXXOokYp/wCNPJ+qF4WhgKw3OjtOdksw=="
    
    try:
        decrypted_key = decrypter.decrypt_api_key(example_encrypted)
        if decrypted_key:
            print(f"Decrypted API key: {decrypted_key}")
        else:
            print("Failed to decrypt API key")
    except Exception as e:
        print(f"Error: {e}")