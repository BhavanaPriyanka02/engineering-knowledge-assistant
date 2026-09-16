import os
import shutil
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from git import Repo

BASE_REPOSITORIES_DIR = Path(__file__).resolve().parents[2] / "repositories"
MAX_FILE_SIZE = 1024 * 1024
IGNORE_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "coverage",
    ".pytest_cache",
    ".idea",
    ".vscode",
}
SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".mjs",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".scss",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".php",
    ".sql",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".toml",
    ".ini",
}
IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
    ".ico",
    ".mp4",
    ".mov",
    ".avi",
    ".mp3",
    ".wav",
    ".flac",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".bz2",
    ".xz",
    ".rar",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".class",
    ".o",
    ".obj",
    ".pyc",
    ".pyo",
    ".jar",
    ".war",
    ".ear",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}


def validate_github_url(repo_url: str) -> str:
    if not repo_url or not isinstance(repo_url, str):
        raise ValueError("Invalid GitHub repository URL.")

    normalized_url = repo_url.strip()
    parsed = urlparse(normalized_url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Invalid GitHub repository URL.")

    if parsed.netloc.lower() != "github.com":
        raise ValueError("Invalid GitHub repository URL.")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) != 2:
        raise ValueError("Invalid GitHub repository URL.")

    owner, repo_name = path_parts
    repo_name = repo_name.removesuffix(".git")

    if not owner or not repo_name:
        raise ValueError("Invalid GitHub repository URL.")

    return f"https://github.com/{owner}/{repo_name}"


def _ensure_repositories_root() -> Path:
    BASE_REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
    return BASE_REPOSITORIES_DIR


def create_unique_clone_directory() -> Path:
    base_dir = _ensure_repositories_root()
    for _ in range(100):
        candidate = base_dir / uuid4().hex
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not create a unique repository directory.")


def _should_ignore_directory(directory_name: str) -> bool:
    return directory_name in IGNORE_DIRECTORIES or directory_name.startswith(".") and directory_name not in {".env.example"}


def _should_ignore_file(file_name: str, file_path: str) -> bool:
    normalized_name = file_name.lower()
    normalized_path = file_path.lower()

    if normalized_name in {".env", ".gitignore", ".gitattributes"}:
        return True

    if normalized_name == ".env.example":
        return False

    if normalized_name.startswith(".env."):
        return True

    if normalized_name.endswith((".pem", ".key")):
        return True

    if normalized_path.startswith(".git/"):
        return True

    if any(pattern in normalized_path for pattern in ["/node_modules/", "/.git/"]):
        return True

    if normalized_name in {"dockerfile", "makefile"}:
        return False

    suffix = Path(normalized_name).suffix.lower()
    if suffix in IGNORED_EXTENSIONS:
        return True

    if suffix and suffix not in SUPPORTED_EXTENSIONS:
        return True

    return False


def _is_probably_binary(file_bytes: bytes) -> bool:
    if not file_bytes:
        return True

    if b"\x00" in file_bytes:
        return True

    sample = file_bytes[:2048]
    if not sample:
        return True

    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True

    return False


def _read_text_file(file_path: Path) -> str | None:
    try:
        file_bytes = file_path.read_bytes()
    except OSError:
        return None

    if len(file_bytes) > MAX_FILE_SIZE:
        return None

    if _is_probably_binary(file_bytes):
        return None

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None

    return text.replace("\x00", "")


def collect_repository_files(clone_dir: Path) -> list[dict]:
    collected_files: list[dict] = []

    for root, dirs, files in os.walk(clone_dir):
        dirs[:] = [
            directory_name
            for directory_name in sorted(dirs)
            if not _should_ignore_directory(directory_name)
        ]

        for file_name in sorted(files):
            file_path = Path(root) / file_name
            relative_path = file_path.relative_to(clone_dir).as_posix()

            if _should_ignore_file(file_name, relative_path):
                continue

            if file_path.stat().st_size > MAX_FILE_SIZE:
                continue

            content = _read_text_file(file_path)
            if content is None:
                continue

            file_extension = Path(file_name).suffix.lower().lstrip(".")
            if not file_extension:
                file_extension = "txt"

            collected_files.append(
                {
                    "file_path": relative_path,
                    "file_name": file_name,
                    "file_extension": file_extension[:32],
                    "content": content,
                }
            )

    return collected_files


def clone_repository(repo_url: str) -> tuple[str, Path, list[dict]]:
    normalized_repo_url = validate_github_url(repo_url)
    repo_name = normalized_repo_url.rstrip("/").split("/")[-1]
    clone_dir = create_unique_clone_directory()

    try:
        Repo.clone_from(normalized_repo_url, clone_dir, multi_options=["--depth", "1"])
    except Exception as error:
        if clone_dir.exists():
            shutil.rmtree(clone_dir, ignore_errors=True)
        raise RuntimeError(f"The repository could not be cloned: {error}") from error

    try:
        files = collect_repository_files(clone_dir)
    except Exception as error:
        shutil.rmtree(clone_dir, ignore_errors=True)
        raise RuntimeError(f"The repository could not be processed: {error}") from error

    return repo_name, clone_dir, files
