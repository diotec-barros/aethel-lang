from lark import Lark
from aethel_grammar import aethel_grammar


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
        return [f"{p.children[0].value}:{p.children[1].value}" for p in node.children]
    
    def _get_block(self, node):
        # Extrai as condições lógicas
        return [" ".join([c.children[0].value, c.children[1].value, c.children[2].value]) for c in node.children]
    
    def _get_settings(self, node):
        # Extrai as configurações para a IA (ex: priority: security)
        return {s.children[0].value: s.children[1].value for s in node.children}
