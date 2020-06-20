;; if the camera is too close to the ball
(if (or (is dist Z) (is dist PS))
    (begin
      (if (and (is dir-x Z) (is dir-y Z)) (set! dx NS))
      (if (is dir-x PS) (set! dx NS))
      (if (is dir-x NS) (set! dx PS))
      (if (is dir-y PS) (set! dy NS))
      (if (is dir-y NS) (set! dy PS))
      ))

;; condition to stop moving
(if (and (is dir-x PM) (is dir-y PM) (is dist PS))
    (begin
      (set! rot Z)
      (set! dx Z)
      (set! dy Z)
      ))

;; rotation
(if (is dir-x NM) (set! rot PM))
(if (is dir-y NM) (set! rot NM))
