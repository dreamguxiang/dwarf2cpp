import unittest
from pathlib import Path
from types import SimpleNamespace

from jinja2 import Environment, FileSystemLoader


class Access:
    def __init__(self, name: str):
        self.name = name


def insert_name(tp, name):
    if isinstance(tp, tuple):
        if not name:
            return "".join(tp)
        return f"{tp[0]} {name}{tp[1]}"

    if not name:
        return tp

    return f"{tp} {name}"


def grouped_member_sections(members):
    return [[[obj] for line in sorted(members) for obj in members[line]]]


def ns_chain(ns):
    chain = []
    while ns is not None:
        chain.append(ns)
        ns = ns.parent
    return list(reversed(chain))


def ns_actions(prev, curr):
    i = 0
    while i < len(prev) and i < len(curr):
        if (prev[i].name, prev[i].is_inline) != (curr[i].name, curr[i].is_inline):
            break
        i += 1

    actions = []
    for ns in reversed(prev[i:]):
        actions.append({"kind": "close", "namespace": ns})
    for ns in curr[i:]:
        actions.append({"kind": "open", "namespace": ns})
    return actions


def make_env() -> Environment:
    template_dir = Path(__file__).parents[1] / "src" / "dwarf2cpp" / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), keep_trailing_newline=True)
    env.filters["ns_chain"] = ns_chain
    env.filters["ns_actions"] = ns_actions
    env.filters["insert_name"] = insert_name
    env.filters["grouped_member_sections"] = grouped_member_sections
    return env


def make_attribute(name: str, tp: str, offset: int = 0):
    return SimpleNamespace(
        kind="attribute",
        name=name,
        type=tp,
        default_value=None,
        alignment=None,
        bit_size=None,
        offset=offset,
        is_static=False,
        is_implicit=False,
        access=Access("PUBLIC"),
        template=None,
    )


def make_function(name: str):
    return SimpleNamespace(
        kind="function",
        name=name,
        template=None,
        noreturn=False,
        virtuality=None,
        is_explicit=False,
        is_inline=False,
        is_static=False,
        returns="void",
        parameters=[],
        is_const=False,
        is_deleted=False,
        vtable_index=None,
        is_implicit=False,
        access=Access("PUBLIC"),
    )


def make_file():
    enum = SimpleNamespace(
        kind="enum",
        name="Color",
        is_class=True,
        base="int",
        values=[("Red", 0)],
        is_implicit=False,
        parent=None,
    )
    struct = SimpleNamespace(
        kind="struct",
        name="Point",
        alignment=None,
        is_declaration=False,
        bases=[],
        members={1: [make_attribute("x", "int")]},
        byte_size=4,
        is_implicit=False,
        parent=None,
        template=None,
    )
    klass = SimpleNamespace(
        kind="class",
        name="Widget",
        alignment=None,
        is_declaration=False,
        bases=[],
        members={1: [make_function("draw")]},
        byte_size=8,
        is_implicit=False,
        parent=None,
        template=None,
    )
    return {1: [enum], 2: [struct], 3: [klass]}


class TemplateFormattingTest(unittest.TestCase):
    def test_classes_start_access_specifier_on_own_line(self):
        env = make_env()

        for grouped_members in (False, True):
            with self.subTest(grouped_members=grouped_members):
                result = env.get_template("file.jinja").render(
                    file=make_file(),
                    grouped_members=grouped_members,
                )

                self.assertIn("class Widget {\npublic:\n", result)
                self.assertNotIn("{public:", result)

    def test_top_level_declarations_are_separated_by_blank_lines(self):
        env = make_env()

        for grouped_members in (False, True):
            with self.subTest(grouped_members=grouped_members):
                result = env.get_template("file.jinja").render(
                    file=make_file(),
                    grouped_members=grouped_members,
                )

                self.assertIn("};\n\nstruct Point", result)
                self.assertIn("}; // size: 4\n\nclass Widget", result)

    def test_namespace_close_stays_on_a_new_line(self):
        env = make_env()
        ns = SimpleNamespace(name="demo", parent=None, is_inline=False)
        klass = make_file()[3][0]
        klass.parent = ns

        result = env.get_template("file.jinja").render(file={1: [klass]}, grouped_members=False)

        self.assertIn("}; // size: 8\n} // namespace demo", result)


if __name__ == "__main__":
    unittest.main()
