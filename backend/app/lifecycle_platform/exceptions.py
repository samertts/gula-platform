class LifecyclePlatformError(Exception):
    ...


class ComponentNotFoundError(LifecyclePlatformError):
    def __str__(self) -> str:
        return "Component not found in registry"


class ReleaseNotFoundError(LifecyclePlatformError):
    def __str__(self) -> str:
        return "Release not found"


class CompatibilityEntryNotFoundError(LifecyclePlatformError):
    def __str__(self) -> str:
        return "Compatibility entry not found"


class UpgradePathNotFoundError(LifecyclePlatformError):
    def __str__(self) -> str:
        return "Upgrade path not found"


class DeprecationNoticeNotFoundError(LifecyclePlatformError):
    def __str__(self) -> str:
        return "Deprecation notice not found"


class VersionConflictError(LifecyclePlatformError):
    def __str__(self) -> str:
        return "Component version conflict detected"
