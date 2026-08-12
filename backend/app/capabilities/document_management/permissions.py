from __future__ import annotations

from enum import Enum


class Document_managementPermission(Enum):
    READ = "document_management:document.read"
    WRITE = "document_management:document.write"
    DELETE = "document_management:document.delete"
    SIGN = "document_management:document.sign"
    ADMIN = "document_management:document.admin"

    def describe(self) -> str:
        descriptions = {        "document_management:document.read": "Document.Read",
                "document_management:document.write": "Document.Write",
                "document_management:document.delete": "Document.Delete",
                "document_management:document.sign": "Document.Sign",
                "document_management:document.admin": "Document.Admin"}
        return descriptions.get(self, self.value)
