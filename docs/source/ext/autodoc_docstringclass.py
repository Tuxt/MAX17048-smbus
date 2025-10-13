import re
from typing import ClassVar, Literal

from sphinx.ext.autodoc import ALL, ClassDocumenter, ObjectMember
from sphinx.util.typing import OptionSpec


def no_docstring_members_option(arg: str | None) -> Literal["all", "repeated"] | list[str] | None:
    """Convert the :no-docstring-members: option."""
    if arg is None or arg is True:
        return "all"
    if arg is False:
        return None
    if arg == DocstringClassDocumenter.REPEATED:
        return "repeated"
    return list({stripped for x in arg.split(",") if (stripped := x.strip())})


class DocstringClassDocumenter(ClassDocumenter):
    """
    A ClassDocumenter to filter the class docstring.

    A Documenter similar to ClassDocumenter that allows you to filter
    attributes and methods described in the class docstring without
    removing them from the ``Attributes`` and ``Methods`` sections.
    """

    objtype = "docstringclass"
    directivetype = ClassDocumenter.objtype
    priority = 10 + ClassDocumenter.priority
    option_spec: ClassVar[OptionSpec] = dict(ClassDocumenter.option_spec)
    option_spec["no-docstring-members"] = no_docstring_members_option
    REPEATED = "@repeated"  # Reserved keyword

    def get_doc(self) -> list[list[str]] | None:
        doc = super().get_doc()

        filter = self.options.get("no-docstring-members", None)
        if filter == "all":
            doc = [self._filter_all(subdoc) for subdoc in doc]
        elif filter == "repeated":
            members = self.options["members"]
            members = (
                self.get_object_members(want_all=True) if members is ALL else self.get_object_members(want_all=False)
            )
            members = [member.__name__ for member in members[1] if self._is_documented(member)]
            if not members:
                return doc
            doc = [self._filter_list(subdoc, members) for subdoc in doc]
            doc = [self._extract_items(subdoc) for subdoc in doc]
        elif isinstance(filter, list):
            doc = [self._filter_list(subdoc, filter) for subdoc in doc]

        return doc

    def _filter_all(self, doc: list[str]) -> list[str]:
        """Remove 'Attributes' and 'Methods' sections from a class docstring."""
        for section in ("Attributes", "Methods"):
            if section not in doc:
                continue
            index = doc.index(section)
            while len(doc) > index and doc[index]:
                doc.pop(index)
            doc.pop(index)
        return doc

    def _filter_list(self, doc: list[str], filter: list[str]) -> list[str]:
        """
        Remove listed members (and their descriptions) from the docstring.

        Uses a regex to match field names and a flag to skip their description lines.
        """
        pattern = re.compile(rf"^({'|'.join(map(re.escape, filter))})\b")
        flag = False  # Indicate if it's deleting a field (with description)

        def check(line) -> bool:
            nonlocal flag
            if pattern.match(line):
                flag = True
                return True
            if flag and line.startswith(" "):
                return True
            flag = False
            return False

        return [line for line in doc if not check(line)]

    def _is_documented(self, member: ObjectMember) -> bool:
        """
        Return True if the member is considered documented.

        Checks inline docstrings or __doc__ different from its class.
        """
        if member.docstring:
            return True
        doc = member.object.__doc__
        try:
            return doc is not None and doc and doc != member.object.__class__.__doc__
        except Exception:
            return doc != ""

    def _extract_items(self, doc: list[str]) -> list[str]:
        """
        Extract item docstrings from class sections and store them in the Sphinx environment.

        Parses the "Attributes" and "Methods" sections of the class docstring and collects
        each item's name-docstring pair into `self.env.temp_items`. This enables later
        retrieval of class-level documentation (for example, in autodoc hooks) when
        individual members lack their own docstrings.
        """
        if hasattr(self.env, "temp_items"):
            return doc
        item = ""
        docstring = ""
        items = {}
        for section in ("Attributes", "Methods"):
            if section not in doc:
                continue
            index = doc.index(section) + 1
            while len(doc) > index and doc[index]:
                line = doc.pop(index)
                if line.startswith(" "):
                    docstring += line.strip()
                else:
                    if item and docstring:
                        items[item] = docstring
                        item = ""
                        docstring = ""
                    item = line.split(" ")[0]
        return doc


def patch_member_docstrings(app, what, name, obj, options, lines):
    if not hasattr(app.env, "temp_items"):
        return
    item_name = name.split(".")[-1]
    if item_name in app.env.temp_items:
        app.env.temp_items[item_name]
        lines.clear()
        lines.append(app.env.temp_items[item_name])


def setup(app):
    app.add_autodocumenter(DocstringClassDocumenter)
    app.connect("autodoc-process-docstring", patch_member_docstrings)
