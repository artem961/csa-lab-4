import os

from src.binary import write_binary
from src.translator.parser import parse_code
from src.translator.definition import print_ast
from src.translator.translator import Translator

code = """
  (def x 2147483647)
  (out 1 -1)
"""

final_ast = parse_code(code)
print_ast(final_ast)
translator = Translator(data_mem_size=1024)
instr, data = translator.translate(final_ast)

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out'))
write_binary(out_path + ".bin", instr, data, listing_path=out_path + '.txt')

