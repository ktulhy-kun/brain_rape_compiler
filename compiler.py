from typing import Iterator
from typing import List, Tuple

from br_lexer import Block
from br_parser import Token, Line, NameSpace, BrFunctionType
from br_exceptions.lexer import LexerLevelErrorException, LexerBlockLevelErrorException
from builtin_functions import builtin_functions
from bytecode import ByteCode


class BfCompiler:
    def __init__(self, file_name):
        self.file_name = file_name
        self.file = None
        self.lines = []  # type: List[Line]
        self.block = None  # type: Block
        self._lines_process()
        self._block_process()
        self.namespaces = []  # type: List[NameSpace]
        self._create_default_namespace()

    @staticmethod
    def _get_line_level(s):
        """ Возвращает уровень вложенности строки """
        level = 0
        for ch in s:
            if ' ' == ch:
                level += 1
            else:
                break
        if level % 4:
            raise LexerLevelErrorException(s, level)
        return level // 4

    def _get_tokens(self, line_n: int, s: str) -> List[Token]:
        """ Возвращает список токенов из строки """
        pos = 0
        tokens = []
        for word in s.split(" "):
            if len(word.strip()):
                # Комментарии отсекаем
                if '#' == word[0]:
                    break
                tokens.append(Token(line_n, pos, word.strip()))
                pos += len(word)

            pos += 1
        return tokens

    def _get_line(self, line_n: int, s: str) -> Line or None:
        """ Возвращает Line из строки """
        level = self._get_line_level(s)
        tokens = self._get_tokens(line_n, s)
        line = None
        if tokens:
            line = Line(
                line_n,
                level,
                tokens,
                s
            )
        return line

    def _lines_process(self):
        """ Заполняет self.lines из файла """
        self.file = open(self.file_name, "rt")
        line_n = 1
        for raw_line in self.file.readlines():
            line = self._get_line(line_n, raw_line)
            if line:
                self.lines.append(line)

            line_n += 1
        self.file.close()

    def _block_process(self):
        """ Обрабатывает self.lines и где надо преобразовывает их в блоки"""
        cur_block = self.block = Block(None, Line(-1, -1, [Token(-1, -1, "__main")], "__main"))
        cur_iter = iter(self.lines)  # type: Iterator[Line]
        next_iter = iter(self.lines)  # type: Iterator[Line]
        next(next_iter)
        for (cur_line, next_line) in zip(cur_iter, next_iter):  # type: Line
            nl = next_line.level
            cl = cur_line.level
            if cl == nl:
                # level eq
                cur_block.push(cur_line)
            elif cl + 1 == nl:
                # level up
                child_block = Block(cur_block, cur_line)
                cur_block.push(child_block)
                cur_block = child_block
            elif cl > nl:
                # level down
                cur_block.push(cur_line)
                for i in range(cl - nl):
                    cur_block = cur_block.parent
            elif cl + 1 < nl:
                # level up more then 2
                raise LexerBlockLevelErrorException(cur_line, next_line)

    def _create_default_namespace(self):
        """ Создаёт первичный NameSpace"""
        ns = NameSpace(None)
        ns.functions_push(builtin_functions)
        self.namespaces.append(ns)

    def old_line_compile(self) -> List[Tuple[List[ByteCode], Line]]:
        """ Старая версия итоговой компиляции для одного уровня вложенности """
        bytecode = []
        for line in self.lines:
            ns = self.namespaces[-1]
            func = ns.get_func_by_token(line.func_token)
            if func.builtin:
                #  Builtin NoBlock function
                if BrFunctionType.NO_BLOCK == func.type:
                    variables = func.check_args(line.params)
                    code = func.compile(variables)
                    bytecode.append((code, line))
                #  Builtin Block Function
                elif BrFunctionType.BLOCK == func.type:
                    pass
            else:
                pass
        return bytecode

    def compile(self) -> List[Tuple[List[ByteCode], Line]]:
        pass


if __name__ == "__main__":
    compiler = BfCompiler('br_files/test_block.br')
    print("==== LINES: ====")
    for line in compiler.lines:
        print(line)

    print(compiler.block)

    print(
        "\n".join(
            compiler.block.debug_print()
        )
    )

    # bytecode = compiler.compile()
    # print()
    # print("==== BYTECODE: ====")
    # for code, line in bytecode:
    #     for act in code:
    #         print(act, end=" ")
    #     print()
    #     print(line)
    #     print("------")
    #
    # print()
    # print("==== BRAINFUCK ====")
    # for code, line in bytecode:
    #     for act in code:
    #         print(act.compile(), end="")
    #     print()
    # print()

