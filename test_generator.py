from aethel_generator import AethelGenerator


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

# Criar o gerador com verificação formal habilitada
generator = AethelGenerator(ai_provider="anthropic", enable_verification=True)

# Compilar o código Aethel
result = generator.compile(
    aethel_code, 
    intent_name="transfer_funds",
    output_file="output/transfer_funds.rs"
)

if result["status"] == "FAILED":
    print("\n❌ Compilação falhou na verificação formal!")
    print(result["report"])
else:
    print("\n" + "="*60)
    print("📋 RELATÓRIO DE VERIFICAÇÃO:")
    print("="*60)
    if result["report"]:
        print(result["report"])
    
    print("\n" + "="*60)
    print("📋 PROMPT GERADO:")
    print("="*60)
    print(result["prompt"])
    
    print("\n" + "="*60)
    print("🦀 CÓDIGO RUST GERADO:")
    print("="*60)
    print(result["generated_code"])
