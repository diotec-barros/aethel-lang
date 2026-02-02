"""
Generate Certificates for Existing Functions
Retroactively creates proof certificates for functions already in the vault
"""

from aethel_vault_distributed import AethelDistributedVault
from pathlib import Path

def generate_missing_certificates():
    """Generate certificates for all functions that don't have one"""
    
    vault = AethelDistributedVault()
    
    print("="*70)
    print("GENERATING MISSING CERTIFICATES")
    print("="*70)
    
    generated = 0
    skipped = 0
    
    for function_hash, info in vault.index.items():
        cert_path = vault.certificates_path / f"{function_hash}.cert.json"
        
        if cert_path.exists():
            print(f"\n[SKIP] {info['intent_name']}")
            print(f"  Certificate already exists")
            skipped += 1
            continue
        
        print(f"\n[GENERATE] {info['intent_name']}")
        print(f"  Hash: {function_hash[:16]}...{function_hash[-8:]}")
        
        # Fetch function entry
        entry = vault.fetch(function_hash)
        if not entry:
            print(f"  ERROR: Function not found in vault")
            continue
        
        # Generate certificate
        verification_result = entry['verification']
        metadata = entry.get('metadata', {})
        
        certificate = vault.generate_proof_certificate(
            function_hash,
            verification_result,
            metadata=metadata
        )
        
        print(f"  Status: {certificate['status']}")
        print(f"  Certificate saved")
        generated += 1
    
    print("\n" + "="*70)
    print(f"SUMMARY:")
    print(f"  Generated: {generated}")
    print(f"  Skipped: {skipped}")
    print(f"  Total: {generated + skipped}")
    print("="*70)


if __name__ == "__main__":
    generate_missing_certificates()
