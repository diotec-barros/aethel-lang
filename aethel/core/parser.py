from lark import Lark
from aethel.core.grammar import aethel_grammar


class AethelParser:
    def __init__(self):
        self.parser = Lark(aethel_grammar, parser='lalr')
    
    def parse(self, code):
        tree = self.parser.parse(code)
        return self.transform_to_intent_map(tree)
    
    def transform_to_intent_map(self, tree):
        # Aqui convertemos a árvore bruta em um mapa de intenção
        # que a IA e o Verificador podem entender.
        intents = {}
        for intent in tree.children:
            name = intent.children[0].value
            intents[name] = {
                "params": self._get_params(intent.children[1]),
                "constraints": self._get_block(intent.children[2]), # Guard
                "ai_instructions": self._get_settings(intent.children[3]), # Solve
                "post_conditions": self._get_block(intent.children[4]) # Verify
            }
        return intents
    
    def _get_params(self, node):
        """
        v1.6.2: Extrai parâmetros com suporte a 'secret' keyword
        Retorna lista de dicts com: name, type, is_secret
        """
        params = []
        for p in node.children:
            # Verifica se tem 'secret' keyword
            if len(p.children) == 3:  # secret NAME : NAME
                is_secret = True
                param_name = p.children[1].value
                param_type = p.children[2].value
            else:  # NAME : NAME
                is_secret = False
                param_name = p.children[0].value
                param_type = p.children[1].value
            
            params.append({
                "name": param_name,
                "type": param_type,
                "is_secret": is_secret
            })
        
        return params
    
    def _get_block(self, node):
        """
        Extrai as condições lógicas.
        v1.2: Agora suporta expressões aritméticas!
        v1.6.2: Agora suporta 'secret' keyword nas condições!
        """
        conditions = []
        for condition_node in node.children:
            # Verifica se tem 'secret' keyword
            if len(condition_node.children) == 4:  # secret expr OPERATOR expr
                is_secret = True
                left_expr = self._parse_expr(condition_node.children[1])
                operator = condition_node.children[2].value
                right_expr = self._parse_expr(condition_node.children[3])
            else:  # expr OPERATOR expr
                is_secret = False
                left_expr = self._parse_expr(condition_node.children[0])
                operator = condition_node.children[1].value
                right_expr = self._parse_expr(condition_node.children[2])
            
            conditions.append({
                "expression": f"{left_expr} {operator} {right_expr}",
                "is_secret": is_secret,
                "left": left_expr,
                "operator": operator,
                "right": right_expr
            })
        
        return conditions
    
    def _parse_expr(self, expr_node):
        """
        v1.2: Converte árvore de expressão aritmética em string.
        
        Suporta:
        - Números: NUMBER -> "100"
        - Variáveis: NAME -> "balance"
        - Adição: add(left, right) -> "left + right"
        - Subtração: subtract(left, right) -> "left - right"
        - Multiplicação: multiply(left, right) -> "left * right"
        - Divisão: divide(left, right) -> "left / right"
        - Módulo: modulo(left, right) -> "left % right"
        - Parênteses: mantidos na string
        """
        if hasattr(expr_node, 'data'):
            # É um nó de operação
            if expr_node.data == 'add':
                left = self._parse_expr(expr_node.children[0])
                right = self._parse_expr(expr_node.children[1])
                return f"({left} + {right})"
            
            elif expr_node.data == 'subtract':
                left = self._parse_expr(expr_node.children[0])
                right = self._parse_expr(expr_node.children[1])
                return f"({left} - {right})"
            
            elif expr_node.data == 'multiply':
                left = self._parse_expr(expr_node.children[0])
                right = self._parse_expr(expr_node.children[1])
                return f"({left} * {right})"
            
            elif expr_node.data == 'divide':
                left = self._parse_expr(expr_node.children[0])
                right = self._parse_expr(expr_node.children[1])
                return f"({left} / {right})"
            
            elif expr_node.data == 'modulo':
                left = self._parse_expr(expr_node.children[0])
                right = self._parse_expr(expr_node.children[1])
                return f"({left} % {right})"
        
        # É um token (folha da árvore)
        if expr_node.type == 'NUMBER':
            return str(expr_node.value)
        elif expr_node.type == 'NAME':
            return str(expr_node.value)
        
        # Fallback: retornar como string
        return str(expr_node)
    
    def _get_settings(self, node):
        # Extrai as configurações para a IA (ex: priority: security)
        return {s.children[0].value: s.children[1].value for s in node.children}
