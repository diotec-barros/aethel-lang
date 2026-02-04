"""Aethel Core Components"""

from aethel.core.parser import AethelParser
from aethel.core.judge import AethelJudge
from aethel.core.bridge import AethelBridge
from aethel.core.kernel import AethelKernel
from aethel.core.vault import AethelVault
from aethel.core.vault_distributed import AethelDistributedVault
from aethel.core.weaver import AethelWeaver

# v1.7.0 Oracle Sanctuary
from aethel.core.oracle import (
    OracleRegistry,
    OracleVerifier,
    OracleSimulator,
    OracleProof,
    OracleStatus,
    get_oracle_registry,
    fetch_oracle_data,
    verify_oracle_proof
)

__all__ = [
    'AethelParser',
    'AethelJudge',
    'AethelBridge',
    'AethelKernel',
    'AethelVault',
    'AethelDistributedVault',
    'AethelWeaver',
    # Oracle v1.7.0
    'OracleRegistry',
    'OracleVerifier',
    'OracleSimulator',
    'OracleProof',
    'OracleStatus',
    'get_oracle_registry',
    'fetch_oracle_data',
    'verify_oracle_proof',
]
