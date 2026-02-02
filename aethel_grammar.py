# Gramática Experimental da Aethel
aethel_grammar = """
    start: intent_def+
    
    intent_def: "intent" NAME "(" params ")" "{" guard_block solve_block verify_block "}"
    
    params: (param ("," param)*)?
    param: NAME ":" NAME
    
    guard_block: "guard" "{" (condition ";")+ "}"
    solve_block: "solve" "{" (setting ";")+ "}"
    verify_block: "verify" "{" (condition ";")+ "}"
    
    condition: NAME OPERATOR NAME  // Simplificado para o protótipo
    setting: NAME ":" NAME
    
    OPERATOR: ">=" | "<=" | "==" | "!=" | ">" | "<"
    NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
    
    %import common.WS
    %ignore WS
"""
