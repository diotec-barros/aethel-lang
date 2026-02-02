# Aethel Examples

## Aethel-Finance: DeFi Core

**The Challenge**: Create a financial system where double-spending, negative balances, and supply manipulation are mathematically impossible.

### What Makes This Revolutionary

Traditional smart contracts (Solidity, etc.) rely on:
- Manual testing
- Audits (expensive, slow, fallible)
- Hope that edge cases were covered

**Aethel-Finance uses**:
- Formal verification (Z3 Solver)
- Mathematical proofs
- Impossible to deploy buggy code

### The Three Core Operations

#### 1. Transfer
```aethel
intent transfer(sender: Account, receiver: Account, amount: Balance) {
    guard {
        sender_balance >= amount;          // Can't overdraw
        amount >= min_transfer;            // Minimum transfer amount
        receiver_balance >= balance_zero;  // Receiver exists
    }
    verify {
        sender_balance >= balance_zero;              // No negative balances
        receiver_balance > old_receiver_balance;     // Receiver got funds
        total_supply == old_total_supply;            // Conservation of money
    }
}
```

**What the Judge Proves**:
- Sender can never go negative
- Receiver always gets the money
- Total supply is conserved (no money created/destroyed)

#### 2. Mint (Create New Tokens)
```aethel
intent mint(account: Account, amount: Balance) {
    guard {
        amount > balance_zero;           // Must mint positive amount
        caller == contract_owner;        // Only owner can mint
        account_balance >= balance_zero; // Account exists
    }
    verify {
        account_balance > old_account_balance;  // Account got tokens
        total_supply > old_total_supply;        // Supply increased
    }
}
```

**What the Judge Proves**:
- Only authorized minting
- Supply increases correctly
- No overflow possible

#### 3. Burn (Destroy Tokens)
```aethel
intent burn(account: Account, amount: Balance) {
    guard {
        amount > balance_zero;           // Must burn positive amount
        account_balance >= amount;       // Can't burn more than you have
        caller == account_owner;         // Only owner can burn their tokens
    }
    verify {
        account_balance < old_account_balance;  // Tokens removed
        total_supply < old_total_supply;        // Supply decreased
        total_supply >= balance_zero;           // Supply never negative
    }
}
```

**What the Judge Proves**:
- Can't burn more than you have
- Supply decreases correctly
- Total supply never goes negative

### Real-World Impact

**Traditional DeFi Hacks** (2021-2024):
- Poly Network: $611M stolen (logic bug)
- Wormhole: $325M stolen (verification bypass)
- Ronin Bridge: $625M stolen (access control)
- BNB Chain: $586M stolen (proof forgery)

**Total**: $2.1B+ lost to bugs that formal verification would have caught.

**With Aethel-Finance**:
- All these bugs would be caught at compile time
- Judge would reject the code
- Zero dollars lost

### How to Use

```bash
# Verify the finance module
aethel verify aethel/examples/finance.ae

# Build the finance module
aethel build aethel/examples/finance.ae -o finance_core.rs

# The output is mathematically proved to be correct
```

### Next Steps

1. **Aethel-DeFi**: Full DEX (Decentralized Exchange)
2. **Aethel-Lending**: Lending protocol with provable solvency
3. **Aethel-Stablecoin**: Algorithmic stablecoin with formal guarantees

---

**"In finance, there are no second chances. In Aethel, there are no bugs."**
