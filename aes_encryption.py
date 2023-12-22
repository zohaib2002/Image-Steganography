import base64
import hashlib

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher(object):
    def __init__(self: "AESCipher", key: str) -> None:
        self.bs = AES.block_size
        # Convert the password of any length into a 32 byte key
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self: "AESCipher", raw: str) -> str:
        'Encrypts string data and returns the encrypted string'
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode())).decode("utf-8")

    def decrypt(self: "AESCipher", enc: bytes) -> str:
        'Decrypts string data and returns the decrypted string'
        enc = base64.b64decode(enc)
        iv = enc[: AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        return (cipher.decrypt(enc[AES.block_size :])).decode("utf-8")
