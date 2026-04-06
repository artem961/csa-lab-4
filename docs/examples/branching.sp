(def x -1)
(if #t
    (block
    (out 0 "True block")
    (set x 1))
    (block
    (out 0 "False block")
    (set x 0)
    ))

(out 0 x)