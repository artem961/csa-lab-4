import os

from src.binary import write_binary
from translator.parser import *
from translator.translator import *

code = """
(block
  (def n 27)        ; Стартовое число
  (def steps 0)     ; Счетчик шагов
  (def max_val 0)   ; Максимальное достигнутое значение

  (while (> n 1)
    (block
      (set steps (+ steps 1))

      ;; Проверка и обновление максимума
      ;; Логика: (if (> n max_val) (set max_val n) 0)
      (if (> n max_val)
          (set max_val n)
          0)

      ;; Логика Коллатца: 
      ;; Если n % 2 == 0, то n = n / 2, иначе n = 3n + 1
      (if (= (% n 2) 0)
          (set n (/ n 2))
          (set n (+ (* n 3) 1)))
      
      ;; Каждые 10 шагов будем выводить промежуточное n в порт 1
      (if (= (% steps 10) 0)
          (out 1 n)
          0)
    )
  )

  ;; Финальный вывод
  (out 1 steps)    ; Сколько шагов занял путь к 1
  (out 1 max_val)  ; Какое число было пиковым
)
"""

final_ast = parse_code(code)
print_ast(final_ast)
translator = Translator(data_mem_size=1024)
instr, data = translator.translate(final_ast)

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'out'))
write_binary(out_path + ".bin", instr, data, listing_path=out_path + '.txt')

