(define-transform if-lifting
  (if <A> (begin (if <B> <C>) <D> ...))
  =>
  (if (and <A> <B>) <C>)
  (if <A> (begin <D> ...))
  )

(define-transform delete-empty-then
  (if <A> (begin))
  =>)

(define-transform compile-if-statement
  (if <condition> <action>)
  =>
  (%compute-defuzzer-input <condition>)
  (%compute-defuzzer-output <action>)
  (%pop)
  )

(define-transform expand-and
  (and <A> <B> <C> ...)
  =>
  (and (%and <A> <B>) <C> ...)
  )

(define-transform expand-and/cleanup
  (and (%and <A> <B>))
  =>
  (%and <A> <B>)
  )

(define-transform expand-or
  (or <A> <B> <C> ...)
  =>
  (or (%or <A> <B>) <C> ...)
  )

(define-transform expand-or/cleanup
  (or (%or <A> <B>))
  =>
  (%or <A> <B>)
  )

(define-transform defuzzer-input/is
  (%compute-defuzzer-input (is <input-variable> <level>))
  =>
  (%get-input <input-variable>)
  (%call-member-function <input-variable> <level>)
  )

(define-transform defuzzer-input/and
  (%compute-defuzzer-input (%and <P> <Q>))
  =>
  (%compute-defuzzer-input <P>)
  (%compute-defuzzer-input <Q>)
  (%min)
  )

(define-transform defuzzer-input/or
  (%compute-defuzzer-input (%or <P> <Q>))
  =>
  (%compute-defuzzer-input <P>)
  (%compute-defuzzer-input <Q>)
  (%max)
  )

(define-transform defuzzer-output/begin
  (%compute-defuzzer-output (begin <A> <B> ...))
  =>
  (%compute-defuzzer-output <A>)
  (%compute-defuzzer-output (begin <B> ...))
  )

(define-transform defuzzer-output/empty-begin
  (%compute-defuzzer-output (begin))
  =>)

(define-transform defuzzer-output/set!
  (%compute-defuzzer-output (set! <output-variable> <level>))
  =>
  (%feed <output-variable> <level>)
  )
