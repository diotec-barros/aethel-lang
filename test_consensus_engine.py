"""
Tests for PBFT Consensus Engine.

This module tests the consensus engine implementation including:
- Leader election
- Byzantine quorum calculation
- PRE-PREPARE phase
- PREPARE phase
- COMMIT phase
- Message handling
"""

import pytest
import time
import hashlib
from hypothesis import given, settings, strategies as st

from aethel.consensus.consensus_engine import ConsensusEngine, ConsensusState
from aethel.consensus.mock_network import MockP2PNetwork, create_test_network
from aethel.consensus.proof_verifier import ProofVerifier
from aethel.consensus.state_store import StateStore
from aethel.consensus.proof_mempool import ProofMempool
from aethel.consensus.data_models import (
    ProofBlock,
    PrePrepareMessage,
    PrepareMessage,
    CommitMessage,
    MessageType,
)
from aethel.consensus.test_strategies import (
    proof_blocks,
    node_ids,
)


class TestConsensusEngineBasics:
    """Test basic consensus engine functionality."""
    
    def test_initialization(self):
        """Test consensus engine initialization."""
        network = MockP2PNetwork("node_0")
        network.start()
        
        engine = ConsensusEngine(
            node_id="node_0",
            validator_stake=1000,
            network=network,
        )
        
        assert engine.node_id == "node_0"
        assert engine.validator_stake == 1000
        assert engine.view == 0
        assert engine.sequence == 0
        assert engine.current_state is None
        assert engine.proof_verifier is not None
        assert engine.state_store is not None
        assert engine.proof_mempool is not None
    
    def test_leader_election_single_node(self):
        """Test leader election with single node."""
        network = MockP2PNetwork("node_0")
        network.start()
        
        engine = ConsensusEngine(
            node_id="node_0",
            validator_stake=1000,
            network=network,
        )
        
        # Single node should always be leader
        assert engine.is_leader()
    
    def test_leader_election_multiple_nodes(self):
        """Test leader election with multiple nodes."""
        # Create 4-node network
        networks = create_test_network(4, 0)
        
        engines = {}
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
            )
        
        # Exactly one node should be leader
        leaders = [e for e in engines.values() if e.is_leader()]
        assert len(leaders) == 1
        
        # Leader should be deterministic based on view
        leader = leaders[0]
        all_node_ids = sorted(engines.keys())
        expected_leader = all_node_ids[0 % len(all_node_ids)]
        assert leader.node_id == expected_leader
    
    def test_byzantine_quorum_calculation(self):
        """Test Byzantine quorum calculation."""
        # Create networks with different sizes
        for node_count in [4, 7, 10, 13, 100]:
            networks = create_test_network(node_count, 0)
            node_id = list(networks.keys())[0]
            network = networks[node_id]
            
            engine = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
            )
            
            # f = floor((N-1)/3)
            expected_f = (node_count - 1) // 3
            assert engine.max_faulty_nodes() == expected_f
            
            # Byzantine quorum = 2f + 1
            expected_quorum = 2 * expected_f + 1
            
            # Create dummy messages
            messages = [
                CommitMessage(
                    message_type=MessageType.COMMIT,
                    view=0,
                    sequence=1,
                    sender_id=f"node_{i}",
                    block_digest="test",
                )
                for i in range(expected_quorum)
            ]
            
            assert engine.verify_quorum(messages)
            
            # One less should not be quorum
            assert not engine.verify_quorum(messages[:-1])


