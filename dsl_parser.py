import enum
import string
import collections

class Tokenizer:
    class Buffer:
        delim = (32, 9, 10, 13, 11, 12, 40, 41, 59)  # ();
        whitespace = (32, 9, 10, 13, 11, 12)
        linefeed = (0x0A,)

        def __init__(self, size):
            self.idx = 0
            self.data = bytearray(size)
            self.actual_length = 0

        def refill(self, fd):
            self.actual_length = fd.readinto(self.data)
            self.idx = 0
            return self.actual_length

        def eof(self):
            self.data[0] = 0x0A
            self.idx = 0
            self.actual_length = 1

        def has_next(self):
            return self.idx < self.actual_length

        def _copy_segment(self, i, j):
            return str(self.data[i:j], encoding='utf-8')

        def peekch(self):
            return self._copy_segment(self.idx, self.idx + 1)

        def skipch(self):
            self.idx += 1

        def getch(self):
            result = self.peekch()
            self.idx += 1
            return result

        def _read_until(self, chs, discard=False):
            # ???
            ending_idx = self.idx
            while self.has_next() and self.data[ending_idx] not in chs:
                ending_idx += 1
            result = None
            if not discard:
                result = self._copy_segment(self.idx, ending_idx)
            self.idx = ending_idx
            return result

        def read_and_discard_until_line_ends(self):
            self._read_until(self.linefeed, discard=True)

        def read_until_next_delim(self):
            return self._read_until(self.delim)

    class State(enum.IntEnum):
        reading_non_comments = 0,
        reading_comments = 1,

    def __init__(self, on_symbol, on_list_open, on_list_close):
        self.state = self.State.reading_non_comments
        self.b = self.Buffer(4096)
        self.symbol_acc = []
        # Handlers
        self.on_symbol = on_symbol
        self.on_list_open = on_list_open
        self.on_list_close = on_list_close

    def tokenize(self, fd):
        bytes_read = self.b.refill(fd)
        while bytes_read > 0:
            self.process_buffer()
            bytes_read = self.b.refill(fd)
        self.b.eof()
        self.process_buffer()

    def _yield_symbol(self):
        result = ''.join(self.symbol_acc)
        if result:
            self.on_symbol(result)
        self.symbol_acc = []

    def state_non_comments(self):
        ch = self.b.getch()
        if ch == '(':
            self._yield_symbol()
            self.on_list_open()
            return self.State.reading_non_comments
        elif ch == ')':
            self._yield_symbol()
            self.on_list_close()
            return self.State.reading_non_comments
        elif ch == ';':
            self._yield_symbol()
            return self.State.reading_comments  # start of comment
        elif ch in string.whitespace:
            self._yield_symbol()
            return self.State.reading_non_comments
        else:
            # regular characters A-B a-b
            self.symbol_acc.append(ch)
            if self.b.has_next():
                self.symbol_acc.append(self.b.read_until_next_delim())
            return self.State.reading_non_comments

    def state_comments(self):
        self.b.read_and_discard_until_line_ends()
        if self.b.has_next():
            # skip the linefeed '\n'
            self.b.skipch()
            return self.State.reading_non_comments
        else:
            return self.State.reading_comments

    def process_buffer(self):
        while self.b.has_next():
            if self.state == self.State.reading_non_comments:
                self.state = self.state_non_comments()
            else:
                self.state = self.state_comments()


def main():
    def on_list_open():
        print('(', end='')

    def on_list_close():
        print(')', end='')

    def on_symbol(symbol):
        if not symbol:
            raise ValueError
        print(symbol, end=' ')

    tokenizer = Tokenizer(on_symbol, on_list_open, on_list_close)
    fd = open('rule.scm', 'rb')
    tokenizer.tokenize(fd)
    print('\n====')


class Cons:
    __slots__ = ('car', 'cdr')
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr

    def print_repr(self):
        self._print_repr(self)
        print('')

    def _print_repr(self, curr):
        print('(', end='')
        while curr is not None:
            if isinstance(curr.car, Cons):
                self._print_repr(curr.car)
            else:
                print(curr.car, end=' ')
            curr = curr.cdr
        print(')', end='')

    def __len__(self):
        length = 0
        curr = self
        while curr is not None:
            length += 1
            curr = curr.cdr
        return length

class Accumulator:
    def __init__(self, element=None):
        if element is None:
            self.head = None
            self.tail = None
        else:
            self.head = Cons(element, None)
            self.tail = self.head

    def append(self, element):
        new_node = Cons(element, None)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.cdr = new_node
            self.tail = self.tail.cdr

    def extend(self, linked_list):
        while linked_list is not None:
            self.append(linked_list.car)
            linked_list = linked_list.cdr

    def to_list(self):
        return self.head


class SchemeParser:
    def __init__(self):
        def on_symbol(symbol):
            self.on_symbol(symbol)

        def on_list_open():
            self.on_list_open()

        def on_list_close():
            self.on_list_close()

        self.tokenizer = Tokenizer(on_symbol, on_list_open, on_list_close)
        self.root = Accumulator()
        self.stack = collections.deque()
        self.stack.appendleft(self.root)

    def on_symbol(self, symbol):
        self.stack[0].append(symbol)

    def on_list_open(self):
        self.stack.appendleft(Accumulator())

    def on_list_close(self):
        linked_list = self.stack.popleft().to_list()
        self.stack[0].append(linked_list)

    def parse(self, binary_fd):
        self.tokenizer.tokenize(binary_fd)
        if len(self.stack) != 1:
            raise ValueError('Unbalanced parenthesis')
        return self.root.to_list()
