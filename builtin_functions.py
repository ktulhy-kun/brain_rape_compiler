import sys
import traceback
from typing import Dict

from br_exceptions.parser import *
from br_lexer import Token, Expression
from br_parser import Function, Argument, FunctionLifeTime, FunctionType, NameSpace, \
    Variable
from br_types import IntBrType, IdentifierBrType, BrTypeBrType, \
    FunctionLifeTimeBrType, AddressBrType
from bytecode import ByteCode as B


class _Nope(Function):
    def compile(self, context: 'Context') -> List[B]:
        return [
            B("#", "Nope func")
        ]

nope = _Nope(
    'nope',
    [],
    FunctionType.NO_BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


class _Add(Function):
    def compile(self, context: 'Context') -> List[B]:
        addr = context.vars['addr'].value
        value = context.vars['value'].value
        return [
            B(">", addr),
            B("+", value),
            B("<", addr)
        ]

add = _Add(
    '_add',
    [
        Argument('addr', AddressBrType),
        Argument('value', IntBrType)
    ],
    FunctionType.NO_BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


class _Mov(Function):
    def compile(self, context: 'Context') -> List[B]:
        to_addr = context.vars['to_addr'].value
        from_addr = context.vars['from_addr'].value
        return [
            B(">", from_addr - 0),  # Move to from_addr
            B("[", 0),  # While *from_addr not null, do
            B("-", 1),  # *from_addr -= 1
            B(">", to_addr - from_addr),  # go to to_addr
            B("+", 1),  # *to_addr += 1
            B(">", from_addr - to_addr),  # go to from_addr
            B("]", 0),  # if *from_addr == null then end
            B(">", 0 - from_addr)  # move to 0
        ]

mov = _Mov(
    '_mov',
    [
        Argument('to_addr', AddressBrType),
        Argument('from_addr', AddressBrType)
    ],
    FunctionType.NO_BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


class _Mov2(Function):
    def compile(self, context: 'Context') -> List[B]:
        to1_addr = context.vars['to1_addr'].value
        to2_addr = context.vars['to2_addr'].value
        from_addr = context.vars['from_addr'].value
        return [
            B(">", from_addr - 0),  # Move to from_addr
            B("["),  # While *from_addr not null, do
            B("-", 1),  # *from_addr -= 1
            B(">", to1_addr - from_addr),  # go to to1_addr
            B("+", 1),  # *to1_addr += 1
            B(">", to2_addr - to1_addr),  # goto to2_addr
            B("+", 1),  # *to2_addr += 1
            B(">", from_addr - to2_addr),  # go to from_addr
            B("]"),  # if *from_addr == null then end
            B(">", 0 - from_addr)  # move to 0
        ]

mov2 = _Mov2(
    '_mov2',
    [
        Argument('to1_addr', AddressBrType),
        Argument('to2_addr', AddressBrType),
        Argument('from_addr', AddressBrType)
    ],
    FunctionType.NO_BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


class _Null(Function):
    def compile(self, context: 'Context') -> List[B]:
        addr = context.vars['addr'].value
        return [
            B(">", addr - 0),   # goto addr
            B("["),   # [
            B("-", 1),     # -
            B("]"),  # ]
            B(">", 0 - addr)   # goto 0
        ]

null = _Null(
    '_null',
    [
        Argument('addr', AddressBrType)
    ],
    FunctionType.NO_BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


class _Print(Function):
    def compile(self, context: 'Context') -> List[B]:
        addr = context.vars['addr'].value
        return [
            B(">", addr - 0),    # goto addr
            B("."),           # print from addr
            B(">", 0 - addr)     # goto 0
        ]

_print = _Print(
    '_print',
    [
        Argument('addr', AddressBrType)
    ],
    FunctionType.NO_BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


class _Read(Function):
    def compile(self, context: 'Context') -> List[B]:
        addr = context.vars['addr'].value
        return [
            B(">", addr - 0),
            B(","),
            B(">", 0 - addr)
        ]


_read = _Read(
    '_read',
    [
        Argument('addr', AddressBrType)
    ],
    FunctionType.NO_BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


class _Macro(Function):
    def check_args(self, context: 'Context') -> Dict[str, Variable]:
        arg_tokens = context.expr.args
        variables = {}
        if len(arg_tokens) < 2:
            raise ParserArgumentCheckLenException(self, arg_tokens, 2)
        if len(arg_tokens) % 2:
            raise ParserArgumentCheckLenException(self, arg_tokens, len(arg_tokens) + 1)

        params_iter = iter(arg_tokens)
        try:
            variables['lifetime'] = FunctionLifeTimeBrType(next(params_iter))
            variables['name'] = IdentifierBrType(next(params_iter))
            variables['arguments'] = []

            try:
                while True:
                    arg_type = BrTypeBrType(next(params_iter)).value
                    arg_name = IdentifierBrType(next(params_iter)).value
                    variables['arguments'].append(
                        Argument(arg_name, arg_type)
                    )

            except StopIteration:
                pass
        except Exception as e:
            traceback.print_exception(*sys.exc_info())
            raise ParserArgumentCheckTypeException(
                self,
                arg_tokens,
                exc=e
            )

        return variables

    def compile_block(self, context: 'Context') -> List[B]:
        function_name = context.vars['name'].value
        arguments = context.vars['arguments']  # type: List[Argument]
        lifetime = context.vars['lifetime'].value
        # Because variables['arguments'] List[Argument], not Variable

        block_inside = context.expr.block_lines
        func = Function(
                function_name,
                arguments,
                FunctionType.NO_BLOCK,
                lifetime,
                source=block_inside,
                code=block_inside,
            )

        context.ns.symbol_lifetime_push(lifetime, func)

        return [
            B(B.NONE,
              "Add function `{}` to current namespace".format(function_name)
              ),
        ]

_macro = _Macro(
    "macro",
    [],  # because custom check_args
    FunctionType.BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


class _MacroBlock(_Macro):
    def compile_block(self, context: 'Context') -> List[B]:
        function_name = context.vars['name'].value
        arguments = context.vars['arguments']  # type: List[Argument]
        lifetime = context.vars['lifetime'].value

        code = [[]]

        block_inside = context.expr.block_lines

        for expr in block_inside:  # type: Expression
            if str(expr.func_token) == 'code':
                code.append([])
            else:
                code[-1].append(expr)

        func = Function(
                function_name,
                arguments,
                FunctionType.BLOCK,
                lifetime,
                source=block_inside,
                code=code,
            )

        context.ns.symbol_lifetime_push(lifetime, func)

        return [
            B(B.NONE,
              "Add macro function `{}` to current namespace".format(function_name)
              ),
        ]


_macroblock = _MacroBlock(
    "macroblock",
    [],  # because custom check_args
    FunctionType.BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)


def _get_first_empty(busy: list) -> int:
    busy = sorted(busy)
    for i, v in zip(range(len(busy)), busy):
        if i != v:
            return i
    return len(busy)


class _Reg(Function):
    def compile(self, context: 'Context') -> List[B]:
        register_name = context.vars['name'].value
        busy = set()
        vars = context.ch_ns.get_vars()
        for var in vars:
            if isinstance(var.value_type, AddressBrType):
                busy.add(var.value)
        empty = _get_first_empty(sorted(list(busy)))
        context.ns.symbol_push(
            Variable(register_name, AddressBrType(None, value=empty))
        )
        return [
            B("#",
              "Added new variable `{}` "
              "with address `{}` to local namespace".format(
                  register_name,
                  empty
              )
              )
        ]


_reg = _Reg(
    'reg',
    [
        Argument('name', IdentifierBrType)
    ],
    FunctionType.NO_BLOCK,
    FunctionLifeTime.GLOBAL,
    builtin=True
)

builtin_functions = [
    nope,
    add,
    mov,
    mov2,
    null,
    _print,
    _read,
    _macro,
    _reg,
    _macroblock
]
