import re

from src.translator.definition import (
    ArrayOpsNode,
    BlockNode,
    BooleanNode,
    DefArrayNode,
    DefNode,
    FunctionCallNode,
    IfNode,
    InterruptHandlerNode,
    IONode,
    LambdaNode,
    ListNode,
    Node,
    NumberNode,
    SetNode,
    StringNode,
    SymbolNode,
    WhileNode,
)


def parse_code(code: str) -> list[Node]:
   # Принимает исходный код на Lisp и возвращает типизированное AST.

    tokens = _tokenize(code)
    raw_ast = _RawParser(tokens).parse()
    typed_ast = _SemanticAnalyzer().analyze(raw_ast)
    return typed_ast


def _tokenize(code: str) -> list[str]:
    # Разбивает исходный код на токены, удаляя комментарии.
    code = re.sub(r';.*', '', code)
    return re.findall(r'"[^"]*"|[()]|[^\s()]+', code)


class _RawParser:
    # Первичный парсер: превращает токены в сырое дерево из ListNode и атомов.

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> list[Node]:
        tree = []
        while self.pos < len(self.tokens):
            tree.append(self._parse_expression())
        return tree

    def _parse_expression(self) -> Node:
        if self.pos >= len(self.tokens):
            raise SyntaxError("Unexpected end of input")

        token = self.tokens[self.pos]
        self.pos += 1

        if token == '(':
            elements = []
            while self.pos < len(self.tokens) and self.tokens[self.pos] != ')':
                elements.append(self._parse_expression())

            if self.pos >= len(self.tokens):
                raise SyntaxError("Missing closing parenthesis ')'")
            self.pos += 1  # Пропускаем ')'
            return ListNode(elements)

        elif token == ')':
            raise SyntaxError(f"Unexpected ')' at position {self.pos}")

        return self._parse_atom(token)

    def _parse_atom(self, token: str) -> Node:
        if token == "#t":
            return BooleanNode(True)
        if token == "#f":
            return BooleanNode(False)
        if token.startswith('"') and token.endswith('"'):
            return StringNode(token[1:-1])
        if re.match(r'^-?\d+$', token):
            return NumberNode(int(token))
        return SymbolNode(token)


class _SemanticAnalyzer:
    # Трансформирует сырые ListNode в логические структуры.

    def analyze(self, raw_nodes: list[Node]) -> list[Node]:
        return [self._transform(node) for node in raw_nodes]

    def _transform(self, node: Node) -> Node:
        if not isinstance(node, ListNode):
            return node

        if not node.elements:
            return ListNode([])

        head = node.elements[0]
        args = node.elements[1:]

        if not isinstance(head, SymbolNode):
            raise SyntaxError(f"Expected operator or function name, got: {head}")

        name = head.name

        if name == "def":
            var_name = args[0].name if isinstance(args[0], SymbolNode) else "unknown"
            return DefNode(var_name, self._transform(args[1]))

        elif name == "set":
            var_name = args[0].name if isinstance(args[0], SymbolNode) else "unknown"
            return SetNode(var_name, self._transform(args[1]))

        elif name == "if":
            return IfNode(self._transform(args[0]), self._transform(args[1]), self._transform(args[2]))

        elif name == "while":
            return WhileNode(self._transform(args[0]), self._transform(args[1]))

        elif name == "block":
            return BlockNode([self._transform(arg) for arg in args])

        elif name == "lambda":
            params = [p.name for p in args[0].elements if isinstance(p, SymbolNode)] if isinstance(args[0],
                                                                                                   ListNode) else []
            return LambdaNode(params, self._transform(args[1]))

        elif name == "out":
            port = args[0].value if isinstance(args[0], NumberNode) else 0
            return IONode("out", port, self._transform(args[1]))

        elif name == "in":
            port = args[0].value if isinstance(args[0], NumberNode) else 0
            return IONode("in", port)

        elif name == "out-str":
            port = args[0].value if isinstance(args[0], NumberNode) else 0
            return IONode("out-str", port, self._transform(args[1]))

        elif name == "interrupt-handler":
            port = args[0].value if isinstance(args[0], NumberNode) else 0
            return InterruptHandlerNode(port, self._transform(args[1]))

        elif name == "alloc":
            size_expr = self._transform(args[0])
            return DefArrayNode(name="alloc", args=None, size=size_expr)

        elif name == "array":
            val_nodes = [self._transform(arg) for arg in args]
            return DefArrayNode(name="array", args=val_nodes, size=None)

        elif name == "aref":
            array_ref = self._transform(args[0])
            offset = self._transform(args[1])
            return ArrayOpsNode("aref", array_ref, offset)

        elif name == "aset":
            array_ref = self._transform(args[0])
            offset = self._transform(args[1])
            value = self._transform(args[2])
            return ArrayOpsNode("aset", array_ref, offset, value)

        # Вызов функции или математика
        return FunctionCallNode(name, [self._transform(arg) for arg in args])