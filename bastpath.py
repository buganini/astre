from enum import Enum
from parsimonious.nodes import NodeVisitor
from parser import parse

class Entities(list):
    def __repr__(self):
        return f"{{{', '.join([x.__repr__() for x in self])}}}"
class MatchMode(Enum):
    EXACT = 0
    STARTSWITH = 1
    ENDSWITH = 2
    CONTAINS = 3
    REGEX = 4
class Entity:
    def __init__(self, desc, mode: MatchMode, negate):
        self.desc = desc
        self.mode = mode
        self.negate = negate

    def __repr__(self):
        neg = ["","!"][self.negate]
        desc = [self.desc,"*"][self.desc is None]
        return f"{neg}{desc}"

class Expr:
    def __init__(self, keys, op, values):
        self.keys = keys
        self.op = op
        self.values = values

    def __repr__(self):
        keyconds = []
        if len(self.keys)==1 and self.keys[0].mode==MatchMode.EXACT:
            if self.keys[0].desc is None:
                tag = "*"
            else:
                tag = self.keys[0].desc
        else:
            tag = "*"
            for k in self.keys:
                if k.mode == MatchMode.EXACT:
                    neg = ("","!")[k.negate]
                    keyconds.append(f'name(){neg}="{k.desc}"')
                elif k.mode == MatchMode.STARTSWITH:
                    cond = f'starts-with(name(), "{k.desc}")'
                    if k.negate:
                        cond = f"not({cond})"
                    keyconds.append(cond)
                elif k.mode == MatchMode.ENDSWITH:
                    cond = f'ends-with(name(), "{k.desc}")'
                    if k.negate:
                        cond = f"not({cond})"
                    keyconds.append(cond)
                elif k.mode == MatchMode.CONTAINS:
                    cond = f'contains(name(), "{k.desc}")'
                    if k.negate:
                        cond = f"not({cond})"
                    keyconds.append(cond)
                elif k.mode == MatchMode.REGEX:
                    if k.desc[1]:
                        flags = f', "{k.desc[1]}"'
                    else:
                        flags = ""
                    cond = f'matches(name(), "{k.desc[0]}"{flags})'
                    if k.negate:
                        cond = f"not({cond})"
                    keyconds.append(cond)

        valconds = []
        if self.values:
            for v in self.values:
                if v.mode == MatchMode.EXACT:
                    neg = ("","!")[v.negate]
                    valconds.append(f'string(.){neg}="{v.desc}"')
                elif v.mode == MatchMode.STARTSWITH:
                    cond = f'starts-with(string(.), "{v.desc}")'
                    if v.negate:
                        cond = f"not({cond})"
                    valconds.append(cond)
                elif v.mode == MatchMode.ENDSWITH:
                    cond = f'ends-with(string(.), "{v.desc}")'
                    if v.negate:
                        cond = f"not({cond})"
                    valconds.append(cond)
                elif v.mode == MatchMode.CONTAINS:
                    cond = f'contains(string(.), "{v.desc}")'
                    if v.negate:
                        cond = f"not({cond})"
                    valconds.append(cond)
                elif v.mode == MatchMode.REGEX:
                    if v.desc[1]:
                        flags = f', "{v.desc[1]}"'
                    else:
                        flags = ""
                    cond = f'matches(string(.), "{v.desc[0]}"{flags})'
                    if v.negate:
                        cond = f"not({cond})"
                    valconds.append(cond)

        andconds = []
        if keyconds:
            andconds.append(f"({' or '.join(keyconds)})")
        if valconds:
            andconds.append(f"({' or '.join(valconds)})")

        if andconds:
            cond = f"[({' and '.join(andconds)})]"
        else:
            cond = ""
        return f"{tag}{cond}"

