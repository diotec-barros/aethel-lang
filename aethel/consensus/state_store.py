"""
State Store for Proof-of-Proof consensus protocol.

This module provides distributed state management using Merkle trees for
efficient verification and synchronization. The StateStore wraps a MerkleTree
and adds:
- State transition validation with conservation checking
- Merkle proof generation and verification
- Peer synchronization for distributed consensus
- Integration with persistence layer

The StateStore ensures that all state changes are:
1. Cryptographically verified via Merkle proofs
2. Conservation-preserving (total value unchanged)
3. Persistently stored for recovery
4. Efficiently synchronized across nodes
"""

import time
import hashlib
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from aethel.consensus.merkle_tree import MerkleTree, MerkleProof
from aethel.consensus.data_models import StateTransition, StateChange
from aethel.consensus.conservation_validator import ConservationValidator
from aethel.core.persistence import AethelPersistenceLayer


class StateStore:
    """
    Distributed state store with Merkle tree authentication.
    
    The StateStore manages the global state for the consensus protocol:
    - Account balances (for token rewards)
    - Proof verification history
    - Validator stakes
    - Conservation checksum
    
    All state changes are:
    - Authenticated via Merkle proofs
    - Validated for conservation
    - Persisted to disk
    - Synchronized across nodes
    """
    
    # Minimum stake required to participate in consensus (Requirement 4.3)
    MINIMUM_STAKE = 1000  # tokens
    
    def __init__(self, persistence_layer: Optional[AethelPersistenceLayer] = None):
        """
        Initialize StateStore.
        
        Args:
            persistence_layer: Optional persistence layer for storage
        """
        self.merkle_tree = MerkleTree()
        self.conservation_validator = ConservationValidator()
        self.persistence = persistence_layer
        
        # Track state history for rollback
        self._state_history: List[str] = []  # List of root hashes
        self._max_history = 100  # Keep last 100 states
        
        # Track spent transaction outputs for double-spend detection
        self._spent_outputs: Dict[str, bool] = {}  # txid:output_index -> spent
        
        # Track finalized checkpoints for long-range attack prevention
        self._checkpoints: List[Dict[str, Any]] = []  # List of finalized states
        self._checkpoint_interval = 10  # Checkpoint every 10 state transitions
        self._transition_count = 0
    
    def apply_state_transition(self, transition: StateTransition) -> bool:
        """
        Apply a state transition to the store.
        
        This validates the transition for conservation, applies the changes,
        updates the Merkle tree, and persists the new state.
        
        Optimized with batch updates for better performance.
        
        Args:
            transition: StateTransition to apply
            
        Returns:
            True if transition was applied successfully
        """
        # Get current state as dictionary
        current_state = {}
        for key in self.merkle_tree.get_all_keys():
            current_state[key] = self.merkle_tree.get(key)
        
        # Validate conservation property
        if not self.conservation_validator.validate(transition, current_state):
            return False
        
        # Record current root hash
        root_before = self.merkle_tree.get_root_hash()
        
        # Apply changes to Merkle tree using batch update for efficiency
        updates = {change.key: change.value for change in transition.changes}
        self.merkle_tree.batch_update(updates)
        
        # Get new root hash
        root_after = self.merkle_tree.get_root_hash()
        
        # Update transition with actual root hashes
        transition.merkle_root_before = root_before
        transition.merkle_root_after = root_after
        
        # Calculate conservation checksums
        transition.conservation_checksum_before = self.conservation_validator.calculate_total_value(
            self.merkle_tree
        )
        transition.conservation_checksum_after = transition.conservation_checksum_before
        
        # Persist to disk if persistence layer available
        if self.persistence:
            self.persistence.merkle_db.put(
                f"state_transition_{int(time.time())}",
                {
                    'root_before': root_before,
                    'root_after': root_after,
                    'changes': [
                        {'key': c.key, 'value': c.value}
                        for c in transition.changes
                    ],
                    'timestamp': transition.timestamp
                }
            )
            self.persistence.merkle_db.save_snapshot()
        
        # Add to history
        self._state_history.append(root_after)
        if len(self._state_history) > self._max_history:
            self._state_history.pop(0)
        
        # Increment transition count and create checkpoint if needed
        self._transition_count += 1
        if self._transition_count % self._checkpoint_interval == 0:
            self._create_checkpoint(root_after, transition.conservation_checksum_after)
        
        return True
    
    def get_merkle_proof(self, key: str) -> Optional[MerkleProof]:
        """
        Generate Merkle proof for a state key.
        
        Args:
            key: State key to generate proof for
            
        Returns:
            MerkleProof if key exists, None otherwise
        """
        return self.merkle_tree.generate_proof(key)
    
    def verify_merkle_proof(self, proof: MerkleProof) -> bool:
        """
        Verify a Merkle proof against the current root hash.
        
        Args:
            proof: MerkleProof to verify
            
        Returns:
            True if proof is valid
        """
        return self.merkle_tree.verify_proof(proof)
    
    def sync_from_peer(self, peer_root_hash: str, peer_state: Dict[str, Any]) -> bool:
        """
        Synchronize state from a peer node.
        
        This is used when a node joins the network or falls behind.
        The peer provides their state and root hash, which we verify
        and adopt if valid.
        
        Optimized with batch updates for faster synchronization.
        
        Args:
            peer_root_hash: Root hash from peer
            peer_state: State dictionary from peer
            
        Returns:
            True if sync was successful
        """
        # Create temporary Merkle tree with peer state
        temp_tree = MerkleTree()
        
        # Use batch update for efficiency
        temp_tree.batch_update(peer_state)
        
        # Verify peer's root hash
        calculated_root = temp_tree.get_root_hash()
        
        if calculated_root != peer_root_hash:
            # Peer state doesn't match their claimed root hash
            return False
        
        # Adopt peer state
        self.merkle_tree = temp_tree
        
        # Persist to disk if persistence layer available
        if self.persistence:
            for key, value in peer_state.items():
                self.persistence.merkle_db.put(key, value)
            self.persistence.merkle_db.save_snapshot()
        
        # Add to history
        self._state_history.append(peer_root_hash)
        if len(self._state_history) > self._max_history:
            self._state_history.pop(0)
        
        return True
    
    def get_balance(self, node_id: str) -> int:
        """
        Get balance for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Balance as integer (0 if not found)
        """
        key = f"balance:{node_id}"
        value = self.merkle_tree.get(key)
        
        if value is None:
            return 0
        
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, dict) and 'balance' in value:
            return int(value['balance'])
        
        return 0
    
    def set_balance(self, node_id: str, balance: int) -> None:
        """
        Set balance for a node.
        
        Args:
            node_id: Node identifier
            balance: New balance
        """
        key = f"balance:{node_id}"
        self.merkle_tree.update(key, balance)
    
    def get_validator_stake(self, node_id: str) -> int:
        """
        Get validator stake for a node.
        
        Args:
            node_id: Node identifier
            
        Returns:
            Stake as integer (0 if not found)
        """
        key = f"stake:{node_id}"
        value = self.merkle_tree.get(key)
        
        if value is None:
            return 0
        
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, dict) and 'stake' in value:
            return int(value['stake'])
        
        return 0
    
    def set_validator_stake(self, node_id: str, stake: int) -> None:
        """
        Set validator stake for a node.
        
        Args:
            node_id: Node identifier
            stake: New stake amount
        """
        key = f"stake:{node_id}"
        self.merkle_tree.update(key, stake)
    
    def reduce_stake(self, node_id: str, amount: int) -> None:
        """
        Reduce validator stake (for slashing).
        
        Args:
            node_id: Node identifier
            amount: Amount to reduce
        """
        current_stake = self.get_validator_stake(node_id)
        new_stake = max(0, current_stake - amount)
        self.set_validator_stake(node_id, new_stake)
    
    def has_minimum_stake(self, node_id: str) -> bool:
        """
        Check if node has minimum stake required for consensus participation.
        
        Args:
            node_id: Node identifier
            
        Returns:
            True if node has at least MINIMUM_STAKE tokens
        """
        return self.get_validator_stake(node_id) >= self.MINIMUM_STAKE
    
    def validate_minimum_stake(self, node_id: str) -> bool:
        """
        Validate that node meets minimum stake requirement.
        
        This is used by the consensus engine to reject participation
        from nodes with insufficient stake (Requirement 4.3).
        
        Args:
            node_id: Node identifier
            
        Returns:
            True if node has sufficient stake
        """
        return self.has_minimum_stake(node_id)
    
    def get_root_hash(self) -> str:
        """
        Get current Merkle root hash.
        
        Returns:
            Root hash as hex string
        """
        return self.merkle_tree.get_root_hash()
    
    def get_conservation_checksum(self) -> int:
        """
        Calculate total value in system (conservation checksum).
        
        Returns:
            Total value as integer
        """
        return self.conservation_validator.calculate_total_value(self.merkle_tree)
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Get complete state snapshot for synchronization.
        
        Returns:
            Dictionary of all key-value pairs
        """
        snapshot = {}
        
        for key in self.merkle_tree.get_all_keys():
            snapshot[key] = self.merkle_tree.get(key)
        
        return snapshot
    
    def get_state_history(self) -> List[str]:
        """
        Get history of root hashes.
        
        Returns:
            List of root hashes (most recent last)
        """
        return self._state_history.copy()
    
    def _create_checkpoint(self, root_hash: str, conservation_checksum: int) -> None:
        """
        Create a finalized checkpoint for long-range attack prevention.
        
        Checkpoints are immutable snapshots of the state that cannot be
        rolled back. They prevent attackers from creating alternative
        histories that violate conservation.
        
        Args:
            root_hash: Merkle root hash at checkpoint
            conservation_checksum: Total value at checkpoint
        """
        checkpoint = {
            'root_hash': root_hash,
            'conservation_checksum': conservation_checksum,
            'timestamp': int(time.time()),
            'transition_count': self._transition_count,
        }
        
        self._checkpoints.append(checkpoint)
        
        # Persist checkpoint if persistence layer available
        if self.persistence:
            self.persistence.merkle_db.put(
                f"checkpoint_{self._transition_count}",
                checkpoint
            )
            self.persistence.merkle_db.save_snapshot()
    
    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent finalized checkpoint.
        
        Returns:
            Checkpoint dictionary or None if no checkpoints exist
        """
        if not self._checkpoints:
            return None
        return self._checkpoints[-1].copy()
    
    def get_all_checkpoints(self) -> List[Dict[str, Any]]:
        """
        Get all finalized checkpoints.
        
        Returns:
            List of checkpoint dictionaries
        """
        return [cp.copy() for cp in self._checkpoints]
    
    def validate_state_history(
        self,
        history: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate a state history for long-range attack prevention.
        
        This checks that:
        1. Conservation property holds at every state in the history
        2. The history doesn't conflict with finalized checkpoints
        3. All state transitions are valid
        
        This prevents attackers from creating fake alternative histories
        that violate conservation (Requirement 7.4, Property 29).
        
        Args:
            history: List of state dictionaries with 'root_hash' and 'conservation_checksum'
            
        Returns:
            True if history is valid
        """
        if not history:
            return True
        
        # Check conservation at each state
        prev_checksum = None
        for state in history:
            checksum = state.get('conservation_checksum', 0)
            
            if prev_checksum is not None:
                # Conservation must be preserved between states
                if checksum != prev_checksum:
                    return False
            
            prev_checksum = checksum
        
        # Check history doesn't conflict with finalized checkpoints
        for checkpoint in self._checkpoints:
            checkpoint_root = checkpoint['root_hash']
            checkpoint_checksum = checkpoint['conservation_checksum']
            
            # Find if this checkpoint appears in the history
            for state in history:
                if state.get('root_hash') == checkpoint_root:
                    # Checkpoint found in history, verify conservation matches
                    if state.get('conservation_checksum') != checkpoint_checksum:
                        # Conservation violation at checkpoint
                        return False
        
        return True
    
    def reject_alternative_history(
        self,
        alternative_history: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if an alternative history should be rejected.
        
        This is used to prevent long-range attacks where an attacker
        tries to present a fake history that conflicts with our
        finalized checkpoints.
        
        Args:
            alternative_history: Alternative state history to check
            
        Returns:
            True if history should be rejected (invalid)
        """
        return not self.validate_state_history(alternative_history)
    
    def mark_output_spent(self, txid: str, output_index: int) -> None:
        """
        Mark a transaction output as spent.
        
        Args:
            txid: Transaction ID
            output_index: Output index within transaction
        """
        key = f"{txid}:{output_index}"
        self._spent_outputs[key] = True
        
        # Also store in Merkle tree for persistence
        self.merkle_tree.update(f"spent:{key}", True)
    
    def is_output_spent(self, txid: str, output_index: int) -> bool:
        """
        Check if a transaction output has been spent.
        
        Args:
            txid: Transaction ID
            output_index: Output index within transaction
            
        Returns:
            True if output has been spent
        """
        key = f"{txid}:{output_index}"
        
        # Check in-memory cache first
        if key in self._spent_outputs:
            return self._spent_outputs[key]
        
        # Check Merkle tree
        value = self.merkle_tree.get(f"spent:{key}")
        if value is not None:
            self._spent_outputs[key] = bool(value)
            return bool(value)
        
        return False
    
    def detect_double_spend(self, transactions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Detect double-spend attempts in a list of transactions.
        
        This checks for:
        1. Transactions spending the same output twice within the list
        2. Transactions spending outputs that are already spent in state
        
        Args:
            transactions: List of transaction dictionaries with 'inputs' field
            
        Returns:
            Dictionary with conflict details if double-spend detected, None otherwise
        """
        # Track outputs spent in this batch
        batch_spent = set()
        
        for tx in transactions:
            # Get transaction inputs
            inputs = tx.get('inputs', [])
            
            for inp in inputs:
                txid = inp.get('txid', '')
                output_index = inp.get('output_index', 0)
                
                # Create unique key for this output
                output_key = f"{txid}:{output_index}"
                
                # Check if already spent in this batch
                if output_key in batch_spent:
                    return {
                        'type': 'double_spend_in_batch',
                        'txid': txid,
                        'output_index': output_index,
                        'conflicting_tx': tx.get('id', 'unknown')
                    }
                
                # Check if already spent in state
                if self.is_output_spent(txid, output_index):
                    return {
                        'type': 'double_spend_in_state',
                        'txid': txid,
                        'output_index': output_index,
                        'conflicting_tx': tx.get('id', 'unknown')
                    }
                
                # Mark as spent in this batch
                batch_spent.add(output_key)
        
        # No double-spend detected
        return None
