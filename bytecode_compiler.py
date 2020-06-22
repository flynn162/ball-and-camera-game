from dsl_parser import SchemeParser, Accumulator, Cons
import transform

def compute_buffer_length(bytecode_list):
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

def expand_if_statement(sexp):
    if sexp.car != 'if':
        return sexp
    else:
        return transform_repeatedly_cb(expand_AND_OR, sexp)

def sexp_map(func, sexp):
    acc = Accumulator()
    while sexp is not None:
        acc.append(func(sexp.car))
        sexp = sexp.cdr
    return acc.to_list()

def compile_to_bytecode(sexp):
    # lift all nested if statements
    sexp = transform_repeatedly('if-lifting', sexp)
    sexp = transform_repeatedly('delete-empty-then', sexp)
    # expand all conditions in the if statements
    sexp = sexp_map(expand_if_statement, sexp)

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
    sexp = SchemeParser().parse(open('rule.scm', 'rb'))
    return compile_to_bytecode(sexp)


class Constants:
    @staticmethod
    def assign_number(dictionary):
        return dict(zip(dictionary.keys(), range(len(dictionary))))

    @staticmethod
    def flatten(dictionary, index_info):
        array = [None] * len(dictionary)
        for name, index in index_info.items():
            array[index] = dictionary[name]
        return array

    def __init__(self, inputs, outputs, bytecode):
        self.input_to_index = self.assign_number(inputs)
        self.output_to_index = self.assign_number(outputs)
        self.inputs = [None] * len(inputs)

        mf = {}
        for key in self.extract_member_function_calls(bytecode):
            if key[2] == 'in' and key[0] not in self.input_to_index:
                raise RuntimeError('Unknown input {}'.format(key[0]))
            elif key[2] == 'out' and key[0] not in self.output_to_index:
                raise RuntimeError('Unknown output {}'.format(key[0]))
            if key[2] == 'in':
                mf[(key[0], key[1])] = getattr(inputs[key[0]], key[1])
            else:
                mf[(key[0], key[1])] = getattr(outputs[key[0]], key[1])

        self.member_function_to_index = self.assign_number(mf)
        self.member_functions = self.flatten(mf, self.member_function_to_index)

    @staticmethod
    def extract_member_function_calls(bytecode):
        while bytecode is not None:
            instruction = bytecode.car
            if instruction.car == '%call-member-function':
                yield (instruction.cdr.car, instruction.cdr.cdr.car, 'in')
            elif instruction.car == '%feed':
                yield (instruction.cdr.car, instruction.cdr.cdr.car, 'out')
            bytecode = bytecode.cdr

    def eliminate_map_lookup(self, bytecode):
        return sexp_map(self._indexify, bytecode)

    def get_member_function(self, cons):
        key = (cons.car, cons.cdr.car)
        idx = self.member_function_to_index[key]
        return self.member_functions[idx]

    def _indexify(self, instruction):
        if instruction.car == '%get-input':
            # (%get-input <name>)
            # => (%get-input-by-index <index>)
            idx = self.input_to_index[instruction.cdr.car]
            return Cons('%get-input-by-index', Cons(idx, None))
        elif instruction.car == '%call-member-function':
            # (%call-member-function <input> <level>)
            # => (%call-function-by-ref <triangle-function-ref>)
            ref = self.get_member_function(instruction.cdr)
            return Cons('%call-function-by-ref', Cons(ref, None))
        elif instruction.car == '%feed':
            # (%feed <output> <level>)
            # => (%feed-defuzzer-fast <defuzzer-index> <x2>)
            idx = self.output_to_index[instruction.cdr.car]
            mf = self.get_member_function(instruction.cdr)
            return Cons('%feed-defuzzer-fast', Cons(idx, Cons(mf.x2, None)))
        else:
            return instruction

def init():
    load_transforms('transform.scm')

init()
