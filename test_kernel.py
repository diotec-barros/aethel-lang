from aethel_kernel import AethelKernel


# Código Aethel de exemplo
aethel_code = """
intent transfer_funds(sender: Account, receiver: Account, amount: Gold) {
    guard {
        sender_balance >= amount;
        amount > 0;
    }
    solve {
        priority: speed;
        target: blockchain;
    }
    verify {
        sender_balance < old_balance;
    }
}
"""

print("╔══════════════════════════════════════════════════════════════╗")
print("║     AETHEL KERNEL v0.4 - COMPILADOR DE CONFIANÇA ZERO       ║")
print("╚══════════════════════════════════════════════════════════════╝\n")

# Criar o kernel (pode escolher: "anthropic", "openai", ou "ollama")
kernel = AethelKernel(ai_provider="anthropic")

# Compilar com ciclo de autocorreção
result = kernel.compile(
    aethel_code,
    intent_name="transfer_funds",
    max_attempts=3,
    output_file="output/transfer_funds.rs"
)

print("\n" + "="*70)
print("📊 RESULTADO DA COMPILAÇÃO")
print("="*70)
print(f"Status: {result['status']}")
print(f"Tentativas: {result['attempts']}")

if result['status'] == 'SUCCESS':
    print("\n" + result['report'])
    
    print("\n" + "="*70)
    print("🦀 CÓDIGO RUST GERADO:")
    print("="*70)
    print(result['generated_code'])
elif result['status'] == 'LOGIC_ERROR':
    print("\n❌ ERRO LÓGICO NAS CONSTRAINTS")
    print(result['report'])
else:
    print(f"\n❌ {result['message']}")

print("\n" + "="*70)
print("📈 HISTÓRICO DE VERIFICAÇÕES:")
print("="*70)
for h in result['verification_history']:
    print(f"  Tentativa {h['attempt']}: {h['result']['status']}")
