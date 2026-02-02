from aethel_kernel import AethelKernel


# Código Aethel que pode precisar de múltiplas tentativas
aethel_code = """
intent secure_payment(user: Account, merchant: Account, amount: Gold) {
    guard {
        user_balance >= amount;
        amount > 0;
        amount <= 10000;
    }
    solve {
        priority: security;
        target: blockchain;
    }
    verify {
        user_balance < old_user_balance;
        merchant_balance > old_merchant_balance;
    }
}
"""

print("╔══════════════════════════════════════════════════════════════╗")
print("║   AETHEL KERNEL v0.4 - TESTE DE FEEDBACK LOOP AVANÇADO      ║")
print("╚══════════════════════════════════════════════════════════════╝\n")

kernel = AethelKernel(ai_provider="anthropic")

# Usar o método avançado com feedback loop
result = kernel.compile_with_feedback_loop(
    aethel_code,
    intent_name="secure_payment",
    max_attempts=5,
    output_file="output/secure_payment.rs"
)

print("\n" + "="*70)
print("📊 RESULTADO DA COMPILAÇÃO COM FEEDBACK LOOP")
print("="*70)
print(f"Status: {result['status']}")
print(f"Tentativas: {result['attempts']}")

if result['status'] == 'SUCCESS':
    print("\n✅ SUCESSO!")
    print(result['report'])
    
    print("\n" + "="*70)
    print("🦀 CÓDIGO RUST GERADO:")
    print("="*70)
    print(result['generated_code'])
else:
    print(f"\n❌ {result['message']}")

print("\n" + "="*70)
print("📈 HISTÓRICO DE TENTATIVAS:")
print("="*70)
for h in result['verification_history']:
    print(f"\n  Tentativa {h['attempt']}:")
    print(f"    Status: {h['result']['status']}")
    print(f"    Código gerado: {h['code_length']} caracteres")
    if h['result'].get('counter_examples'):
        print(f"    Contra-exemplos: {len(h['result']['counter_examples'])}")