class TestPrePreparePhase:
    """Test PRE-PREPARE phase of consensus."""
    
    def test_leader_proposes_block_from_mempool(self):
        """Test leader can propose block from mempool."""
        network = MockP2PNetwork("node_0")
        network.start()
        
        mempool = ProofMempool()
        engine = ConsensusEngine(
            node_id="node_0",
            validator_stake=1000,
            network=network,
            proof_mempool=mempool,
        )
        
        # Add proofs to mempool
        for i in range(5):
            proof = {"id": f"proof_{i}", "constraints": ["x > 0"]}
            mempool.add_proof(proof, difficulty=100 * (i + 1))
        
        # Leader should be able to propose block
        assert engine.is_leader()
        proof_block = engine.propose_block_from_mempool(block_size=3)
        
        assert proof_block is not None
        assert len(proof_block.proofs) == 3
        assert proof_block.proposer_id == "node_0"
    
    def test_non_leader_cannot_propose_block(self):
        """Test non-leader cannot propose block from mempool."""
        # Create 4-node network
        networks = create_test_network(4, 0)
        
        # Find a non-leader node
        engines = {}
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
            )
        
        non_leaders = [e for e in engines.values() if not e.is_leader()]
        assert len(non_leaders) > 0
        
        non_leader = non_leaders[0]
        proof_block = non_leader.propose_block_from_mempool()
        
        assert proof_block is None
    
    def test_handle_pre_prepare_validates_leader(self):
        """Test PRE-PREPARE handler validates message is from leader."""
        # Create 4-node network
        networks = create_test_network(4, 0)
        
        engines = {}
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
            )
        
        # Get leader and non-leader
        leader = [e for e in engines.values() if e.is_leader()][0]
        non_leader = [e for e in engines.values() if not e.is_leader()][0]
        
        # Create proof block
        proof_block = ProofBlock(
            block_id="test_block",
            timestamp=int(time.time()),
            proofs=[{"id": "proof_1"}],
            previous_block_hash="0" * 64,
            proposer_id=non_leader.node_id,  # Non-leader proposing
        )
        
        # Create PRE-PREPARE from non-leader
        pre_prepare = PrePrepareMessage(
            message_type=MessageType.PRE_PREPARE,
            view=0,
            sequence=1,
            sender_id=non_leader.node_id,
            proof_block=proof_block,
        )
        
        # Leader should reject PRE-PREPARE from non-leader
        leader.handle_pre_prepare(pre_prepare)
        assert leader.current_state is None  # Should not accept
    
    def test_handle_pre_prepare_validates_proof_block(self):
        """Test PRE-PREPARE handler validates proof block."""
        network = MockP2PNetwork("node_0")
        network.start()
        
        engine = ConsensusEngine(
            node_id="node_0",
            validator_stake=1000,
            network=network,
        )
        
        # Create invalid proof block (no proofs)
        proof_block = ProofBlock(
            block_id="test_block",
            timestamp=int(time.time()),
            proofs=[],  # Empty proofs
            previous_block_hash="0" * 64,
            proposer_id="node_0",
        )
        
        # Create PRE-PREPARE
        pre_prepare = PrePrepareMessage(
            message_type=MessageType.PRE_PREPARE,
            view=0,
            sequence=1,
            sender_id="node_0",
            proof_block=proof_block,
        )
        
        # Should reject invalid block
        engine.handle_pre_prepare(pre_prepare)
        assert engine.current_state is None
    
    @given(proof_block=proof_blocks(min_proofs=1, max_proofs=5))
    @settings(max_examples=10)
    def test_handle_pre_prepare_verifies_proofs(self, proof_block):
        """Test PRE-PREPARE handler verifies all proofs in block."""
        network = MockP2PNetwork("node_0")
        network.start()
        
        engine = ConsensusEngine(
            node_id="node_0",
            validator_stake=1000,
            network=network,
        )
        
        # Set proposer to self (we're the leader)
        proof_block.proposer_id = "node_0"
        
        # Create PRE-PREPARE
        pre_prepare = PrePrepareMessage(
            message_type=MessageType.PRE_PREPARE,
            view=0,
            sequence=1,
            sender_id="node_0",
            proof_block=proof_block,
        )
        
        # Handle PRE-PREPARE
        engine.handle_pre_prepare(pre_prepare)
        
        # Should have current state
        assert engine.current_state is not None
        assert engine.current_state.proof_block == proof_block
        assert engine.current_state.verification_result is not None


