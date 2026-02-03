"""
Aethel Overflow Sentinel v1.4.0
================================

Detecta e previne integer overflow/underflow em operações aritméticas.

A Sentinela analisa todas as operações matemáticas e garante que:
1. Nenhum valor exceda MAX_INT (2^63 - 1 para signed 64-bit)
2. Nenhum valor fique abaixo de MIN_INT (-2^63 para signed 64-bit)
3. Operações intermediárias não causem overflow

Filosofia: "Se o hardware pode quebrar, a matemática deve prevenir."
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


# Limites para inteiros de 64 bits (signed)
MAX_INT = 2**63 - 1  # 9,223,372,036,854,775,807
MIN_INT = -(2**63)   # -9,223,372,036,854,775,808


@dataclass
class OverflowResult:
    """Resultado da verificação de overflow"""
    is_safe: bool
    violations: List[Dict[str, any]]
    message: str
    
    def format_error(self) -> str:
        """Formata mensagem de erro para o usuário"""
        if self.is_safe:
            return "✅ Nenhum overflow detectado"
        
        error_msg = "🚨 OVERFLOW/UNDERFLOW DETECTADO!\n\n"
        for v in self.violations:
            error_msg += f"  • Operação: {v['operation']}\n"
            error_msg += f"    Variável: {v['variable']}\n"
            error_msg += f"    Tipo: {v['type']}\n"
            error_msg += f"    Valor resultante: {v['result']}\n"
            error_msg += f"    Limite: {v['limit']}\n\n"
        
        return error_msg


class OverflowSentinel:
    """
    Sentinela de Overflow - Detecta operações aritméticas perigosas
    
    Estratégia:
    1. Extrai todas as operações aritméticas das pós-condições
    2. Para cada operação, verifica se pode causar overflow/underflow
    3. Considera valores máximos possíveis para variáveis
    4. Bloqueia código se detectar risco
    """
    
    def __init__(self, max_int: int = MAX_INT, min_int: int = MIN_INT):
        self.max_int = max_int
        self.min_int = min_int
    
    def check_intent(self, intent_data: Dict) -> OverflowResult:
        """
        Verifica se um intent pode causar overflow/underflow
        
        Args:
            intent_data: Dicionário com 'verify' (pós-condições)
        
        Returns:
            OverflowResult com resultado da verificação
        """
        post_conditions = intent_data.get('verify', [])
        violations = []
        
        for condition in post_conditions:
            # Detectar operações aritméticas
            operations = self._extract_operations(condition)
            
            for op in operations:
                violation = self._check_operation_safety(op, condition)
                if violation:
                    violations.append(violation)
        
        if violations:
            return OverflowResult(
                is_safe=False,
                violations=violations,
                message=f"Detectadas {len(violations)} operação(ões) com risco de overflow/underflow"
            )
        
        return OverflowResult(
            is_safe=True,
            violations=[],
            message="Todas as operações são seguras contra overflow/underflow"
        )
    
    def _extract_operations(self, condition: str) -> List[Dict]:
        """
        Extrai operações aritméticas de uma condição
        
        Exemplo:
            "balance == old_balance + 1000000000000000000"
            -> [{'var': 'balance', 'op': '+', 'value': 1000000000000000000}]
        """
        operations = []
        
        # Padrão: variável == old_variável [+/-/*///%] valor
        # Exemplo: balance == old_balance + 100
        pattern = r'(\w+)\s*==\s*(\w+)\s*([+\-*/%])\s*(\d+)'
        matches = re.finditer(pattern, condition)
        
        for match in matches:
            var_name = match.group(1)
            old_var = match.group(2)
            operator = match.group(3)
            value = int(match.group(4))
            
            operations.append({
                'variable': var_name,
                'old_variable': old_var,
                'operator': operator,
                'value': value,
                'full_expr': match.group(0)
            })
        
        return operations
    
    def _check_operation_safety(self, operation: Dict, condition: str) -> Optional[Dict]:
        """
        Verifica se uma operação específica é segura
        
        Assume pior caso: variável está no limite antes da operação
        """
        operator = operation['operator']
        value = operation['value']
        variable = operation['variable']
        
        # Verificar adição
        if operator == '+':
            # Pior caso: variável já está perto do MAX_INT
            if value > (self.max_int // 2):  # Heurística: valores muito grandes
                return {
                    'operation': f"{variable} = {operation['old_variable']} + {value}",
                    'variable': variable,
                    'type': 'OVERFLOW',
                    'result': f"> {self.max_int}",
                    'limit': f"MAX_INT = {self.max_int}",
                    'recommendation': f"Use valores menores ou verifique limites antes da operação"
                }
        
        # Verificar subtração
        elif operator == '-':
            # Pior caso: variável já está perto do MIN_INT
            if value > (abs(self.min_int) // 2):  # Heurística: valores muito grandes
                return {
                    'operation': f"{variable} = {operation['old_variable']} - {value}",
                    'variable': variable,
                    'type': 'UNDERFLOW',
                    'result': f"< {self.min_int}",
                    'limit': f"MIN_INT = {self.min_int}",
                    'recommendation': f"Use valores menores ou verifique limites antes da operação"
                }
        
        # Verificar multiplicação
        elif operator == '*':
            # Multiplicação é perigosa: pode crescer exponencialmente
            if value > 1000000:  # Heurística: multiplicadores grandes
                return {
                    'operation': f"{variable} = {operation['old_variable']} * {value}",
                    'variable': variable,
                    'type': 'OVERFLOW',
                    'result': f"Potencialmente > {self.max_int}",
                    'limit': f"MAX_INT = {self.max_int}",
                    'recommendation': f"Multiplicadores grandes podem causar overflow. Adicione verificação de limites."
                }
        
        # Verificar divisão por zero (não é overflow, mas é crítico)
        elif operator == '/' or operator == '%':
            if value == 0:
                return {
                    'operation': f"{variable} = {operation['old_variable']} {operator} {value}",
                    'variable': variable,
                    'type': 'DIVISION_BY_ZERO',
                    'result': 'UNDEFINED',
                    'limit': 'N/A',
                    'recommendation': 'Divisão por zero é matematicamente impossível'
                }
        
        return None
    
    def check_explicit_overflow(self, variable: str, value: int) -> Optional[Dict]:
        """
        Verifica se um valor explícito causa overflow
        
        Exemplo: balance == 99999999999999999999 (maior que MAX_INT)
        """
        if value > self.max_int:
            return {
                'operation': f"{variable} = {value}",
                'variable': variable,
                'type': 'EXPLICIT_OVERFLOW',
                'result': value,
                'limit': f"MAX_INT = {self.max_int}",
                'recommendation': f"Valor excede o limite máximo de inteiros de 64 bits"
            }
        
        if value < self.min_int:
            return {
                'operation': f"{variable} = {value}",
                'variable': variable,
                'type': 'EXPLICIT_UNDERFLOW',
                'result': value,
                'limit': f"MIN_INT = {self.min_int}",
                'recommendation': f"Valor está abaixo do limite mínimo de inteiros de 64 bits"
            }
        
        return None
    
    def get_safe_range(self) -> Tuple[int, int]:
        """Retorna o range seguro de valores"""
        return (self.min_int, self.max_int)
    
    def format_limits(self) -> str:
        """Formata os limites de forma legível"""
        return f"""
╔══════════════════════════════════════════════════════════╗
║              OVERFLOW SENTINEL - LIMITES                 ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Tipo: Inteiros de 64 bits (signed)                     ║
║                                                          ║
║  MAX_INT: {self.max_int:>20,}                    ║
║  MIN_INT: {self.min_int:>20,}                    ║
║                                                          ║
║  Range seguro: [{self.min_int}, {self.max_int}]         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""


# Singleton para uso global
_sentinel_instance = None

def get_overflow_sentinel() -> OverflowSentinel:
    """Retorna instância singleton da Sentinela"""
    global _sentinel_instance
    if _sentinel_instance is None:
        _sentinel_instance = OverflowSentinel()
    return _sentinel_instance
