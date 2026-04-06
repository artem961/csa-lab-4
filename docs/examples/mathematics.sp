; Поддерживаются только целые числа

(def x 5)
(def y 10)
(out 0 (+ x y)) ; => 15
(out 0 (- x y)) ; => -5
(out 0 (* x y)) ; => 50
(out 0 (/ y x)) ; => 2
(out 0 (% y x)) ; => 0
(out 0 (^ x 2)) ; => 25

(out 0 (< x y)) ; => #t
(out 0 (> x y)) ; => #f
(out 0 (= x 2)) ; => #f


(set x (+ x y))
(out 0 x) ; => 15