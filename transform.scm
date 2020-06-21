(define-transform if-lifting
  (if <A> (begin (if <B> <C>) <D> ...))
  =>
  (if (and <A> <B>) <C>)
  (if <A> (begin <D> ...))
  )

(define-transform delete-empty-then
  (if <A> (begin))
  =>)
