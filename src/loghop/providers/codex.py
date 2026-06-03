import shutil
from pathlib import Path

from loghop.providers.base import BaseProvider, ProviderDetection


class CodexProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "codex"

    def detect(self, exclude_dir: Path | None = None) -> ProviderDetection:
        if exclude_dir is not None:
            from loghop.install._shim import detect_real_binary

            path = detect_real_binary(self.name, exclude_dir=exclude_dir) or ""
        else:
            path = shutil.which(self.name) or ""
        return ProviderDetection(name=self.name, path=path)

    def build_launch_command(
        self,
        executable: str,
        prompt: str,
        project_root: Path,
        *,
        interactive: bool = False,
    ) -> list[str]:
        if interactive:
            return [executable, "--", prompt]
        return [executable, "exec", "--cd", str(project_root), "--color", "never", prompt]

    def ensure_ready(self, executable: str, project_root: Path) -> None:
        pass
