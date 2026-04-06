from translator.parser import *

code = """
(def x (+ 1 -1))
(if #t
    (block
    (out 0 "True block")
    (set x 1))
    (block
    (out 0 "False block")
    (set x 0)
    ))

(out 0 x)
"""

# 1. На токены
tokens = tokenize(code)

# 2. В сырое дерево
raw_ast = Parser(tokens).parse()

# 3. В логические структуры
analyzer = SemanticAnalyzer()
final_ast = analyzer.analyze(raw_ast)


def pretty_print(node, indent=0):
    prefix = "  " * indent

    if isinstance(node, DefNode):
        print(f"{prefix}DefNode: variable='{node.variable}'")
        pretty_print(node.expression, indent + 1)

    elif isinstance(node, SetNode):
        print(f"{prefix}SetNode: variable='{node.variable}'")
        pretty_print(node.expression, indent + 1)

    elif isinstance(node, IfNode):
        print(f"{prefix}IfNode:")
        print(f"{prefix}  CONDITION:")
        pretty_print(node.condition, indent + 2)
        print(f"{prefix}  THEN:")
        pretty_print(node.then_block, indent + 2)
        print(f"{prefix}  ELSE:")
        pretty_print(node.else_block, indent + 2)

    elif isinstance(node, WhileNode):
        print(f"{prefix}WhileNode:")
        print(f"{prefix}  CONDITION:")
        pretty_print(node.condition, indent + 2)
        print(f"{prefix}  BODY:")
        pretty_print(node.body, indent + 2)

    elif isinstance(node, BlockNode):
        print(f"{prefix}BlockNode:")
        for expr in node.expressions:
            pretty_print(expr, indent + 1)

    elif isinstance(node, IONode):
        print(f"{prefix}IONode: op='{node.operation}', port={node.port}")
        if node.expression:
            pretty_print(node.expression, indent + 1)

    elif isinstance(node, FunctionCallNode):
        print(f"{prefix}FunctionCallNode: name='{node.name}'")
        for arg in node.args:
            pretty_print(arg, indent + 1)

    elif isinstance(node, LambdaNode):
        print(f"{prefix}LambdaNode: params={node.parameters}")
        pretty_print(node.body, indent + 1)

    # Атомы
    elif isinstance(node, SymbolNode):
        print(f"{prefix}SymbolNode: '{node.name}'")
    elif isinstance(node, NumberNode):
        print(f"{prefix}NumberNode: {node.value}")
    elif isinstance(node, StringNode):
        print(f"{prefix}StringNode: \"{node.value}\"")
    elif isinstance(node, BooleanNode):
        print(f"{prefix}BooleanNode: {node.value}")
    else:
        print(f"{prefix}Unknown Node: {node}")



print("--- Итоговое дерево---")
for node in final_ast:
    pretty_print(node)
    print("-" * 30)