from __future__ import annotations

import gzip
import hashlib
import hmac
import json
import logging
import re
import zlib
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("gula.ecosystem.transformation")


class MappingRule:
    def __init__(
        self,
        field_mappings: dict[str, str] | None = None,
        value_mappings: dict[str, dict[str, Any]] | None = None,
        condition_transforms: list[dict] | None = None,
        script_transforms: list[dict] | None = None,
    ) -> None:
        self.field_mappings = field_mappings or {}
        self.value_mappings = value_mappings or {}
        self.condition_transforms = condition_transforms or []
        self.script_transforms = script_transforms or []


class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas: dict[str, dict] = {}
        self._versions: dict[str, list[dict]] = {}

    def register_schema(self, name: str, schema: dict, version: str = "1.0.0") -> dict:
        entry = {
            "name": name,
            "schema": schema,
            "version": version,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._schemas[name] = entry
        if name not in self._versions:
            self._versions[name] = []
        self._versions[name].append(entry)
        return entry

    def get_schema(self, name: str, version: str | None = None) -> dict | None:
        if version:
            for v in self._versions.get(name, []):
                if v["version"] == version:
                    return v
            return None
        return self._schemas.get(name)

    def validate_against_schema(self, data: Any, schema_name: str) -> tuple[bool, list[str]]:
        entry = self._schemas.get(schema_name)
        if not entry:
            return False, [f"Schema not found: {schema_name}"]
        errors = self._validate(data, entry["schema"])
        return len(errors) == 0, errors

    def version_schema(self, name: str, schema: dict, new_version: str) -> dict:
        if name not in self._schemas:
            raise ValueError(f"Schema not found: {name}")
        return self.register_schema(name, schema, new_version)

    def list_schemas(self) -> list[dict]:
        return [
            {"name": name, "version": entry["version"], "created_at": entry["created_at"]}
            for name, entry in self._schemas.items()
        ]

    def _validate(self, data: Any, schema: dict, path: str = "") -> list[str]:
        errors: list[str] = []
        if not isinstance(schema, dict):
            return errors

        schema_type = schema.get("type")
        if schema_type == "object" and isinstance(data, dict):
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            for field in required:
                if field not in data:
                    errors.append(f"{path}.{field}: required field missing")
            for key, value in data.items():
                if key in properties:
                    errors.extend(self._validate(value, properties[key], f"{path}.{key}"))
        elif schema_type == "array" and isinstance(data, list):
            items_schema = schema.get("items", {})
            for i, item in enumerate(data):
                errors.extend(self._validate(item, items_schema, f"{path}[{i}]"))
        elif schema_type == "string" and not isinstance(data, str):
            errors.append(f"{path}: expected string, got {type(data).__name__}")
        elif schema_type == "integer" and not isinstance(data, int):
            errors.append(f"{path}: expected integer, got {type(data).__name__}")
        elif schema_type == "number" and not isinstance(data, (int, float)):
            errors.append(f"{path}: expected number, got {type(data).__name__}")
        elif schema_type == "boolean" and not isinstance(data, bool):
            errors.append(f"{path}: expected boolean, got {type(data).__name__}")
        pattern = schema.get("pattern")
        if pattern and isinstance(data, str) and not re.match(pattern, data):
            errors.append(f"{path}: does not match pattern {pattern}")
        return errors


class ValueMapper:
    def map_values(self, source_value: Any, mapping: dict[str, Any]) -> Any:
        if isinstance(source_value, str) and source_value in mapping:
            source_value = mapping[source_value]
        return source_value

    def apply_transformations(self, value: Any, transforms: list[dict]) -> Any:
        result = value
        for transform in transforms:
            t_type = transform.get("type", "")
            if t_type == "uppercase" and isinstance(result, str):
                result = result.upper()
            elif t_type == "lowercase" and isinstance(result, str):
                result = result.lower()
            elif t_type == "trim" and isinstance(result, str):
                result = result.strip()
            elif t_type == "replace" and isinstance(result, str):
                old = transform.get("old", "")
                new = transform.get("new", "")
                result = result.replace(old, new)
            elif t_type == "regex_replace" and isinstance(result, str):
                pattern = transform.get("pattern", "")
                replacement = transform.get("replacement", "")
                result = re.sub(pattern, replacement, result)
            elif t_type == "truncate" and isinstance(result, str):
                max_len = transform.get("max_length", 255)
                result = result[:max_len]
            elif t_type == "strip_prefix" and isinstance(result, str):
                prefix = transform.get("prefix", "")
                result = result.removeprefix(prefix)
            elif t_type == "strip_suffix" and isinstance(result, str):
                suffix = transform.get("suffix", "")
                result = result.removesuffix(suffix)
            elif t_type == "default" and (result is None or result == ""):
                result = transform.get("default_value", "")
            elif t_type == "format_date":
                source_fmt = transform.get("source_format", "%Y-%m-%d")
                target_fmt = transform.get("target_format", "%Y-%m-%d")
                try:
                    parsed = datetime.strptime(str(result), source_fmt)
                    result = parsed.strftime(target_fmt)
                except (ValueError, TypeError):
                    pass
        return result


class TransformationEngine:
    def __init__(self) -> None:
        self._schema_registry = SchemaRegistry()
        self._value_mapper = ValueMapper()

    @property
    def schema_registry(self) -> SchemaRegistry:
        return self._schema_registry

    @property
    def value_mapper(self) -> ValueMapper:
        return self._value_mapper

    def transform(
        self,
        source_data: Any,
        source_format: str,
        target_format: str,
        mapping_rules: MappingRule | None = None,
    ) -> Any:
        intermediate = self._normalize(source_data, source_format)
        if mapping_rules:
            intermediate = self.map_fields(intermediate, mapping_rules)
        return self._serialize(intermediate, target_format)

    def validate(self, data: Any, schema: dict) -> tuple[bool, list[str]]:
        return (
            self._schema_registry.validate_against_schema(data, schema.get("name", ""))
            if isinstance(schema, dict) and "name" in schema
            else self._schema_validator(data, schema)
        )

    def map_fields(self, data: Any, rules: MappingRule) -> Any:
        if isinstance(data, dict):
            result = {}
            for src_field, target_field in rules.field_mappings.items():
                value = self._get_nested(data, src_field)
                if value is not None:
                    if src_field in rules.value_mappings:
                        value = self._value_mapper.map_values(
                            value, rules.value_mappings[src_field],
                        )
                    for condition in rules.condition_transforms:
                        if condition.get("source_field") == src_field:
                            value = self._apply_condition_transform(value, condition)
                    for script in rules.script_transforms:
                        if script.get("source_field") == src_field:
                            value = self._apply_script_transform(value, script)
                    self._set_nested(result, target_field, value)

            for condition in rules.condition_transforms:
                if not condition.get("source_field"):
                    self._apply_conditional_mapping(data, result, condition)

            return result
        if isinstance(data, list):
            return [self.map_fields(item, rules) for item in data]
        return data

    def _normalize(self, data: Any, fmt: str) -> Any:
        if fmt in ("json", "application/json"):
            if isinstance(data, str):
                return json.loads(data)
            return data
        if fmt in ("xml", "application/xml", "text/xml"):
            return self._xml_to_dict(data)
        if fmt in ("csv", "text/csv"):
            return self._csv_to_dict(data)
        return data

    def _serialize(self, data: Any, fmt: str) -> Any:
        if fmt in ("json", "application/json"):
            return (
                json.dumps(data, ensure_ascii=False, default=str)
                if isinstance(data, (dict, list))
                else data
            )
        if fmt in ("xml", "application/xml", "text/xml"):
            return self._dict_to_xml(data)
        if fmt in ("csv", "text/csv"):
            return self._dict_to_csv(data)
        return data

    def _get_nested(self, data: dict, path: str) -> Any:
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _set_nested(self, data: dict, path: str, value: Any) -> None:
        parts = path.split(".")
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def _apply_condition_transform(self, value: Any, condition: dict) -> Any:
        condition_type = condition.get("type", "")
        condition_value = condition.get("value")
        transform_value = condition.get("transform")

        if condition_type == "equals" and value == condition_value:
            return transform_value
        if condition_type == "not_equals" and value != condition_value:
            return transform_value
        if condition_type == "contains" and isinstance(value, str) and condition_value in value:
            return transform_value
        if (
            condition_type == "starts_with"
            and isinstance(value, str)
            and value.startswith(str(condition_value))
        ):
            return transform_value
        if (
            condition_type == "ends_with"
            and isinstance(value, str)
            and value.endswith(str(condition_value))
        ):
            return transform_value
        if condition_type == "is_empty" and not value:
            return transform_value
        if condition_type == "is_not_empty" and value:
            return transform_value
        return value

    def _apply_conditional_mapping(self, source: dict, target: dict, condition: dict) -> None:
        source_field = condition.get("source_field", "")
        target_field = condition.get("target_field", "")
        condition_type = condition.get("type", "")
        condition_value = condition.get("value")
        transform_value = condition.get("transform")
        source_value = self._get_nested(source, source_field)

        if self._evaluate_condition(source_value, condition_type, condition_value):
            if transform_value is not None:
                self._set_nested(target, target_field, transform_value)
            else:
                self._set_nested(target, target_field, source_value)

    def _evaluate_condition(self, value: Any, condition_type: str, condition_value: Any) -> bool:
        if condition_type == "equals":
            return value == condition_value
        if condition_type == "not_equals":
            return value != condition_value
        if condition_type == "contains" and isinstance(value, str):
            return condition_value in value
        if condition_type == "starts_with" and isinstance(value, str):
            return value.startswith(str(condition_value))
        if condition_type == "ends_with" and isinstance(value, str):
            return value.endswith(str(condition_value))
        if condition_type == "greater_than":
            try:
                return float(value) > float(condition_value)
            except (ValueError, TypeError):
                return False
        if condition_type == "less_than":
            try:
                return float(value) < float(condition_value)
            except (ValueError, TypeError):
                return False
        if condition_type == "is_empty":
            return not value
        if condition_type == "is_not_empty":
            return bool(value)
        return True

    def _apply_script_transform(self, value: Any, script: dict) -> Any:
        script_type = script.get("type", "")
        script_body = script.get("script", "")

        if script_type == "template":
            template = str(script_body)
            if isinstance(value, dict):
                for k, v in value.items():
                    template = template.replace(f"{{{k}}}", str(v))
            elif isinstance(value, str):
                template = template.replace("{value}", value)
            return template

        if script_type == "concat":
            parts = script.get("parts", [])
            result = ""
            for part in parts:
                if part == "{source}":
                    result += str(value)
                elif (
                    isinstance(part, str)
                    and part.startswith("{")
                    and part.endswith("}")
                    and isinstance(value, dict)
                ):
                    result += str(value.get(part[1:-1], ""))
                else:
                    result += str(part)
            return result

        if script_type == "split":
            delimiter = script.get("delimiter", ",")
            index = script.get("index", 0)
            parts = str(value).split(delimiter)
            return parts[index] if index < len(parts) else value

        if script_type == "join":
            delimiter = script.get("delimiter", ",")
            if isinstance(value, list):
                return delimiter.join(str(v) for v in value)
            return value

        if script_type == "lookup":
            mapping = script.get("mapping", {})
            return mapping.get(str(value), script.get("default", value))

        return value

    def _schema_validator(self, data: Any, schema: dict, path: str = "") -> list[str]:
        errors: list[str] = []
        if not isinstance(schema, dict):
            return errors
        schema_type = schema.get("type")
        if schema_type == "object" and isinstance(data, dict):
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            for field in required:
                if field not in data:
                    errors.append(f"{path}.{field}: required field missing")
            additional_props = schema.get("additionalProperties", True)
            if not additional_props:
                for key in data:
                    if key not in properties:
                        errors.append(f"{path}.{key}: unexpected field")
            for key, value in data.items():
                if key in properties:
                    errors.extend(self._schema_validator(value, properties[key], f"{path}.{key}"))
        elif schema_type == "array" and isinstance(data, list):
            items_schema = schema.get("items", {})
            for i, item in enumerate(data):
                errors.extend(self._schema_validator(item, items_schema, f"{path}[{i}]"))
            min_items = schema.get("minItems")
            max_items = schema.get("maxItems")
            if min_items is not None and len(data) < min_items:
                errors.append(f"{path}: minimum {min_items} items required")
            if max_items is not None and len(data) > max_items:
                errors.append(f"{path}: maximum {max_items} items allowed")
        elif schema_type == "string" and not isinstance(data, str):
            errors.append(f"{path}: expected string, got {type(data).__name__}")
        elif schema_type == "integer" and not isinstance(data, int):
            errors.append(f"{path}: expected integer, got {type(data).__name__}")
        elif schema_type == "number" and not isinstance(data, (int, float)):
            errors.append(f"{path}: expected number, got {type(data).__name__}")
        elif schema_type == "boolean" and not isinstance(data, bool):
            errors.append(f"{path}: expected boolean, got {type(data).__name__}")

        if isinstance(data, str):
            min_length = schema.get("minLength")
            max_length = schema.get("maxLength")
            if min_length is not None and len(data) < min_length:
                errors.append(f"{path}: minimum length {min_length}")
            if max_length is not None and len(data) > max_length:
                errors.append(f"{path}: maximum length {max_length}")
            pattern = schema.get("pattern")
            if pattern and not re.match(pattern, data):
                errors.append(f"{path}: does not match pattern {pattern}")

        if isinstance(data, (int, float)):
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")
            if minimum is not None and data < minimum:
                errors.append(f"{path}: less than minimum {minimum}")
            if maximum is not None and data > maximum:
                errors.append(f"{path}: greater than maximum {maximum}")

        enum = schema.get("enum")
        if enum is not None and data not in enum:
            errors.append(f"{path}: value not in enum {enum}")

        return errors

    def _xml_to_dict(self, data: Any) -> Any:
        if isinstance(data, str):
            from defusedxml.ElementTree import fromstring as safe_xml_parse

            root = safe_xml_parse(data)
            return self._element_to_dict(root)
        return data

    def _element_to_dict(self, element: Any) -> dict:
        result: dict = {}
        for child in element:
            if len(child):
                sub = self._element_to_dict(child)
                if child.tag in result:
                    existing = result[child.tag]
                    if not isinstance(existing, list):
                        result[child.tag] = [existing]
                    result[child.tag].append(sub)
                else:
                    result[child.tag] = sub
            else:
                text = child.text or ""
                if child.tag in result:
                    existing = result[child.tag]
                    if not isinstance(existing, list):
                        result[child.tag] = [existing]
                    result[child.tag].append(text)
                else:
                    result[child.tag] = text
        return result

    def _dict_to_xml(self, data: Any) -> str:
        if isinstance(data, dict):
            from xml.etree import ElementTree

            root_name = next(iter(data.keys())) if data else "root"
            root = ElementTree.Element(root_name)
            self._build_xml(root, data[root_name] if data else data)
            return ElementTree.tostring(root, encoding="unicode")
        return str(data)

    def _build_xml(self, parent: Any, data: Any) -> None:
        from xml.etree import ElementTree

        if isinstance(data, dict):
            for key, value in data.items():
                child = ElementTree.SubElement(parent, key)
                self._build_xml(child, value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        child = ElementTree.SubElement(parent, key)
                        self._build_xml(child, value)
                else:
                    child = ElementTree.SubElement(parent, "item")
                    child.text = str(item)
        else:
            parent.text = str(data)

    def _csv_to_dict(self, data: Any) -> list[dict]:
        if isinstance(data, str):
            import csv
            import io

            reader = csv.DictReader(io.StringIO(data))
            return list(reader)
        return data if isinstance(data, list) else []

    def _dict_to_csv(self, data: Any) -> str:
        import csv
        import io

        if isinstance(data, list) and data:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        if isinstance(data, dict):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(data.keys())
            writer.writerow(data.values())
            return output.getvalue()
        return str(data)


class CompressionEngine:
    @staticmethod
    def compress(data: str | bytes, algorithm: str = "gzip") -> bytes:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        if algorithm == "gzip":
            return gzip.compress(raw)
        if algorithm == "zlib":
            return zlib.compress(raw)
        if algorithm == "lz4":
            try:
                import lz4.frame

                return lz4.frame.compress(raw)
            except ImportError:
                logger.warning("lz4 not installed, falling back to gzip")
                return gzip.compress(raw)
        else:
            raise ValueError(f"unsupported compression algorithm: {algorithm}")

    @staticmethod
    def decompress(data: bytes, algorithm: str = "gzip") -> bytes:
        if algorithm == "gzip":
            return gzip.decompress(data)
        if algorithm == "zlib":
            return zlib.decompress(data)
        if algorithm == "lz4":
            try:
                import lz4.frame

                return lz4.frame.decompress(data)
            except ImportError:
                logger.warning("lz4 not installed, falling back to gzip")
                return gzip.decompress(data)
        else:
            raise ValueError(f"unsupported compression algorithm: {algorithm}")


class EncryptionEngine:
    @staticmethod
    def encrypt(data: str, key: str | bytes, algorithm: str = "AES-256") -> str:
        if algorithm == "AES-256":
            import base64

            from cryptography.fernet import Fernet

            derived_key = base64.urlsafe_b64encode(
                hashlib.sha256(key.encode() if isinstance(key, str) else key).digest(),
            )
            f = Fernet(derived_key)
            return f.encrypt(data.encode()).decode()
        if algorithm == "RSA":
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import hashes as crypto_hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives.serialization import load_pem_public_key

            public_key = load_pem_public_key(
                key.encode() if isinstance(key, str) else key, backend=default_backend(),
            )
            encrypted = public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=crypto_hashes.SHA256()),
                    algorithm=crypto_hashes.SHA256(),
                    label=None,
                ),
            )
            return encrypted.hex()
        raise ValueError(f"unsupported encryption algorithm: {algorithm}")

    @staticmethod
    def decrypt(data: str, key: str | bytes, algorithm: str = "AES-256") -> str:
        if algorithm == "AES-256":
            import base64

            from cryptography.fernet import Fernet

            derived_key = base64.urlsafe_b64encode(
                hashlib.sha256(key.encode() if isinstance(key, str) else key).digest(),
            )
            f = Fernet(derived_key)
            return f.decrypt(data.encode()).decode()
        if algorithm == "RSA":
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import hashes as crypto_hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives.serialization import load_pem_private_key

            private_key = load_pem_private_key(
                key.encode() if isinstance(key, str) else key,
                password=None,
                backend=default_backend(),
            )
            decrypted = private_key.decrypt(
                bytes.fromhex(data),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=crypto_hashes.SHA256()),
                    algorithm=crypto_hashes.SHA256(),
                    label=None,
                ),
            )
            return decrypted.decode()
        raise ValueError(f"unsupported encryption algorithm: {algorithm}")


