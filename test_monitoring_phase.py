"""Run monitoring tests in phases"""
import subprocess
import sys

tests = [
    ("Property 32: Consensus Metrics", "test_property_32_consensus_metrics_emission"),
    ("Property 33: Mempool Metrics", "test_property_33_real_time_mempool_metrics"),
    ("Property 34: Low Accuracy Alert", "test_property_34_low_accuracy_alerting_simple"),
    ("Property 35: Reward Tracking", "test_property_35_reward_tracking_accuracy"),
    ("Property 36: Byzantine Logging", "test_property_36_byzantine_behavior_logging"),
    ("Integration Test", "test_metrics_integration_full_consensus_flow"),
    ("Prometheus Export", "test_prometheus_metrics_export"),
]

passed = 0
failed = 0

for name, test_func in tests:
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print('='*60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         f"test_properties_monitoring.py::{test_func}",
         "-v", "--tb=short", "--timeout=30"],
        capture_output=False,
        timeout=45
    )
    
    if result.returncode == 0:
        print(f"✓ {name} PASSED")
        passed += 1
    else:
        print(f"✗ {name} FAILED")
        failed += 1

print(f"\n{'='*60}")
print(f"RESULTS: {passed} passed, {failed} failed")
print('='*60)

sys.exit(0 if failed == 0 else 1)
