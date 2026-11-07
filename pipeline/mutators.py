"""AST mutation operators. Every mutant changes exactly one existing line of the function.

Operators (names match contracts/question.schema.json provenance.mutation_operator):
  flip_comparison  <  <-> <=,  >  <-> >=,  == <-> !=,  in <-> not in
  off_by_one       integer constant c -> c + 1 / c - 1
  wrong_operator   + <-> -,  * -> +,  += <-> -=
  swap_and_or      and <-> or
  wrong_base_case  any of the above inside a recursive function's base case (if ...: return ...)
  wrong_return     constant in a return statement changed (True <-> False, n -> n +/- 1)
Lines are never added or removed; `generate` verifies that by diffing the printed source.
"""
import ast
import copy
from dataclasses import dataclass
from typing import Callable, Iterator

COMPARE_FLIPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.In: ast.NotIn, ast.NotIn: ast.In,
}
BINOP_SWAPS = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add}
AUG_SWAPS = {ast.Add: ast.Sub, ast.Sub: ast.Add}


@dataclass(frozen=True)
class Mutant:
    operator: str
    source: str          # full mutated function source
    line: int            # 1-indexed line that changed
    original_line: str
    mutated_line: str


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _base_case_nodes(func: ast.FunctionDef) -> set[ast.AST]:
    """Nodes inside a top-level `if ...: return ...` of a recursive function."""
    recursive = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == func.name
        for n in ast.walk(func)
    )
    if not recursive:
        return set()
    out: set[ast.AST] = set()
    for stmt in func.body:
        if isinstance(stmt, ast.If) and any(isinstance(s, ast.Return) for s in stmt.body):
            out.update(ast.walk(stmt))
    return out


def _inside(node: ast.AST, kind: type, parents: dict) -> bool:
    while node in parents:
        node = parents[node]
        if isinstance(node, kind):
            return True
    return False


def _is_divisor(node: ast.AST, parents: dict) -> bool:
    """`// 2`, `% 2`, `** 2`: changing these is not a realistic off-by-one."""
    p = parents.get(node)
    return isinstance(p, ast.BinOp) and p.right is node and isinstance(p.op, (ast.FloorDiv, ast.Mod, ast.Div, ast.Pow))


def _sites(tree: ast.Module) -> Iterator[tuple[int, str, Callable[[ast.AST], None]]]:
    """Yield (walk index, operator, mutate-in-place fn) for every mutation site."""
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
    parents = _parents(tree)
    base = _base_case_nodes(func)

    def label(node: ast.AST, default: str) -> str:
        if node in base:
            return "wrong_base_case"
        if default in ("off_by_one",) and _inside(node, ast.Return, parents):
            return "wrong_return"
        return default

    for idx, node in enumerate(ast.walk(tree)):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in COMPARE_FLIPS:
            new = COMPARE_FLIPS[type(node.ops[0])]
            yield idx, label(node, "flip_comparison"), lambda n, new=new: n.ops.__setitem__(0, new())
        elif isinstance(node, ast.BinOp) and type(node.op) in BINOP_SWAPS:
            new = BINOP_SWAPS[type(node.op)]
            yield idx, label(node, "wrong_operator"), lambda n, new=new: setattr(n, "op", new())
        elif isinstance(node, ast.AugAssign) and type(node.op) in AUG_SWAPS:
            new = AUG_SWAPS[type(node.op)]
            yield idx, label(node, "wrong_operator"), lambda n, new=new: setattr(n, "op", new())
        elif isinstance(node, ast.BoolOp):
            new = ast.Or if isinstance(node.op, ast.And) else ast.And
            yield idx, label(node, "swap_and_or"), lambda n, new=new: setattr(n, "op", new())
        elif isinstance(node, ast.Constant) and type(node.value) is bool and _inside(node, ast.Return, parents):
            yield idx, label(node, "wrong_return"), lambda n: setattr(n, "value", not n.value)
        elif isinstance(node, ast.Constant) and type(node.value) is int and not _is_divisor(node, parents):
            for delta in (1, -1):
                if node.value + delta < 0:
                    continue
                parent = parents.get(node)
                if node.value + delta == 0 and (
                    isinstance(parent, ast.UnaryOp)
                    or (isinstance(parent, ast.BinOp) and parent.right is node and isinstance(parent.op, (ast.Add, ast.Sub)))
                ):
                    continue  # "-0", "+ 0", "- 0" read as no-ops, not realistic bugs
                yield idx, label(node, "off_by_one"), lambda n, d=delta: setattr(n, "value", n.value + d)


def generate(source: str) -> list[Mutant]:
    """All single-line mutants of the one function in `source` (printed with ast.unparse)."""
    tree = ast.parse(source)
    original = ast.unparse(tree)
    orig_lines = original.split("\n")
    seen: set[str] = set()
    out: list[Mutant] = []
    for idx, operator, mutate in _sites(tree):
        clone = copy.deepcopy(tree)
        target = next(n for i, n in enumerate(ast.walk(clone)) if i == idx)
        mutate(target)
        try:
            printed = ast.unparse(clone)
        except Exception:
            continue
        lines = printed.split("\n")
        changed = [i for i, (a, b) in enumerate(zip(orig_lines, lines)) if a != b]
        if len(lines) != len(orig_lines) or len(changed) != 1 or printed in seen:
            continue
        seen.add(printed)
        i = changed[0]
        out.append(Mutant(operator, printed, i + 1, orig_lines[i], lines[i]))
    return out