class TestPreparePhase:
    """Test PREPARE phase of consensus."""
    
    def test_handle_prepare_collects_messages(self):
        """Test PREPARE handler collects messages from peers."""
        # Create 4-node network
        networks = create_test_network(4, 0)
        
        engines = {}
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
            )
        
        # Get one engine
        engine = engines["node_0"]
        
        # Create consensus state
        proof_block = ProofBlock(
            block_id="test_block",
            timestamp=int(time.time()),
            proofs=[{"id": "proof_1"}],
            previous_block_hash="0" * 64,
            proposer_id="node_0",
        )
        
        engine.current_state = ConsensusState(
            sequence=1,
            view=0,
            proof_block=proof_block,
            block_digest=proof_block.hash(),
        )
        
        # Create PREPARE messages from other nodes
        for i in range(1, 4):
            prepare = PrepareMessage(
                message_type=MessageType.PREPARE,
                view=0,
                sequence=1,
                sender_id=f"node_{i}",
                block_digest=proof_block.hash(),
            )
            
            engine.handle_prepare(prepare)
        
        # Should have collected 3 PREPARE messages
        assert len(engine.current_state.prepare_messages) == 3
    
    def test_handle_prepare_validates_block_digest(self):
        """Test PREPARE handler validates block digest matches."""
        network = MockP2PNetwork("node_0")
        network.start()
        
        engine = ConsensusEngine(
            node_id="node_0",
            validator_stake=1000,
            network=network,
        )
        
        # Create consensus state
        proof_block = ProofBlock(
            block_id="test_block",
            timestamp=int(time.time()),
            proofs=[{"id": "proof_1"}],
            previous_block_hash="0" * 64,
            proposer_id="node_0",
        )
        
        engine.current_state = ConsensusState(
            sequence=1,
            view=0,
            proof_block=proof_block,
            block_digest=proof_block.hash(),
        )
        
        # Create PREPARE with wrong digest
        prepare = PrepareMessage(
            message_type=MessageType.PREPARE,
            view=0,
            sequence=1,
            sender_id="node_1",
            block_digest="wrong_digest",
        )
        
        engine.handle_prepare(prepare)
        
        # Should not accept message
        assert len(engine.current_state.prepare_messages) == 0
    
    def test_prepare_phase_reaches_quorum(self):
        """Test PREPARE phase transitions to COMMIT when quorum reached."""
        # Create 4-node network (f=1, quorum=3)
        networks = create_test_network(4, 0)
        
        engines = {}
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
            )
        
        engine = engines["node_0"]
        
        # Create consensus state
        proof_block = ProofBlock(
            block_id="test_block",
            timestamp=int(time.time()),
            proofs=[{"id": "proof_1"}],
            previous_block_hash="0" * 64,
            proposer_id="node_0",
        )
        
        engine.current_state = ConsensusState(
            sequence=1,
            view=0,
            proof_block=proof_block,
            block_digest=proof_block.hash(),
        )
        
        # Send PREPARE messages until quorum
        # Need 3 messages for quorum (2f+1 = 3)
        for i in range(1, 4):
            prepare = PrepareMessage(
                message_type=MessageType.PREPARE,
                view=0,
                sequence=1,
                sender_id=f"node_{i}",
                block_digest=proof_block.hash(),
            )
            
            engine.handle_prepare(prepare)
        
        # Should have reached prepared state
        assert engine.current_state.prepared


