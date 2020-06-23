;; if the camera is too close to the ball
(if (is dist Z)
    (begin
      (if (and (is dir-x Z) (is dir-y Z))
          (begin (set! dx NS)
                 (set! rot NM)))
      (if (is dir-x PS)
          (begin (set! dx NS)
                 (set! rot NM)))
      (if (is dir-x NS)
          (begin (set! dx PS)
                 (set! rot PM)))
      (if (is dir-y PS)
          (begin (set! dy NS)
                 (set! rot NM)))
      (if (is dir-y NS)
          (begin (set! dy PS)
                 (set! rot PM)))
      ))

;; condition to stop moving
(if (and (is dir-x PM) (is dir-y PM) (is dist PS))
    (begin
      (set! rot Z)
      (set! dx Z)
      (set! dy Z)
      ))

;; if the camera is too far from the ball, come closer
(if (is dist PM)
    (begin
      (if (is dir-x PM) (set! dx PM))
      (if (is dir-x PS) (set! dx PS))
      (if (is dir-y PM) (set! dy PM))
      (if (is dir-y PS) (set! dy PS))
      ))

;; rotation
(if (or (is dir-x NS) (is dir-x NM) (is dir-x Z)) (set! rot PM))
(if (or (is dir-y NS) (is dir-y NM) (is dir-y Z)) (set! rot NM))
