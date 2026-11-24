"""Authoritative national event fabric and compatibility adapters.

Only ``authority.py`` implements event publish/drain semantics. All historical
event stacks reach it through narrow adapters in ``adapters.py`` so that legacy
call sites keep their observable behavior while sharing one durable substrate.
"""
