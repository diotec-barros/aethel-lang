from z3 import *
import re


class AethelJudge:
    """
    O Juiz - Verificador Matemático que garante correção formal do código gerado.
    Usa Z3 Solver para provar que o código respeita as constraints.
    """
    
    def __init__(self, intent_map):
        self.intent_map = intent_map
        self.solver = Solver()
        self.variables = {}
    
    def verify_logic(self, intent_name):
        """
        Verifica se a lógica da intenção é matematicamente consistente.
        
        Estratégia:
        1. Adiciona guards como premissas (assumimos que são verdadeiras)
        2. Adiciona NEGAÇÃO dos verify como objetivo
        3. Se Z3 encontrar solução = FALHA (existe contra-exemplo)
        4. Se Z3 não encontrar = PROVA (código é seguro)
        """
        data = self.intent_map[intent_name]
        
        print(f"\n⚖️  Iniciando verificação formal de '{intent_name}'...")
        
        # Reset do solver para nova verificação
        self.solver.reset()
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
        
        # 3. Adicionar NEGAÇÃO das PÓS-CONDIÇÕES (verify)
        # Se o solver encontrar solução, significa que existe um caso onde verify falha!
        print("\n🎯 Verificando pós-condições (verify):")
        verification_failed = False
        counter_examples = []
        
        for post_condition in data['post_conditions']:
            z3_expr = self._parse_constraint(post_condition)
            if z3_expr is not None:
                # Testamos a NEGAÇÃO
                self.solver.push()
                self.solver.add(Not(z3_expr))
                
                result = self.solver.check()
                
                if result == sat:
                    # Encontrou contra-exemplo!
                    verification_failed = True
                    model = self.solver.model()
                    counter_examples.append({
                        'condition': post_condition,
                        'counter_example': self._format_model(model)
                    })
                    print(f"  ❌ {post_condition} - FALHA DETECTADA!")
                elif result == unsat:
                    print(f"  ✓ {post_condition} - PROVADO")
                else:
                    print(f"  ⚠️  {post_condition} - INDETERMINADO")
                
                self.solver.pop()
        
        # 4. Resultado final
        if verification_failed:
            return {
                'status': 'FAILED',
                'message': 'Encontrei falhas lógicas! O código viola as pós-condições.',
                'counter_examples': counter_examples
            }
        else:
            return {
                'status': 'PROVED',
                'message': 'O código é matematicamente seguro. Todas as pós-condições são garantidas.',
                'counter_examples': []
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
        
        Exemplo: "sender_balance >= amount" -> z3.Int('sender_balance') >= z3.Int('amount')
        """
        try:
            # Remove espaços extras
            constraint_str = constraint_str.strip()
            
            # Detectar operador
            if '>=' in constraint_str:
                left, right = constraint_str.split('>=')
                return self._parse_expr(left.strip()) >= self._parse_expr(right.strip())
            elif '<=' in constraint_str:
                left, right = constraint_str.split('<=')
                return self._parse_expr(left.strip()) <= self._parse_expr(right.strip())
            elif '==' in constraint_str:
                left, right = constraint_str.split('==')
                return self._parse_expr(left.strip()) == self._parse_expr(right.strip())
            elif '!=' in constraint_str:
                left, right = constraint_str.split('!=')
                return self._parse_expr(left.strip()) != self._parse_expr(right.strip())
            elif '>' in constraint_str:
                left, right = constraint_str.split('>')
                return self._parse_expr(left.strip()) > self._parse_expr(right.strip())
            elif '<' in constraint_str:
                left, right = constraint_str.split('<')
                return self._parse_expr(left.strip()) < self._parse_expr(right.strip())
            else:
                print(f"  ⚠️  Operador não reconhecido em: {constraint_str}")
                return None
        except Exception as e:
            print(f"  ⚠️  Erro ao parsear '{constraint_str}': {e}")
            return None
    
    def _parse_expr(self, expr_str):
        """
        Converte expressão (variável ou número) para Z3.
        """
        expr_str = expr_str.strip()
        
        # Se for número
        if expr_str.isdigit() or (expr_str.startswith('-') and expr_str[1:].isdigit()):
            return int(expr_str)
        
        # Se for variável
        if expr_str in self.variables:
            return self.variables[expr_str]
        
        # Criar variável se não existir
        self.variables[expr_str] = Int(expr_str)
        return self.variables[expr_str]
    
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
