from dsl_parser import SchemeParser, Accumulator, Cons
import transform

def compute_bytecode_buffer_length(self, bytecode_list):
    result = 0
    while bytecode_list is not None:
        result += len(bytecode_list.car)
        bytecode_list = bytecode_list.cdr
    return result

RULES = {}

def load_transforms(path):
    sexp = None
    with open(path, 'rb') as fd:
        parser = SchemeParser()
        sexp = parser.parse(fd)
    while sexp is not None:
        rule = transform.Transform(sexp.car)
        RULES[rule.name] = rule
        sexp = sexp.cdr

def transform_repeatedly_cb(callback, sexp):
    changed = True
    while changed:
        result = callback(sexp)
        if result is None:
            return None
        elif result is transform.UNCHANGED:
            changed = False
        else:
            sexp = result.car
    return sexp

def transform_repeatedly(name, original_sexp):
    def callback(sexp):
        return RULES[name].recursively_transform(sexp)

    return transform_repeatedly_cb(callback, original_sexp)

def apply_multiple_transforms(rules, apply_transform, current):
    changed = False

    for rule in rules:
        result = apply_transform(rule, current)
        if result is None:  # deleted by rule
            return None
        elif result is not transform.UNCHANGED:
            current = result.car
            changed = True

    if changed:
        return Cons(current, None)
    else:
        return transform.UNCHANGED

def expand_AND_OR(sexp):
    rules = (RULES['expand-and'], RULES['expand-and/cleanup'],
             RULES['expand-or'], RULES['expand-or/cleanup'])
    return apply_multiple_transforms(
        rules,
        lambda rule, current: rule.recursively_transform(current),
        sexp
    )

def expand_compute_input_AND_OR(sexp):
    return apply_multiple_transforms(
        (RULES['defuzzer-input/and'], RULES['defuzzer-input/or']),
        lambda rule, current: rule.recursively_transform(current),
        sexp
    )

def _expand_if_statement(sexp):
    if sexp.car != 'if':
        return sexp
    else:
        return transform_repeatedly_cb(expand_AND_OR, sexp)

def expand_if_conditions(sexp):
    acc = Accumulator()
    while sexp is not None:
        acc.append(_expand_if_statement(sexp.car))
        sexp = sexp.cdr
    return acc.to_list()

def compile_to_bytecode(sexp):
    # lift all nested if statements
    sexp = transform_repeatedly('if-lifting', sexp)
    sexp = transform_repeatedly('delete-empty-then', sexp)
    # expand all conditions in the if statements
    sexp = expand_if_conditions(sexp)

    # expand if statements
    sexp = transform_repeatedly('compile-if-statement', sexp)
    # expand %compute-defuzzer-input
    sexp = transform_repeatedly_cb(expand_compute_input_AND_OR, sexp)
    sexp = transform_repeatedly('defuzzer-input/is', sexp)
    # expand %compute-defuzzer-output
    sexp = transform_repeatedly('defuzzer-output/begin', sexp)
    sexp = transform_repeatedly('defuzzer-output/empty-begin', sexp)
    sexp = transform_repeatedly('defuzzer-output/set!', sexp)

    return sexp


def main():
    load_transforms('transform.scm')
    return SchemeParser().parse(open('rule.scm', 'rb'))