class XPathTransformer(NodeVisitor):
    PROMOTES = ["!"]

    def visit_Selector(self, node, visited_children):
        # print("!Selector", node, "=>", visited_children)
        ret = ["//", visited_children[0]]
        for c in visited_children[1]:
            if c[0]: # direct
                ret.append("/")
            else:
                ret.append("//")
            ret.append(c[1])
        return "".join([str(x) for x in ret])

    def visit_Attr(self, node, visited_children):
        # print("!Attr", node, "=>", visited_children)
        return visited_children[0]

    def visit_AttrKey(self, node, visited_children):
        # print("!AttrKey", node, "=>", visited_children)
        entities = visited_children[0]
        return Expr(entities, None, None)

    def visit_AttrKeyValue(self, node, visited_children):
        # print("!AttrKeyValue", node, "=>", visited_children)
        return Expr(visited_children[0], visited_children[1], visited_children[2])

    def visit_CHILDOP(self, node, visited_children):
        return visited_children[0]

    def visit_DIROP(self, node, visited_children):
        return True

    def visit_INDIROP(self, node, visited_children):
        return False

    def visit_COMPARATOR(self, node, visited_children):
        return node.text

    def visit_Entities(self, node, visited_children):
        # print("!Entities", node, "=>", visited_children)
        ret = [visited_children[0]]
        for c in visited_children[1]:
            ret.append(c[1])
        if len(ret)>1 and any([c.desc is None for c in ret]):
            raise SyntaxError("Wildcard in tags list")
        return Entities(ret)

    def visit_COMMA(self, node, visited_children):
        return "COMMA"

    def visit_Entity(self, node, visited_children):
        # print("!Entity", node, "=>", visited_children)
        ret = visited_children[1][0]
        if visited_children[0] == "!":
            if ret.desc is None:
                raise SyntaxError("Cannot negate wildcard")
            ret.negate = True
        return ret

    def visit_Identifier(self, node, visited_children):
        # print("!Identifier", dir(node))
        if node.children[0].text and node.children[2]:
            mode = MatchMode.CONTAINS
        elif node.children[0].text:
            mode = MatchMode.ENDSWITH
        elif node.children[2].text:
            mode = MatchMode.STARTSWITH
        else:
            mode = MatchMode.EXACT
        return Entity(node.children[1].text, mode, False)

    def visit_NOT(self, node, visited_children):
        return "!"

    def visit_String(self, node, visited_children):
        # print("!String", node, "=>", visited_children)
        if node.children[0].text and node.children[2]:
            mode = MatchMode.CONTAINS
        elif node.children[0].text:
            mode = MatchMode.ENDSWITH
        elif node.children[2].text:
            mode = MatchMode.STARTSWITH
        else:
            mode = MatchMode.EXACT
        return Entity(node.text.decode('string_escape'), mode, False)

    def visit_Wildcard(self, node, visited_children):
        return Entity(None, MatchMode.EXACT, False)

    def visit_Regex(self, node, visited_children):
        return Entity((node.children[0].text[1:-1], node.children[1].text), MatchMode.REGEX, False)

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        # return node
        if len(visited_children) == 1 and visited_children[0] in self.PROMOTES:
            return visited_children[0]
        return visited_children or node

class Bastpath:
    def __init__(self, selector):
        self.visitor = XPathTransformer()
        self.ast = parse(selector)

    def __str__(self):
        return self.ast.__str__()

    def toXPath(self):
        return self.visitor.visit(self.ast)

if __name__=="__main__":
    errors = [
        "a,*",
    ]
    for sel in errors:
        ok = True
        try:
            Bastpath(sel).toXPath()
            ok = False
        except:
            pass
        if not ok:
            print("Should be error", sel)

    tests = [
        [
            "a",
            ""
        ],
        [
            "*",
            ""
        ],
        [
            "a=b",
            ""
        ],
        [
            "a..=b",
            ""
        ],
        [
            "..a=b",
            ""
        ],
        [
            "..a..,b=c",
            ""
        ],
        [
            "/x/i,b=c",
            ""
        ],
        [
            "a=..b",
            ""
        ],
        [
            "a=b..",
            ""
        ],
        [
            "a=..b..",
            ""
        ],
        [
            "!a=b",
            ""
        ],
        [
            "a,b=c",
            ""
        ],
        [
            "a b c",
            ""
        ],
        [
            "a>b > c",
            ""
        ],
        [
            "a b>b,c,!d, e",
            ""
        ],
        [
            "a b=/x/",
            ""
        ],
    ]
    for sel, xpath in tests:
        b = Bastpath(sel)
        print(sel)
        print(b.toXPath())
        print()
