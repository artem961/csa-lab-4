(def i 0)
(while (< i 10)
    (block
        (set i (+ i 1))
        (out 0 i)
    ))