class DigitalSignature:
    @staticmethod
    def sign(data: str, private_key: str) -> str:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes as crypto_hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        key = load_pem_private_key(private_key.encode(), password=None, backend=default_backend())
        signature = key.sign(
            data.encode(),
            padding.PKCS1v15(),
            crypto_hashes.SHA256(),
        )
        return signature.hex()

    @staticmethod
    def verify(data: str, signature: str, public_key: str) -> bool:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes as crypto_hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        try:
            key = load_pem_public_key(public_key.encode(), backend=default_backend())
            key.verify(
                bytes.fromhex(signature),
                data.encode(),
                padding.PKCS1v15(),
                crypto_hashes.SHA256(),
            )
            return True
        except Exception:
            return False


class IntegrityValidator:
    SUPPORTED_ALGORITHMS = {"sha256", "sha384", "sha512", "md5"}

    @staticmethod
    def compute_hash(data: str | bytes, algorithm: str = "sha256") -> str:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        if algorithm == "sha256":
            return hashlib.sha256(raw).hexdigest()
        if algorithm == "sha384":
            return hashlib.sha384(raw).hexdigest()
        if algorithm == "sha512":
            return hashlib.sha512(raw).hexdigest()
        if algorithm == "md5":
            return hashlib.md5(raw, usedforsecurity=False).hexdigest()
        raise ValueError(f"unsupported hash algorithm: {algorithm}")

    @staticmethod
    def validate_hash(data: str | bytes, expected_hash: str, algorithm: str = "sha256") -> bool:
        computed = IntegrityValidator.compute_hash(data, algorithm)
        return hmac.compare_digest(computed, expected_hash)
