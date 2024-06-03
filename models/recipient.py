from dataclasses import dataclass

from eth_typing import ChecksumAddress


@dataclass
class Recipient:
    address: ChecksumAddress
    amount: str
