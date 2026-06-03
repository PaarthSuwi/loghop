from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProviderDetection:
    name: str
    path: str

    @property
    def installed(self) -> bool:
        return bool(self.path)


class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def detect(self, exclude_dir: Path | None = None) -> ProviderDetection:
        pass

    @abstractmethod
    def build_launch_command(
        self,
        executable: str,
        prompt: str,
        project_root: Path,
        *,
        interactive: bool = False,
    ) -> list[str]:
        pass

    @abstractmethod
    def ensure_ready(self, executable: str, project_root: Path) -> None:
        pass
