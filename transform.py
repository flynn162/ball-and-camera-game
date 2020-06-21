from dsl_parser import Cons, Accumulator

def ASSERT_EQ(str1, str2):
    if str1 != str2:
        raise RuntimeError('should be %s but got %s' % (str2, str1))

UNCHANGED = Cons('<UNCHANGED>', None)

class Transform:
    class Placeholder:
        def __init__(self, name, ellipsis=False):
            self.sexp = None
            self.name = name
            self.ellipsis = ellipsis

        def put_value(self, sexp):
            self.sexp = sexp

        def __repr__(self):
            ellipsis = '0+' if self.ellipsis else ''
            return '<placeholder%s %s>' % (ellipsis, self.name)

    def __init__(self, sexp):
        self.placeholders = {}
        ASSERT_EQ(sexp.car, 'define-transform')

        # next element
        sexp = sexp.cdr
        self.name = sexp.car

        # next element
        sexp = sexp.cdr
        self.src = self._parse_src(sexp.car)
        self.hint = self.src.car

        # next element
        sexp = sexp.cdr
        ASSERT_EQ(sexp.car, '=>')

        # the rest (can be null)
        sexp = sexp.cdr
        self.dst = self._parse_dst(sexp)

    def _parse_transform(self, sexp, callback):
        while sexp is not None:
            if isinstance(sexp.car, Cons):
                self._parse_transform(sexp.car, callback)
            elif sexp.car.startswith('<') and sexp.car.endswith('>'):
                ellipsis = False
                if sexp.cdr is not None and sexp.cdr.car == '...':
                    ellipsis = True
                    if sexp.cdr.cdr is not None:
                        raise RuntimeError('Extra stuff after "..."')
                sexp.car = callback(sexp.car, ellipsis)  # set-car!

            sexp = sexp.cdr

    def _parse_src(self, sexp):
        def callback(name, ellipsis):
            placeholder = self.Placeholder(name, ellipsis)
            self.placeholders[name] = placeholder
            return placeholder

        self._parse_transform(sexp, callback)
        return sexp

    def _parse_dst(self, list_of_sexps):
        def callback(name, ellipsis):
            previously = self.placeholders.get(name)
            if previously is None:
                raise RuntimeError('Unknown placeholder: {}'.format(name))
            if previously.ellipsis and (not ellipsis):
                raise RuntimeError('Missing ellipsis: {}'.format(name))
            if (not previously.ellipsis) and ellipsis:
                raise RuntimeError('Unexpected ellipsis: {}'.format(name))
            return previously

        self._parse_transform(list_of_sexps, callback)
        return list_of_sexps

    def _match(self, curr, to_match):
        while curr is not None:
            if isinstance(curr.car, self.Placeholder):
                if curr.car.ellipsis:
                    curr.car.put_value(to_match)  # match the entire tail
                    return True  # bail out
                elif to_match is None:
                    return False  # expected one non-empty pair
                else:
                    curr.car.put_value(to_match.car)
            elif isinstance(curr.car, Cons):
                if not isinstance(to_match, Cons):
                    return False
                elif not self._match(curr.car, to_match.car):
                    return False
            else:
                if curr.car != to_match.car:
                    return False

            curr = curr.cdr
            to_match = to_match.cdr

        # if `to_match` is longer than expected
        if to_match is not None:
            return False

        return True

    def _generate(self, curr):
        acc = Accumulator()

        while curr is not None:
            if isinstance(curr.car, self.Placeholder):
                if curr.car.ellipsis:
                    acc.extend(curr.car.sexp)
                else:
                    acc.append(curr.car.sexp)
            elif isinstance(curr.car, Cons):
                acc.append(self._generate(curr.car))
            elif curr.car != '...':
                acc.append(curr.car)

            curr = curr.cdr

        return acc.to_list()

    def try_transform(self, sexp):
        if not self._match(self.src, sexp):
            return UNCHANGED
        if self.dst is None:
            return None
        else:
            return self._generate(self.dst)

    def recursively_transform(self, sexp):
        acc = Accumulator()
        changed = False

        while sexp is not None:
            if isinstance(sexp.car, Cons):
                result = self.recursively_transform(sexp.car)
                if result is UNCHANGED:
                    acc.append(sexp.car)
                else:
                    changed = True
                    acc.extend(result)
            else:
                acc.append(sexp.car)

            sexp = sexp.cdr

        # To return: UNCHANGED or a (possibly empty) list of S-expressions
        sexp = acc.to_list()
        transformed = self.try_transform(sexp)
        if transformed is not UNCHANGED:
            return transformed
        elif changed:
            # `transformed` is UNCHANGED, but the sexp has changed in deeper
            # levels
            return sexp
        else:
            return UNCHANGED

def main():
    import dsl_parser
    parser = dsl_parser.SchemeParser()
    sexp = parser.parse(open('transform.scm', 'rb'))
    transform = Transform(sexp.cdr.car)
    return transform

def main2():
    import dsl_parser
    parser = dsl_parser.SchemeParser()
    return parser.parse(open('rule.scm', 'rb'))
