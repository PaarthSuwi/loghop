from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from loghop.store import init_project, project_paths
from loghop.store._integrity import (
    _derive_key,
    compute_signature,
    embed_signature,
    sign_markdown,
    verify_signature,
)


def test_integrity_key_is_persisted_private_secret(git_repo: Path) -> None:
    init_project(git_repo)

    key1 = _derive_key(git_repo)
    key2 = _derive_key(git_repo)

    key_path = project_paths(git_repo).dot / "integrity.key"
    assert key1 == key2
    assert key_path.exists()
    assert len(key1) == 32
    if os.name != "nt":
        assert stat.S_IMODE(key_path.stat().st_mode) == 0o600


def test_integrity_key_refuses_symlink(git_repo: Path) -> None:
    init_project(git_repo)
    _derive_key(git_repo)
    key_path = project_paths(git_repo).dot / "integrity.key"
    key_path.unlink()
    target = git_repo / "outside.key"
    target.write_text("0" * 64, encoding="utf-8")
    key_path.symlink_to(target)

    with pytest.raises(ValueError, match="symlinked integrity key"):
        _derive_key(git_repo)


def test_signature_round_trip_with_secret_key(git_repo: Path) -> None:
    init_project(git_repo)
    frontmatter = "id: S-001\nstatus: succeeded"

    signed = embed_signature(git_repo, frontmatter)

    assert verify_signature(git_repo, signed) is True
    assert verify_signature(git_repo, signed.replace("succeeded", "failed")) is False
    assert compute_signature(git_repo, frontmatter) in signed


def test_markdown_signature_covers_body(git_repo: Path) -> None:
    init_project(git_repo)
    markdown = "---\nid: S-001\nstatus: succeeded\n---\n\n# Session\nbody\n"

    signed = sign_markdown(git_repo, markdown)
    lines = signed.splitlines()
    end_idx = lines.index("---", 1)
    frontmatter = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])

    assert "_signature:" in signed
    assert verify_signature(git_repo, frontmatter, body) is True
    assert verify_signature(git_repo, frontmatter, body.replace("body", "tampered")) is False


def test_signature_length_and_legacy_compatibility(git_repo: Path) -> None:
    init_project(git_repo)
    frontmatter = "id: S-001\nstatus: succeeded"

    # Newly generated signatures should be 32 hex chars
    sig_32 = compute_signature(git_repo, frontmatter)
    assert len(sig_32) == 32

    # 32-character signature validation
    signed_32 = f"id: S-001\nstatus: succeeded\n_signature: {sig_32}"
    assert verify_signature(git_repo, signed_32) is True

    # 16-character legacy signature verification compatibility
    sig_16 = sig_32[:16]
    signed_16 = f"id: S-001\nstatus: succeeded\n_signature: {sig_16}"
    assert verify_signature(git_repo, signed_16) is True

    # Tampering should still fail for both lengths
    assert verify_signature(git_repo, signed_32.replace("succeeded", "failed")) is False
    assert verify_signature(git_repo, signed_16.replace("succeeded", "failed")) is False