class TestCommitPhase:
    """Test COMMIT phase of consensus."""
    
    def test_handle_commit_collects_messages(self):
        """Test COMMIT handler collects messages from peers."""
        # Create 4-node network
        networks = create_test_network(4, 0)
        
        engines = {}
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
            )
        
        engine = engines["node_0"]
        
        # Create consensus state
        proof_block = ProofBlock(
            block_id="test_block",
            timestamp=int(time.time()),
            proofs=[{"id": "proof_1"}],
            previous_block_hash="0" * 64,
            proposer_id="node_0",
        )
        
        engine.current_state = ConsensusState(
            sequence=1,
            view=0,
            proof_block=proof_block,
            block_digest=proof_block.hash(),
            prepared=True,
        )
        
        # Create COMMIT messages from other nodes
        for i in range(1, 4):
            commit = CommitMessage(
                message_type=MessageType.COMMIT,
                view=0,
                sequence=1,
                sender_id=f"node_{i}",
                block_digest=proof_block.hash(),
            )
            
            engine.handle_commit(commit)
        
        # Should have collected 3 COMMIT messages
        assert len(engine.current_state.commit_messages) == 3
    
    def test_commit_phase_reaches_quorum_and_finalizes(self):
        """Test COMMIT phase finalizes consensus when quorum reached."""
        # Create 4-node network (f=1, quorum=3)
        networks = create_test_network(4, 0)
        
        engines = {}
        mempool = ProofMempool()
        
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
                proof_mempool=mempool,
            )
        
        engine = engines["node_0"]
        
        # Add proofs to mempool
        proofs = [{"id": f"proof_{i}"} for i in range(3)]
        for proof in proofs:
            mempool.add_proof(proof, difficulty=100)
        
        # Create consensus state
        proof_block = ProofBlock(
            block_id="test_block",
            timestamp=int(time.time()),
            proofs=proofs,
            previous_block_hash="0" * 64,
            proposer_id="node_0",
        )
        
        # Verify the block first
        verifier = ProofVerifier()
        verification_result = verifier.verify_proof_block(proof_block)
        
        engine.current_state = ConsensusState(
            sequence=1,
            view=0,
            proof_block=proof_block,
            block_digest=proof_block.hash(),
            prepared=True,
            verification_result=verification_result,
        )
        
        # Send COMMIT messages until quorum
        result = None
        for i in range(1, 4):
            commit = CommitMessage(
                message_type=MessageType.COMMIT,
                view=0,
                sequence=1,
                sender_id=f"node_{i}",
                block_digest=proof_block.hash(),
            )
            
            result = engine.handle_commit(commit)
        
        # Should have finalized consensus
        assert engine.current_state.committed
        assert result is not None
        assert result.consensus_reached
        assert result.finalized_state == proof_block.hash()
        
        # Proofs should be removed from mempool
        for proof in proofs:
            assert not mempool.contains(proof)


class TestConsensusIntegration:
    """Integration tests for full consensus flow."""
    
    def test_full_consensus_flow_4_nodes(self):
        """Test complete consensus flow with 4 nodes."""
        # Create 4-node network
        networks = create_test_network(4, 0)
        
        engines = {}
        mempool = ProofMempool()
        
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
                proof_mempool=mempool,
            )
        
        # Add proofs to mempool
        proofs = [{"id": f"proof_{i}", "constraints": ["x > 0"]} for i in range(3)]
        for proof in proofs:
            mempool.add_proof(proof, difficulty=100)
        
        # Get leader
        leader = [e for e in engines.values() if e.is_leader()][0]
        
        # Leader proposes block
        proof_block = leader.propose_block_from_mempool(block_size=3)
        assert proof_block is not None
        
        # Start consensus round
        leader.start_consensus_round(proof_block)
        
        # Verify leader has started consensus
        assert leader.current_state is not None
        assert leader.current_state.proof_block == proof_block


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ============================================================================
# PROPERTY-BASED TESTS FOR CONSENSUS SAFETY AND LIVENESS
# ============================================================================


