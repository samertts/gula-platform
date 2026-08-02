"""Unit tests for the android-consistency and db-migrations validation engine validators."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts import enterprise_validation_engine as eve


class TestAndroidConsistency:
    def test_consistent_release_passes(self):
        result = eve._validator_android_consistency()
        assert result["status"] == "pass"
        assert "1.0.0-RC2" in result["detail"]

    def test_version_name_mismatch_detected(self, tmp_path, monkeypatch):
        mobile = tmp_path / "mobile"
        mobile.mkdir()
        (mobile / "version.json").write_text(
            json.dumps({"android": {"versionName": "9.9.9", "versionCode": 42}})
        )
        android = mobile / "android" / "app"
        android.mkdir(parents=True)
        (android / "build.gradle.kts").write_text(
            'versionCode = 1\nversionName = "1.0.0"\n'
        )
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "mobile-android.yml").write_text("on: push")
        gradlew = mobile / "android" / "gradlew"
        gradlew.write_text("#!/bin/bash")

        monkeypatch.setattr(eve, "REPO_ROOT", tmp_path)
        result = eve._validator_android_consistency()
        assert result["status"] == "fail"
        assert "versionName mismatch" in result["detail"]
        assert "versionCode mismatch" in result["detail"]

    def test_missing_workflow_detected(self, tmp_path, monkeypatch):
        mobile = tmp_path / "mobile"
        mobile.mkdir()
        (mobile / "version.json").write_text(
            json.dumps({"android": {"versionName": "1.0.0", "versionCode": 1}})
        )
        android = mobile / "android" / "app"
        android.mkdir(parents=True)
        (android / "build.gradle.kts").write_text(
            'versionCode = 1\nversionName = "1.0.0"\n'
        )
        gradlew = mobile / "android" / "gradlew"
        gradlew.write_text("#!/bin/bash")

        monkeypatch.setattr(eve, "REPO_ROOT", tmp_path)
        result = eve._validator_android_consistency()
        assert result["status"] == "fail"
        assert "mobile-android.yml" in result["detail"]

    def test_missing_version_json_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr(eve, "REPO_ROOT", tmp_path)
        assert eve._validator_android_consistency()["status"] == "fail"


class TestDbMigrations:
    def test_real_migration_chain_passes(self):
        result = eve._validator_db_migrations()
        assert result["status"] == "pass"
        assert "single root" in result["detail"]

    def test_duplicate_revisions_detected(self, tmp_path, monkeypatch):
        versions = tmp_path / "backend" / "migrations" / "versions"
        versions.mkdir(parents=True)
        (versions / "m_a.py").write_text('revision = "0001"\ndown_revision = None\n')
        (versions / "m_b.py").write_text('revision = "0002"\ndown_revision = "0001"\n')
        (versions / "m_c.py").write_text('revision = "0001"\ndown_revision = "0002"\n')
        monkeypatch.setattr(eve, "REPO_ROOT", tmp_path)
        result = eve._validator_db_migrations()
        assert result["status"] == "fail"
        assert "duplicate revision ids" in result["detail"]

    def test_dangling_down_revision_detected(self, tmp_path, monkeypatch):
        versions = tmp_path / "backend" / "migrations" / "versions"
        versions.mkdir(parents=True)
        (versions / "m_1.py").write_text('revision = "0001"\ndown_revision = None\n')
        (versions / "m_2.py").write_text('revision = "0002"\ndown_revision = "does-not-exist"\n')
        monkeypatch.setattr(eve, "REPO_ROOT", tmp_path)
        result = eve._validator_db_migrations()
        assert result["status"] == "fail"
        assert "dangling down_revision" in result["detail"]

    def test_missing_versions_dir_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr(eve, "REPO_ROOT", tmp_path)
        assert eve._validator_db_migrations()["status"] == "fail"

    def test_typed_annotation_style_migrations_parsed(self, tmp_path, monkeypatch):
        versions = tmp_path / "backend" / "migrations" / "versions"
        versions.mkdir(parents=True)
        (versions / "m_1.py").write_text('revision: str = "0001"\ndown_revision: str | None = None\n')
        (versions / "m_2.py").write_text(
            'revision: str = "0002"\ndown_revision: str | None = "0001"\n'
        )
        monkeypatch.setattr(eve, "REPO_ROOT", tmp_path)
        result = eve._validator_db_migrations()
        assert result["status"] == "pass", result["detail"]
        assert "2 migrations" in result["detail"]
