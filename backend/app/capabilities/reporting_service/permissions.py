from __future__ import annotations

from enum import Enum


class Reporting_servicePermission(Enum):
    REPORT.READ = "reporting_service:report.read"
    REPORT.CREATE = "reporting_service:report.create"
    REPORT.SCHEDULE = "reporting_service:report.schedule"
    REPORT.ADMIN = "reporting_service:report.admin"

    def describe(self) -> str:
        descriptions = {        "reporting_service:report.read": "Report.Read",
                "reporting_service:report.create": "Report.Create",
                "reporting_service:report.schedule": "Report.Schedule",
                "reporting_service:report.admin": "Report.Admin"}
        return descriptions.get(self, self.value)
