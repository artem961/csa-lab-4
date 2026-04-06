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