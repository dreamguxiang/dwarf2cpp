import functools

from .models import Attribute, Function, Namespace, Object, Template


def do_ns_chain(ns: Namespace | None) -> list[Namespace]:
    chain = []
    while ns is not None:
        chain.append(ns)
        ns = ns.parent
    return list(reversed(chain))


def do_ns_actions(prev: list[Namespace], curr: list[Namespace]):
    i = 0
    while i < len(prev) and i < len(curr):
        if (prev[i].name, prev[i].is_inline) != (curr[i].name, curr[i].is_inline):
            break
        i += 1

    actions = []

    for n in reversed(prev[i:]):
        actions.append({"kind": "close", "namespace": n})

    for n in curr[i:]:
        actions.append({"kind": "open", "namespace": n})

    return actions


@functools.cache
def do_insert_name(tp: str | tuple[str, str], name: str):
    if isinstance(tp, tuple):
        if not name:
            return "".join(tp)

        if tp[0].endswith("*") and tp[1].startswith(")"):  # do not add space if pointer to (member) function
            return f"{tp[0]}{name}{tp[1]}"

        return f"{tp[0]} {name}{tp[1]}"

    if not name:
        return tp

    return f"{tp} {name}"


def do_grouped_member_sections(members: dict[int, list[Object]]) -> list[list[list[Object]]]:
    items = _flatten_members(members)

    virtual_functions = []
    data_members = []
    static_members = []
    other_functions = []
    other_declarations = []

    for item in items:
        obj = item[2]
        subject = _category_subject(obj)

        if _is_virtual_function(subject):
            virtual_functions.append(item)
        elif isinstance(subject, Attribute) and not subject.is_static:
            data_members.append(item)
        elif getattr(subject, "is_static", False):
            static_members.append(item)
        elif isinstance(subject, Function):
            other_functions.append(item)
        else:
            other_declarations.append(item)

    sections = [
        sorted(virtual_functions, key=_virtual_sort_key),
        sorted(data_members, key=_member_sort_key),
        sorted(static_members, key=_source_sort_key),
        sorted(other_functions, key=_source_sort_key),
        sorted(other_declarations, key=_source_sort_key),
    ]

    return [[[_obj] for _, _, _obj in section] for section in sections if section]


def _flatten_members(members: dict[int, list[Object]]) -> list[tuple[int, int, Object]]:
    result = []
    for lineno, objects in sorted(members.items()):
        for index, obj in enumerate(objects):
            if not getattr(obj, "is_implicit", False):
                result.append((lineno, index, obj))

    return result


def _category_subject(obj: Object) -> Object:
    if isinstance(obj, Template) and obj.declaration is not None:
        return obj.declaration

    return obj


def _is_virtual_function(obj: Object) -> bool:
    return isinstance(obj, Function) and (obj.virtuality is not None or obj.vtable_index is not None)


def _source_sort_key(item: tuple[int, int, Object]) -> tuple[int, int]:
    return item[0], item[1]


def _virtual_sort_key(item: tuple[int, int, Object]) -> tuple[int, int, int, int]:
    obj = _category_subject(item[2])
    assert isinstance(obj, Function)

    if obj.vtable_index is not None:
        return 0, obj.vtable_index, item[0], item[1]

    return 1, item[0], item[1], 0


def _member_sort_key(item: tuple[int, int, Object]) -> tuple[int, int, int, int]:
    obj = _category_subject(item[2])
    assert isinstance(obj, Attribute)

    if obj.offset is not None:
        return 0, obj.offset, item[0], item[1]

    return 1, item[0], item[1], 0
