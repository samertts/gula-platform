from __future__ import annotations

from typing import Any

from app.engineering.generators.base import BaseGenerator, GenerateResult


class MermaidGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        diagram_type = kwargs.get("type", "flowchart")
        title = kwargs.get("title", "System Architecture")
        components = kwargs.get("components", [])
        relations = kwargs.get("relations", [])

        if diagram_type == "flowchart":
            content = self._flowchart(title, components, relations)
        elif diagram_type == "sequence":
            content = self._sequence(title, components, relations)
        elif diagram_type == "class":
            content = self._class_diagram(title, components)
        elif diagram_type == "c4":
            content = self._c4(title, components, relations)
        else:
            content = self._flowchart(title, components, relations)

        self._write(f"diagrams/{title.lower().replace(' ', '_')}.mmd", content)
        return self._result

    def _flowchart(self, title: str, components: list, relations: list) -> str:
        lines = [f"%% {title}", "flowchart TD"]
        for c in components:
            name = c.get("name", "Component")
            lines.append(f"    {name}[{name}]")
        for r in relations:
            src = r.get("from", "A")
            dst = r.get("to", "B")
            label = r.get("label", "")
            arrow = r.get("arrow", "-->")
            if label:
                lines.append(f"    {src} {arrow}|{label}| {dst}")
            else:
                lines.append(f"    {src} {arrow} {dst}")
        return "\n".join(lines) + "\n"

    def _sequence(self, title: str, components: list, relations: list) -> str:
        lines = [f"%% {title}", "sequenceDiagram"]
        for c in components:
            name = c.get("name", "Actor")
            lines.append(f"    participant {name}")
        for r in relations:
            src = r.get("from", "A")
            dst = r.get("to", "B")
            label = r.get("label", "")
            lines.append(f"    {src}->>{dst}: {label}")
        return "\n".join(lines) + "\n"

    def _class_diagram(self, title: str, components: list) -> str:
        lines = [f"%% {title}", "classDiagram"]
        for c in components:
            name = c.get("name", "Class")
            methods = c.get("methods", [])
            fields = c.get("fields", [])
            lines.append(f"    class {name}{{")
            for f in fields:
                lines.append(f"        +{f}")
            for m in methods:
                lines.append(f"        +{m}()")
            lines.append("    }")
        return "\n".join(lines) + "\n"

    def _c4(self, title: str, components: list, relations: list) -> str:
        lines = [f"%% {title} (C4)", "C4Context"]
        lines.append(f'    title("{title}")')
        for c in components:
            name = c.get("name", "System")
            boundary = c.get("boundary", "")
            if boundary:
                lines.append(f"    {boundary}({name}, {name})")
        for r in relations:
            src = r.get("from", "A")
            dst = r.get("to", "B")
            label = r.get("label", "")
            lines.append(f'    {src} --> {dst} : "{label}"')
        lines.append("@enduml")
        return "\n".join(lines) + "\n"


class PlantUMLGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        title = kwargs.get("title", "Architecture")
        components = kwargs.get("components", [])
        relations = kwargs.get("relations", [])

        lines = ["@startuml", f"title {title}", "skinparam componentStyle rectangle", ""]
        for c in components:
            name = c.get("name", "Component")
            stereotype = c.get("stereotype", "")
            if stereotype:
                lines.append(f"component {name} <<{stereotype}>>")
            else:
                lines.append(f"component {name}")
        lines.append("")
        for r in relations:
            src = r.get("from", "A")
            dst = r.get("to", "B")
            label = r.get("label", "")
            arrow = r.get("arrow", "-->")
            if label:
                lines.append(f"{src} {arrow} {dst} : {label}")
            else:
                lines.append(f"{src} {arrow} {dst}")
        lines.append("")
        lines.append("@enduml")

        self._write(f"diagrams/{title.lower().replace(' ', '_')}.puml", "\n".join(lines) + "\n")
        return self._result
