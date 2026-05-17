import os

from src.binary import write_binary
from translator.parser import *
from translator.translator import *

code = """
  (interrupt-handler 1 (lambda () (out 2 (in 1))))
  
  (def i 0)
  (while (< i 100) (block
    (set i (+ i 1))
  ))
"""

final_ast = parse_code(code)
print_ast(final_ast)
translator = Translator(data_mem_size=1024)
instr, data = translator.translate(final_ast)

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out'))
write_binary(out_path + ".bin", instr, data, listing_path=out_path + '.txt')

