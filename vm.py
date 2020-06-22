import bytecode_compiler
import dsl_parser
import fuzzy

POP = 1
MIN = 2
MAX = 3
GET_INPUT_BY_INDEX = 4
CALL_FUNCTION_BY_REF = 5
FEED_DEFUZZER_FAST = 6

class VM(bytecode_compiler.Constants):
    def __init__(self, inputs, outputs, rule_path):
        sexp = None
        with open(rule_path, 'rb') as fd:
            sexp = dsl_parser.SchemeParser().parse(fd)
        bytecode = bytecode_compiler.compile_to_bytecode(sexp)
        super().__init__(inputs, outputs, bytecode)
        self.bytecode = self.eliminate_map_lookup(bytecode)
        self.defuzzers = [fuzzy.Defuzzer() for _ in range(len(outputs))]

        buflen = bytecode_compiler.compute_buffer_length(self.bytecode)
        self.bcbuf = [None] * buflen
        self._encode()

        self.stack = [None] * 16
        self.sp = 0

    def _encode_kernel(self, idx, ins):
        if ins.car == '%pop':
            self.bcbuf[idx] = POP
            return 1
        if ins.car == '%min':
            self.bcbuf[idx] = MIN
            return 1
        if ins.car == '%max':
            self.bcbuf[idx] = MAX
            return 1
        if ins.car == '%get-input-by-index':
            self.bcbuf[idx] = GET_INPUT_BY_INDEX
            self.bcbuf[idx + 1] = ins.cdr.car
            return 2
        if ins.car == '%call-function-by-ref':
            self.bcbuf[idx] = CALL_FUNCTION_BY_REF
            self.bcbuf[idx + 1] = ins.cdr.car
            return 2
        if ins.car == '%feed-defuzzer-fast':
            self.bcbuf[idx] = FEED_DEFUZZER_FAST
            self.bcbuf[idx + 1] = ins.cdr.car
            self.bcbuf[idx + 2] = ins.cdr.cdr.car
            return 3

    def _encode(self):
        idx = 0
        current = self.bytecode
        while idx < len(self.bcbuf):
            idx += self._encode_kernel(idx, current.car)
            current = current.cdr

    def input(self, key, value):
        idx = self.input_to_index[key]
        self.inputs[idx] = value

    def _pop(self):
        self.sp -= 1
        return self.stack[self.sp]

    def _push(self, value):
        self.stack[self.sp] = value
        self.sp += 1

    def _interpret(self, idx, ins):
        if ins == POP:
            self.sp -= 1
            return 1
        if ins == MIN:
            self._push(min(self._pop(), self._pop()))
            return 1
        if ins == MAX:
            self._push(max(self._pop(), self._pop()))
            return 1
        if ins == GET_INPUT_BY_INDEX:
            # push the input onto the stack
            input_index = self.bcbuf[idx + 1]
            self._push(self.inputs[input_index])
            return 2
        if ins == CALL_FUNCTION_BY_REF:
            # take the input off the stack and call member function
            # push the result onto the stack
            result = self.bcbuf[idx + 1](self._pop())
            self._push(result)
            return 2
        if ins == FEED_DEFUZZER_FAST:
            # do not take anything off the stack
            defuzzer = self.defuzzers[self.bcbuf[idx + 1]]
            y2 = self.bcbuf[idx + 2]
            defuzzer.feed(y2, self.stack[self.sp - 1])
            return 3

    def run(self):
        for defuzzer in self.defuzzers:
            defuzzer.reset()
        idx = 0
        while idx < len(self.bcbuf):
            idx += self._interpret(idx, self.bcbuf[idx])

    def get_output(self, key):
        idx = self.output_to_index[key]
        return self.defuzzers[idx].defuzz()
