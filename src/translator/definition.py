from dataclasses import dataclass
from typing import List, Union, Optional

@dataclass
class Node:
    pass


@dataclass
class NumberNode(Node):
    value: int

@dataclass
class SymbolNode(Node):
    name: str

@dataclass
class StringNode(Node):
    value: str

@dataclass
class BooleanNode(Node):
    value: bool


@dataclass
class ListNode(Node):
    elements: List[Node]


@dataclass
class DefNode(Node):
    variable: str
    expression: Node

@dataclass
class SetNode(Node):
    variable: str
    expression: Node

@dataclass
class IfNode(Node):
    condition: Node
    then_block: Node
    else_block: Node

@dataclass
class WhileNode(Node):
    condition: Node
    body: Node

@dataclass
class BlockNode(Node):
    expressions: List[Node]

@dataclass
class LambdaNode(Node):
    parameters: List[str]
    body: Node

@dataclass
class IONode(Node):
    operation: str
    port: int
    expression: Optional[Node] = None

@dataclass
class FunctionCallNode(Node):
    name: str
    args: List[Node]

@dataclass
class TrapNode(Node):
    interrupt_code: int


def print_ast(nodes: List[Node], indent: int = 0):
    prefix = "  " * indent

    for i, node in enumerate(nodes):
        if indent == 0 and i > 0:
            print("-" * 40)

        if isinstance(node, NumberNode):
            print(f"{prefix}Number: {node.value}")

        elif isinstance(node, SymbolNode):
            print(f"{prefix}Symbol: {node.name}")

        elif isinstance(node, StringNode):
            print(f"{prefix}String: \"{node.value}\"")

        elif isinstance(node, BooleanNode):
            print(f"{prefix}Boolean: {'#t' if node.value else '#f'}")

        elif isinstance(node, DefNode):
            print(f"{prefix}Definition (variable: {node.variable}):")
            print_ast([node.expression], indent + 1)

        elif isinstance(node, SetNode):
            print(f"{prefix}Assignment (variable: {node.variable}):")
            print_ast([node.expression], indent + 1)

        elif isinstance(node, IfNode):
            print(f"{prefix}Condition (IF):")
            print(f"{prefix}  [Condition]:")
            print_ast([node.condition], indent + 2)
            print(f"{prefix}  [Then]:")
            print_ast([node.then_block], indent + 2)
            print(f"{prefix}  [Else]:")
            print_ast([node.else_block], indent + 2)

        elif isinstance(node, WhileNode):
            print(f"{prefix}Loop (WHILE):")
            print(f"{prefix}  [Condition]:")
            print_ast([node.condition], indent + 2)
            print(f"{prefix}  [Body]:")
            print_ast([node.body], indent + 2)

        elif isinstance(node, BlockNode):
            print(f"{prefix}Block:")
            print_ast(node.expressions, indent + 1)

        elif isinstance(node, LambdaNode):
            print(f"{prefix}Lambda (args: {', '.join(node.parameters)}):")
            print_ast([node.body], indent + 1)

        elif isinstance(node, IONode):
            print(f"{prefix}IO ({node.operation.upper()}, port: {node.port}):")
            if node.expression:
                print_ast([node.expression], indent + 1)

        elif isinstance(node, TrapNode):
            print(f"{prefix}Trap (interrupt code: {node.interrupt_code})")

        elif isinstance(node, FunctionCallNode):
            print(f"{prefix}Call: {node.name}")
            if node.args:
                for idx, arg in enumerate(node.args):
                    print_ast([arg], indent + 1)

        elif isinstance(node, ListNode):
            print(f"{prefix}List:")
            print_ast(node.elements, indent + 1)