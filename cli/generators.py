import os
import re
from datetime import datetime


def _read_template(name: str) -> str:
    try:
        from importlib.resources import files as _files

        pkg = _files("cli") / "templates" / name
        if pkg.is_file():
            return pkg.read_text(encoding="utf-8")
    except Exception:
        pass
    tmpl_dir = os.path.join(os.path.dirname(__file__), "templates")
    tmpl_path = os.path.join(tmpl_dir, name)
    with open(tmpl_path, encoding="utf-8") as fh:
        return fh.read()


def _jinja_render(template: str, context: dict) -> str:
    def _replace_var(match):
        parts = match.group(1).strip().split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, "")
            else:
                try:
                    value = getattr(value, part, "")
                except Exception:
                    return ""
        return str(value) if value is not None else ""

    def _replace_for(match):
        body = match.group(2)
        var_name = match.group(1)
        items = context.get(var_name, [])
        parts = []
        for item in items:
            ctx = dict(context)
            if isinstance(item, dict):
                ctx.update(item)
            else:
                ctx["_item"] = item
            parts.append(_simple_replace(body, ctx))
        return "".join(parts)

    result = template
    result = re.sub(
        r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
        _replace_for,
        result,
        flags=re.DOTALL,
    )
    result = re.sub(r"\{\{\s*([^}]+)\s*\}\}", _replace_var, result)
    return result


def _simple_replace(text: str, ctx: dict) -> str:
    def _replace_var(match):
        parts = match.group(1).strip().split(".")
        value = ctx
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, "")
            else:
                try:
                    value = getattr(value, part, "")
                except Exception:
                    return ""
        return str(value) if value is not None else ""

    return re.sub(r"\{\{\s*([^}]+)\s*\}\}", _replace_var, text)


def _to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _to_pascal(name: str) -> str:
    return "".join(word.capitalize() for word in re.split(r"[_\- ]", name))


def _to_plural(name: str) -> str:
    s = _to_snake(name)
    if s.endswith("s"):
        return s
    if s.endswith("y"):
        return s[:-1] + "ies"
    return s + "s"


def _field_defs(fields: list[str]) -> list[dict]:
    parsed = []
    for f in fields:
        if ":" in f:
            name, typ = f.split(":", 1)
        else:
            name = f
            typ = "String(255)"
        parsed.append({"name": name.strip(), "type": typ.strip()})
    if not parsed:
        parsed.append({"name": "name", "type": "String(200)"})
    return parsed


class RouteGenerator:
    def generate(self, name: str, output_dir: str = ".") -> str:
        snake = _to_snake(name)
        cls_name = _to_pascal(name)
        context = {
            "name": snake,
            "class_name": cls_name,
            "plural": _to_plural(name),
            "prefix": _to_plural(name),
            "tag": snake.replace("_", " ").title(),
            "model_import": snake,
            "year": datetime.now().year,
        }
        template = _read_template("route.py.tpl")
        code = _jinja_render(template, context)
        path = os.path.join(output_dir, f"{snake}.py")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
        return path


class ModelGenerator:
    def generate(self, name: str, fields: list[str], output_dir: str = ".") -> str:
        snake = _to_snake(name)
        cls_name = _to_pascal(name)
        context = {
            "name": snake,
            "class_name": cls_name,
            "table_name": _to_plural(name),
            "fields": _field_defs(fields),
        }
        template = _read_template("model.py.tpl")
        code = _jinja_render(template, context)
        path = os.path.join(output_dir, f"{snake}.py")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
        return path


class ServiceGenerator:
    def generate(self, name: str, output_dir: str = ".") -> str:
        snake = _to_snake(name)
        cls_name = _to_pascal(name)
        context = {
            "name": snake,
            "class_name": cls_name,
            "model_import": snake,
        }
        template = _read_template("service.py.tpl")
        code = _jinja_render(template, context)
        path = os.path.join(output_dir, f"{snake}_service.py")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
        return path


class FHIRProfileGenerator:
    def generate(self, name: str, output_dir: str = ".") -> str:
        snake = _to_snake(name)
        cls_name = _to_pascal(name)
        context = {
            "name": snake,
            "class_name": cls_name,
            "profile_id": snake,
            "title": name.replace("_", " ").title(),
            "description": f"GULA {cls_name} FHIR profile",
            "base_type": "Patient" if "patient" in snake else "Observation",
            "base_definition": f"http://hl7.org/fhir/StructureDefinition/{'Patient' if 'patient' in snake else 'Observation'}",
        }
        template = _read_template("fhir_profile.json.tpl")
        code = _jinja_render(template, context)
        path = os.path.join(output_dir, f"{snake}.json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
        return path


class PluginGenerator:
    def generate(self, name: str, output_dir: str = ".") -> str:
        snake = _to_snake(name)
        context = {
            "name": name,
            "module_name": snake,
            "prefix": snake,
            "description": f"GULA {name} plugin",
        }
        template = _read_template("plugin.py.tpl")
        code = _jinja_render(template, context)
        path = os.path.join(output_dir, f"{snake}_plugin.py")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(code)
        return path