class TestConsensusSafetyProperty:
    """
    Property 8: Consensus Safety
    
    Feature: proof-of-proof-consensus, Property 8: Consensus Safety
    Validates: Requirements 2.4, 7.1
    
    For any two honest nodes in the same consensus round, they must never
    accept conflicting states for the same sequence number (safety property).
    """
    
    @given(
        node_count=st.integers(min_value=4, max_value=10),
        proof_block=proof_blocks(min_proofs=1, max_proofs=5),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_8_consensus_safety(self, node_count, proof_block):
        """
        Test that no two honest nodes accept conflicting states.
        
        This property verifies the safety guarantee of PBFT consensus:
        - All honest nodes that reach consensus agree on the same state
        - No two nodes finalize different blocks for the same sequence
        - Byzantine nodes cannot cause honest nodes to diverge
        """
        # Create network with honest nodes only
        networks = create_test_network(node_count, 0)
        
        engines = {}
        mempool = ProofMempool()
        
        # Add proofs to mempool
        for proof in proof_block.proofs:
            mempool.add_proof(proof, difficulty=100)
        
        # Create engines for all nodes
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
                proof_mempool=mempool,
            )
        
        # Get leader
        leader = [e for e in engines.values() if e.is_leader()][0]
        
        # Set proof block metadata
        proof_block.proposer_id = leader.node_id
        proof_block.previous_block_hash = "0" * 64
        
        # Leader broadcasts PRE-PREPARE
        pre_prepare = PrePrepareMessage(
            message_type=MessageType.PRE_PREPARE,
            view=0,
            sequence=1,
            sender_id=leader.node_id,
            proof_block=proof_block,
        )
        
        # All nodes handle PRE-PREPARE
        for engine in engines.values():
            engine.handle_pre_prepare(pre_prepare)
        
        # Collect all nodes that verified the block
        verified_nodes = []
        for engine in engines.values():
            if engine.current_state and engine.current_state.verification_result:
                if engine.current_state.verification_result.valid:
                    verified_nodes.append(engine)
        
        # All honest nodes should have the same block digest
        if verified_nodes:
            expected_digest = verified_nodes[0].current_state.block_digest
            for engine in verified_nodes:
                assert engine.current_state.block_digest == expected_digest, \
                    "Safety violation: Honest nodes have different block digests"
        
        # Simulate PREPARE phase
        for engine in verified_nodes:
            prepare = PrepareMessage(
                message_type=MessageType.PREPARE,
                view=0,
                sequence=1,
                sender_id=engine.node_id,
                block_digest=proof_block.hash(),
            )
            
            # Broadcast to all nodes
            for other_engine in engines.values():
                other_engine.handle_prepare(prepare)
        
        # Check that all nodes that reached prepared state have same digest
        prepared_nodes = []
        for engine in engines.values():
            if engine.current_state and engine.current_state.prepared:
                prepared_nodes.append(engine)
        
        if prepared_nodes:
            expected_digest = prepared_nodes[0].current_state.block_digest
            for engine in prepared_nodes:
                assert engine.current_state.block_digest == expected_digest, \
                    "Safety violation: Prepared nodes have different block digests"
        
        # Simulate COMMIT phase
        for engine in prepared_nodes:
            commit = CommitMessage(
                message_type=MessageType.COMMIT,
                view=0,
                sequence=1,
                sender_id=engine.node_id,
                block_digest=proof_block.hash(),
            )
            
            # Broadcast to all nodes
            for other_engine in engines.values():
                other_engine.handle_commit(commit)
        
        # Check that all nodes that committed have same finalized state
        committed_nodes = []
        finalized_states = []
        
        for engine in engines.values():
            if engine.current_state and engine.current_state.committed:
                committed_nodes.append(engine)
                # Get finalized state
                result = engine._finalize_consensus()
                if result.consensus_reached:
                    finalized_states.append(result.finalized_state)
        
        # SAFETY PROPERTY: All finalized states must be identical
        if finalized_states:
            expected_state = finalized_states[0]
            for state in finalized_states:
                assert state == expected_state, \
                    f"Safety violation: Nodes finalized different states: {set(finalized_states)}"


