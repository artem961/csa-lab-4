import os

from src.binary import write_binary
from translator.parser import *
from translator.translator import *

code = """
  (def add (lambda (a b) (+ a b)))
  (def sub (lambda (a b) (- a b)))
  (def mul (lambda (a b) (* a b)))
  
  ; Аргумент функции test является функцией
  (def test (lambda (fun) (fun 1 2)))
  
  (out 1 (test add)) ; -> 3
  (out 1 (test sub)) ; -> -1
  (out 1 (test mul)) ; -> 2
"""

final_ast = parse_code(code)
print_ast(final_ast)
translator = Translator(data_mem_size=1024)
instr, data = translator.translate(final_ast)

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out'))
write_binary(out_path + ".bin", instr, data, listing_path=out_path + '.txt')

