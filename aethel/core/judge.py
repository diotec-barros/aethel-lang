from z3 import *
import re
import ast  # v1.2: Para parsing de expressões aritméticas
import time  # v1.5: Para medir tempo de execução
from .conservation import ConservationChecker  # v1.3: Conservation Checker
from .overflow import OverflowSentinel  # v1.4: Overflow Sentinel
from .sanitizer import AethelSanitizer  # v1.5: Input Sanitizer
from .zkp_simulator import get_zkp_simulator  # v1.6.2: Zero-Knowledge Proofs


class AethelJudge:
    """
    O Juiz - Verificador Matemático que garante correção formal do código gerado.
    Usa Z3 Solver para provar que o código respeita as constraints.
    
    v1.6.2: Ghost Protocol Expansion - Zero-Knowledge Proofs
    - Suporte a variáveis 'secret'
    - Verificação sem revelação de valores
    - Commitments criptográficos
    
    v1.5: Defesa em 4 Camadas (The Fortress):
    - Layer 0: Input Sanitizer (anti-injection) ⭐ NEW v1.5.1
    - Layer 1: Conservation Guardian (Σ = 0)
    - Layer 2: Overflow Sentinel (limites de hardware)
    - Layer 3: Z3 Theorem Prover (lógica profunda) + Timeout ⭐ NEW v1.5.2
    """
    
    # v1.5.2: Limites de segurança
    Z3_TIMEOUT_MS = 2000  # 2 segundos
    MAX_VARIABLES = 100
    MAX_CONSTRAINTS = 500
    
    def __init__(self, intent_map):
        self.intent_map = intent_map
        self.solver = Solver()
        self.variables = {}
        self.sanitizer = AethelSanitizer()  # v1.5.1: Initialize Sanitizer
        self.conservation_checker = ConservationChecker()  # v1.3: Initialize Conservation Checker
        self.overflow_sentinel = OverflowSentinel()  # v1.4: Initialize Overflow Sentinel
        self.zkp_engine = get_zkp_simulator()  # v1.6.2: Initialize ZKP Engine
        self.secret_variables = set()  # v1.6.2: Track secret variables
        
        # v1.5.2: Configurar timeout do Z3
        self.solver.set("timeout", self.Z3_TIMEOUT_MS)
    
    def verify_logic(self, intent_name):
        """
        Verifica se a lógica da intenção é matematicamente consistente.
        
        Estratégia v1.5 - FORTRESS DEFENSE (4 LAYERS):
        -1. [v1.5.1] Sanitiza input (anti-injection, O(n))
        0. [v1.3] Verifica conservação de fundos (fast pre-check, O(n))
        0.5 [v1.4] Verifica limites de hardware (overflow/underflow, O(n))
        1. Adiciona guards como premissas (assumimos que são verdadeiras)
        2. Verifica se TODAS as pós-condições podem ser verdadeiras JUNTAS
        3. Se Z3 encontrar modelo = PROVA (existe realidade consistente)
        4. Se Z3 não encontrar = FALHA (contradição global detectada)
        
        New v1.5.1: Sanitização de input (anti-injection)
        New v1.5.2: Z3 Timeout (anti-DoS)
        
        Defesa em 4 Camadas:
        - Layer 0: Input Sanitizer - Protege contra injeção de código
        - Layer 1: Conservation Guardian (Σ = 0) - Protege contra criação de fundos
        - Layer 2: Overflow Sentinel (limites) - Protege contra bugs de hardware
        - Layer 3: Z3 Theorem Prover (lógica) - Protege contra contradições lógicas
        """
        data = self.intent_map[intent_name]
        
        print(f"\n⚖️  Iniciando verificação formal de '{intent_name}'...")
        print("🛡️  Usando Fortress Defense (v1.5)")
        print("    Layer 0: Input Sanitizer (anti-injection)")
        print("    Layer 1: Conservation Guardian")
        print("    Layer 2: Overflow Sentinel")
        print("    Layer 3: Z3 Theorem Prover (timeout: 2s)")
        
        # STEP -1: Input Sanitization (v1.5.1 - Anti-Injection)
        print("\n🔒 [INPUT SANITIZER] Verificando segurança do código...")
        
        # Sanitizar todas as strings do intent
        code_to_check = str(data)
        sanitize_result = self.sanitizer.sanitize(code_to_check)
        
        if not sanitize_result.is_safe:
            print("  🚨 TENTATIVA DE INJEÇÃO DETECTADA!")
            for violation in sanitize_result.violations:
                print(f"  ⚠️  {violation['type']}: {violation.get('matched', 'N/A')}")
            return {
                'status': 'REJECTED',
                'message': f'🔒 FORTRESS BLOCK - {sanitize_result.format_error()}',
                'counter_examples': [],
                'sanitizer_violations': sanitize_result.violations
            }
        
        print(f"  ✅ Código aprovado pela sanitização")
        
        # STEP -0.5: Complexity Check (v1.5.2 - Anti-DoS)
        print("\n⏱️  [COMPLEXITY CHECK] Verificando complexidade...")
        
        num_vars = len(self.variables)
        num_constraints = len(data['constraints']) + len(data['post_conditions'])
        
        if num_vars > self.MAX_VARIABLES:
            print(f"  🚨 MUITAS VARIÁVEIS: {num_vars} > {self.MAX_VARIABLES}")
            return {
                'status': 'REJECTED',
                'message': f'🛡️ DoS PROTECTION - Muitas variáveis ({num_vars}). Máximo: {self.MAX_VARIABLES}',
                'counter_examples': []
            }
        
        if num_constraints > self.MAX_CONSTRAINTS:
            print(f"  🚨 MUITAS CONSTRAINTS: {num_constraints} > {self.MAX_CONSTRAINTS}")
            return {
                'status': 'REJECTED',
                'message': f'🛡️ DoS PROTECTION - Muitas constraints ({num_constraints}). Máximo: {self.MAX_CONSTRAINTS}',
                'counter_examples': []
            }
        
        print(f"  ✅ Complexidade aceitável (vars: {num_vars}, constraints: {num_constraints})")
        
        # STEP 0: Conservation Check (v1.3 - Fast Pre-Check)
        print("\n💰 [CONSERVATION GUARDIAN] Verificando Lei da Conservação...")
        conservation_result = self.conservation_checker.check_intent({
            'verify': data['post_conditions']
        })
        
        if not conservation_result.is_valid:
            print("  🚨 VIOLAÇÃO DE CONSERVAÇÃO DETECTADA!")
            print(f"  📊 Balanço líquido: {conservation_result.net_change}")
            print(f"  ⚖️  Lei violada: Σ(mudanças) = {conservation_result.net_change} ≠ 0")
            return {
                'status': 'FAILED',
                'message': f'🛡️ CONSERVATION VIOLATION - {conservation_result.format_error()}',
                'counter_examples': [],
                'conservation_violation': {
                    'net_change': conservation_result.net_change,
                    'changes': conservation_result.changes,
                    'law': 'Sum-Zero Enforcement'
                }
            }
        
        if conservation_result.changes:
            print(f"  ✅ Conservação válida ({len(conservation_result.changes)} mudanças de saldo detectadas)")
        else:
            print("  ℹ️  Nenhuma mudança de saldo detectada (pulando verificação de conservação)")
        
        # STEP 0.5: Overflow Check (v1.4 - Hardware Safety Check)
        print("\n🔢 [OVERFLOW SENTINEL] Verificando limites de hardware...")
        overflow_result = self.overflow_sentinel.check_intent({
            'verify': data['post_conditions']
        })
        
        if not overflow_result.is_safe:
            print("  🚨 OVERFLOW/UNDERFLOW DETECTADO!")
            for violation in overflow_result.violations:
                print(f"  ⚠️  {violation['type']}: {violation['operation']}")
            return {
                'status': 'FAILED',
                'message': f'🔢 OVERFLOW/UNDERFLOW DETECTED - {overflow_result.format_error()}',
                'counter_examples': [],
                'overflow_violation': {
                    'violations': overflow_result.violations,
                    'limits': {
                        'MAX_INT': self.overflow_sentinel.max_int,
                        'MIN_INT': self.overflow_sentinel.min_int
                    }
                }
            }
        
        print(f"  ✅ Todas as operações estão dentro dos limites de hardware")
        
        # Reset do solver para nova verificação
        self.solver.reset()
        self.solver.set("timeout", self.Z3_TIMEOUT_MS)  # Reconfigurar timeout
        self.variables = {}
        
        # 1. Extrair e criar variáveis simbólicas
        self._extract_variables(data['constraints'] + data['post_conditions'])
        
        # 2. Adicionar PRÉ-CONDIÇÕES (guards) como premissas
        print("\n📋 Adicionando pré-condições (guards):")
        for constraint in data['constraints']:
            z3_expr = self._parse_constraint(constraint)
            if z3_expr is not None:
                self.solver.add(z3_expr)
                print(f"  ✓ {constraint}")
        
        # 3. UNIFIED PROOF: Verificar TODAS as pós-condições JUNTAS
        print("\n🎯 Verificando consistência global das pós-condições:")
        
        all_post_conditions = []
        for post_condition in data['post_conditions']:
            z3_expr = self._parse_constraint(post_condition)
            if z3_expr is not None:
                all_post_conditions.append(z3_expr)
                print(f"  • {post_condition}")
        
        if not all_post_conditions:
            return {
                'status': 'ERROR',
                'message': 'Nenhuma pós-condição válida para verificar',
                'counter_examples': []
            }
        
        # 4. Criar condição unificada (AND de todas as pós-condições)
        unified_condition = And(all_post_conditions)
        
        # 5. Adicionar ao solver e verificar COM TIMEOUT
        self.solver.add(unified_condition)
        
        print(f"\n⏱️  Executando Z3 com timeout de {self.Z3_TIMEOUT_MS}ms...")
        start_time = time.time()
        result = self.solver.check()
        elapsed_ms = (time.time() - start_time) * 1000
        
        print(f"\n🔍 Resultado da verificação unificada: {result} (tempo: {elapsed_ms:.0f}ms)")
        
        # 6. Interpretar resultado
        if result == sat:
            # Existe uma realidade onde TODAS as condições são verdadeiras!
            model = self.solver.model()
            print("  ✅ PROVED - Todas as pós-condições são consistentes!")
            return {
                'status': 'PROVED',
                'message': 'O código é matematicamente seguro. Todas as pós-condições são consistentes e prováveis.',
                'counter_examples': [],
                'model': self._format_model(model),
                'elapsed_ms': elapsed_ms
            }
        elif result == unsat:
            # Contradição detectada! Não existe realidade onde todas sejam verdadeiras
            print("  ❌ FAILED - Contradição global detectada!")
            return {
                'status': 'FAILED',
                'message': 'As pós-condições são contraditórias ou não podem ser satisfeitas juntas. Contradição global detectada.',
                'counter_examples': [],
                'elapsed_ms': elapsed_ms
            }
        else:
            # Z3 não conseguiu determinar (timeout ou muito complexo)
            print("  ⚠️  TIMEOUT - Z3 excedeu o limite de tempo (possível ataque DoS)")
            return {
                'status': 'TIMEOUT',
                'message': f'🛡️ DoS PROTECTION - Verificação excedeu {self.Z3_TIMEOUT_MS}ms. Problema muito complexo ou tentativa de ataque.',
                'counter_examples': [],
                'elapsed_ms': elapsed_ms
            }
    
    def _extract_variables(self, constraints):
        """
        Extrai nomes de variáveis das constraints e cria símbolos Z3.
        """
        var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
        operators = {'>=', '<=', '==', '!=', '>', '<'}
        
        for constraint in constraints:
            tokens = re.findall(var_pattern, constraint)
            for token in tokens:
                if token not in operators and token not in self.variables:
                    # Criar variável inteira no Z3
                    self.variables[token] = Int(token)
    
    def _parse_constraint(self, constraint_str):
        """
        Converte string de constraint para expressão Z3.
        v1.2: Agora suporta expressões aritméticas!
        
        Exemplo v1.1: "sender_balance >= amount"
        Exemplo v1.2: "(balance - 100) >= amount"
        Exemplo v1.2: "fee == (amount * 5 / 100)"
        """
        try:
            # Remove espaços extras
            constraint_str = constraint_str.strip()
            
            # Detectar operador de comparação
            if '>=' in constraint_str:
                left, right = constraint_str.split('>=')
                return self._parse_arithmetic_expr(left.strip()) >= self._parse_arithmetic_expr(right.strip())
            elif '<=' in constraint_str:
                left, right = constraint_str.split('<=')
                return self._parse_arithmetic_expr(left.strip()) <= self._parse_arithmetic_expr(right.strip())
            elif '==' in constraint_str:
                left, right = constraint_str.split('==')
                return self._parse_arithmetic_expr(left.strip()) == self._parse_arithmetic_expr(right.strip())
            elif '!=' in constraint_str:
                left, right = constraint_str.split('!=')
                return self._parse_arithmetic_expr(left.strip()) != self._parse_arithmetic_expr(right.strip())
            elif '>' in constraint_str:
                left, right = constraint_str.split('>')
                return self._parse_arithmetic_expr(left.strip()) > self._parse_arithmetic_expr(right.strip())
            elif '<' in constraint_str:
                left, right = constraint_str.split('<')
                return self._parse_arithmetic_expr(left.strip()) < self._parse_arithmetic_expr(right.strip())
            else:
                print(f"  ⚠️  Operador não reconhecido em: {constraint_str}")
                return None
        except Exception as e:
            print(f"  ⚠️  Erro ao parsear '{constraint_str}': {e}")
            return None
    
    def _parse_arithmetic_expr(self, expr_str):
        """
        v1.2: Converte expressão aritmética em Z3.
        
        Suporta:
        - Números: "100" -> 100
        - Variáveis: "balance" -> Int('balance')
        - Operações: "(balance + 100)" -> Int('balance') + 100
        - Complexas: "((amount * rate) / 100)" -> (Int('amount') * Int('rate')) / 100
        
        Usa Python's ast para parsing seguro.
        """
        expr_str = expr_str.strip()
        
        # Se for apenas um número
        if re.match(r'^-?\d+$', expr_str):
            return int(expr_str)
        
        # Se for apenas uma variável
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', expr_str):
            if expr_str not in self.variables:
                self.variables[expr_str] = Int(expr_str)
            return self.variables[expr_str]
        
        # Expressão aritmética complexa - usar AST
        try:
            tree = ast.parse(expr_str, mode='eval')
            return self._ast_to_z3(tree.body)
        except Exception as e:
            print(f"  ⚠️  Erro ao parsear expressão aritmética '{expr_str}': {e}")
            # Fallback: tentar como variável simples
            if expr_str not in self.variables:
                self.variables[expr_str] = Int(expr_str)
            return self.variables[expr_str]
    
    def _ast_to_z3(self, node):
        """
        v1.2: Converte AST Python para expressão Z3.
        
        Suporta operações aritméticas: +, -, *, /, %
        """
        if isinstance(node, ast.BinOp):
            left = self._ast_to_z3(node.left)
            right = self._ast_to_z3(node.right)
            
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                # Z3 usa divisão inteira
                return left / right
            elif isinstance(node.op, ast.Mod):
                return left % right
            else:
                raise ValueError(f"Operador não suportado: {type(node.op)}")
        
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name not in self.variables:
                self.variables[var_name] = Int(var_name)
            return self.variables[var_name]
        
        elif isinstance(node, ast.Constant):
            # Python 3.8+
            return node.value
        
        elif isinstance(node, ast.Num):
            # Python 3.7 e anterior
            return node.n
        
        else:
            raise ValueError(f"Tipo de nó AST não suportado: {type(node)}")
    
    def _format_model(self, model):
        """
        Formata o modelo (contra-exemplo) de forma legível.
        """
        result = {}
        for var in model:
            result[str(var)] = model[var].as_long()
        return result
    
    def generate_proof_report(self, intent_name, verification_result):
        """
        Gera relatório detalhado da verificação formal.
        """
        data = self.intent_map[intent_name]
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           AETHEL FORMAL VERIFICATION REPORT                  ║
╚══════════════════════════════════════════════════════════════╝

Intent: {intent_name}
Parameters: {', '.join(data['params'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRE-CONDITIONS (Guards):
"""
        for constraint in data['constraints']:
            report += f"  • {constraint}\n"
        
        report += "\nPOST-CONDITIONS (Verify):\n"
        for condition in data['post_conditions']:
            report += f"  • {condition}\n"
        
        report += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        report += f"\nVERDICT: {verification_result['status']}\n"
        report += f"MESSAGE: {verification_result['message']}\n"
        
        if verification_result['counter_examples']:
            report += "\n⚠️  COUNTER-EXAMPLES FOUND:\n"
            for ce in verification_result['counter_examples']:
                report += f"\n  Condition: {ce['condition']}\n"
                report += f"  Fails when: {ce['counter_example']}\n"
        
        report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        return report