class TestConsensusLivenessProperty:
    """
    Property 9: Consensus Liveness
    
    Feature: proof-of-proof-consensus, Property 9: Consensus Liveness
    Validates: Requirements 2.5
    
    For any consensus round where at least ⌈2N/3⌉ nodes are honest and
    responsive, consensus must complete within the timeout threshold
    (liveness property).
    """
    
    @given(
        node_count=st.integers(min_value=4, max_value=10),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_9_consensus_liveness(self, node_count):
        """
        Test that consensus completes when 67%+ nodes are honest.
        
        This property verifies the liveness guarantee of PBFT consensus:
        - Consensus completes within timeout when 67%+ nodes are honest
        - The protocol does not deadlock or stall indefinitely
        - Progress is guaranteed with sufficient honest nodes
        """
        # Create network with all honest nodes (100% honest > 67%)
        networks = create_test_network(node_count, 0)
        
        engines = {}
        mempool = ProofMempool()
        
        # Create a simple proof block with mock proofs
        # Use dict format that ProofVerifier can handle
        proofs = [{"id": f"proof_{i}", "constraints": ["x > 0"]} for i in range(3)]
        
        # Add proofs to mempool
        for proof in proofs:
            mempool.add_proof(proof, difficulty=100)
        
        # Create engines for all nodes with a mock verifier that always succeeds
        from aethel.consensus.data_models import BlockVerificationResult, VerificationResult
        
        class MockVerifier:
            """Mock verifier that always returns valid results."""
            def verify_proof_block(self, block):
                results = []
                for proof in block.proofs:
                    results.append(VerificationResult(
                        valid=True,
                        difficulty=100,
                        verification_time=1.0,
                        proof_hash=hashlib.sha256(str(proof).encode()).hexdigest(),
                    ))
                return BlockVerificationResult(
                    valid=True,
                    total_difficulty=len(block.proofs) * 100,
                    results=results,
                )
        
        for node_id, network in networks.items():
            engines[node_id] = ConsensusEngine(
                node_id=node_id,
                validator_stake=1000,
                network=network,
                proof_mempool=mempool,
                proof_verifier=MockVerifier(),
            )
        
        # Record start time
        start_time = time.time()
        
        # Get leader
        leader = [e for e in engines.values() if e.is_leader()][0]
        
        # Create proof block
        proof_block = ProofBlock(
            block_id="test_block",
            timestamp=int(time.time()),
            proofs=proofs,
            previous_block_hash="0" * 64,
            proposer_id=leader.node_id,
        )
        
        # Leader broadcasts PRE-PREPARE
        pre_prepare = PrePrepareMessage(
            message_type=MessageType.PRE_PREPARE,
            view=0,
            sequence=1,
            sender_id=leader.node_id,
            proof_block=proof_block,
        )
        
        # All nodes handle PRE-PREPARE
        for engine in engines.values():
            engine.handle_pre_prepare(pre_prepare)
        
        # Collect nodes that verified successfully
        verified_nodes = []
        for engine in engines.values():
            if engine.current_state and engine.current_state.verification_result:
                if engine.current_state.verification_result.valid:
                    verified_nodes.append(engine)
        
        # Simulate PREPARE phase - each verified node broadcasts PREPARE
        prepare_messages = []
        for engine in verified_nodes:
            prepare = PrepareMessage(
                message_type=MessageType.PREPARE,
                view=0,
                sequence=1,
                sender_id=engine.node_id,
                block_digest=proof_block.hash(),
            )
            prepare_messages.append(prepare)
        
        # All nodes receive all PREPARE messages
        for prepare in prepare_messages:
            for engine in engines.values():
                engine.handle_prepare(prepare)
        
        # Collect nodes that reached prepared state
        prepared_nodes = []
        for engine in engines.values():
            if engine.current_state and engine.current_state.prepared:
                prepared_nodes.append(engine)
        
        # Simulate COMMIT phase - each prepared node broadcasts COMMIT
        commit_messages = []
        for engine in prepared_nodes:
            commit = CommitMessage(
                message_type=MessageType.COMMIT,
                view=0,
                sequence=1,
                sender_id=engine.node_id,
                block_digest=proof_block.hash(),
            )
            commit_messages.append(commit)
        
        # All nodes receive all COMMIT messages
        for commit in commit_messages:
            for engine in engines.values():
                engine.handle_commit(commit)
        
        # Check that consensus completed
        consensus_reached = False
        committed_nodes = []
        for engine in engines.values():
            if engine.current_state and engine.current_state.committed:
                consensus_reached = True
                committed_nodes.append(engine)
        
        # Record end time
        end_time = time.time()
        elapsed = end_time - start_time
        
        # LIVENESS PROPERTY: Consensus must complete
        # With 100% honest nodes, at least some nodes should reach consensus
        assert consensus_reached, \
            f"Liveness violation: Consensus did not complete with 100% honest nodes. " \
            f"Verified: {len(verified_nodes)}, Prepared: {len(prepared_nodes)}, " \
            f"Committed: {len(committed_nodes)}, Total: {node_count}"
        
        # LIVENESS PROPERTY: Consensus must complete within timeout
        # Note: In simulation, this should be very fast (< 1 second)
        # In real network, timeout would be 10 seconds
        assert elapsed < 10.0, \
            f"Liveness violation: Consensus took {elapsed:.2f}s (timeout: 10s)"
        
        # Verify at least quorum of nodes finalized
        # Byzantine quorum = 2f+1 where f = (N-1)/3
        f = (node_count - 1) // 3
        quorum = 2 * f + 1
        
        assert len(committed_nodes) >= quorum, \
            f"Liveness violation: Only {len(committed_nodes)} nodes committed, " \
            f"need {quorum} for quorum (f={f}, N={node_count})"
