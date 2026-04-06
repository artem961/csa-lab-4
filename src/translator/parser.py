import re
from typing import List
from src.translator.definition import *


def tokenize(code: str) -> List[str]:
    """Разбивает исходный код на токены, удаляя комментарии."""
    code = re.sub(r';.*', '', code)
    tokens = re.findall(r'"[^"]*"|[()]|[^\s()]+', code)
    return tokens


class Parser:
    """Первичный парсер: превращает токены в сырое дерево из ListNode и атомов."""

    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> List[Node]:
        tree = []
        while self.pos < len(self.tokens):
            tree.append(self.parse_expression())
        return tree

    def parse_expression(self) -> Node:
        if self.pos >= len(self.tokens):
            raise SyntaxError("Unexpected end of input")

        token = self.tokens[self.pos]
        self.pos += 1

        if token == '(':
            elements = []
            while self.pos < len(self.tokens) and self.tokens[self.pos] != ')':
                elements.append(self.parse_expression())

            if self.pos >= len(self.tokens):
                raise SyntaxError("Missing closing parenthesis ')'")
            self.pos += 1  # Пропускаем ')'
            return ListNode(elements)

        elif token == ')':
            raise SyntaxError(f"Unexpected ')' at position {self.pos}")

        return self.parse_atom(token)

    def parse_atom(self, token: str) -> Node:
        if token == "#t": return BooleanNode(True)
        if token == "#f": return BooleanNode(False)
        if token.startswith('"') and token.endswith('"'):
            return StringNode(token[1:-1])
        if re.match(r'^-?\d+$', token):
            return NumberNode(int(token))
        return SymbolNode(token)


class SemanticAnalyzer:
    """Трансформирует сырые ListNode в логические структуры"""

    def analyze(self, raw_nodes: List[Node]) -> List[Node]:
        return [self.transform(node) for node in raw_nodes]

    def transform(self, node: Node) -> Node:
        if not isinstance(node, ListNode):
            return node

        if not node.elements:
            return ListNode([])

        head = node.elements[0]
        args = node.elements[1:]

        # Если первый элемент — не символ, значит это просто список выражений или ошибка
        if not isinstance(head, SymbolNode):
            raise SyntaxError("Unexpected symbol")

        name = head.name

        if name == "def":
            # (def x expression)
            var_name = args[0].name if isinstance(args[0], SymbolNode) else "unknown"
            return DefNode(var_name, self.transform(args[1]))

        if name == "set":
            # (set x expression)
            var_name = args[0].name if isinstance(args[0], SymbolNode) else "unknown"
            return SetNode(var_name, self.transform(args[1]))

        if name == "if":
            # (if cond then else)
            return IfNode(self.transform(args[0]), self.transform(args[1]), self.transform(args[2]))

        if name == "while":
            # (while cond body)
            return WhileNode(self.transform(args[0]), self.transform(args[1]))

        if name == "block":
            # (block expr1 expr2 ...)
            return BlockNode([self.transform(arg) for arg in args])

        if name == "lambda":
            # (lambda (p1 p2) body)
            params = []
            if isinstance(args[0], ListNode):
                params = [p.name for p in args[0].elements if isinstance(p, SymbolNode)]
            return LambdaNode(params, self.transform(args[1]))

        if name == "out":
            # (out port expression)
            port = args[0].value if isinstance(args[0], NumberNode) else 0
            return IONode("out", port, self.transform(args[1]))

        if name == "in":
            # (in port)
            port = args[0].value if isinstance(args[0], NumberNode) else 0
            return IONode("in", port)

        if name == "trap":
            # (trap code)
            code = args[0].value if isinstance(args[0], NumberNode) else 0
            return TrapNode(code)

        # (+ x y) или (some-func a b)
        return FunctionCallNode(name, [self.transform(arg) for arg in args])