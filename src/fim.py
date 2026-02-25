from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Union

logger = logging.getLogger(__name__)


class FileIntegrityMonitor:
	"""文件完整性监控器，使用 SHA-256 计算文件哈希并生成/校验基线。

	所有路径可以传入字符串或 ``pathlib.Path`` 对象。基线中的路径是
	相对于提供的根目录的字符串路径。
	"""

	@staticmethod
	def _hash_file(path: Path) -> str:
		"""计算文件的 SHA-256 摘要并以十六进制字符串返回。

		在读取过程中会以流式方式分块读取以节省内存。
		"""
		hasher = hashlib.sha256()
		try:
			with path.open("rb") as fh:
				for chunk in iter(lambda: fh.read(8192), b""):
					hasher.update(chunk)
		except PermissionError:
			logger.warning("Permission denied when reading file: %s", path)
			raise
		return hasher.hexdigest()

	@classmethod
	def create_baseline(
		cls, root_dir: Union[str, Path], output_file: Union[str, Path]
	) -> None:
		"""递归遍历 ``root_dir``，计算所有文件的 SHA-256，并将基线写为 JSON。

		基线文件内容为字典，键为相对路径（使用 POSIX 风格斜杠），值为
		十六进制哈希字符串。

		如果在遍历或读取文件时遇到权限错误或文件不存在，方法不会抛出
		未捕获异常；会记录警告并跳过该文件。
		"""
		root = Path(root_dir)
		out = Path(output_file)
		baseline: Dict[str, str] = {}

		if not root.exists():
			logger.warning("Root directory does not exist: %s", root)
			# 写入空基线并返回，避免抛出异常
			out.parent.mkdir(parents=True, exist_ok=True)
			out.write_text(json.dumps(baseline, indent=2))
			return

		for path in root.rglob("*"):
			if not path.is_file():
				continue
			try:
				digest = cls._hash_file(path)
			except PermissionError:
				# 已记录警告，跳过该文件
				continue
			except OSError as exc:
				logger.warning("OS error when hashing %s: %s", path, exc)
				continue

			try:
				rel_path = path.relative_to(root).as_posix()
			except Exception:
				# Fallback to absolute string if relative conversion fails
				rel_path = str(path)

			baseline[rel_path] = digest

		try:
			out.parent.mkdir(parents=True, exist_ok=True)
			out.write_text(json.dumps(baseline, indent=2))
		except OSError as exc:
			logger.warning("Failed to write baseline file %s: %s", out, exc)

	@classmethod
	def check_integrity(
		cls, root_dir: Union[str, Path], baseline_file: Union[str, Path]
	) -> Dict[str, List[str]]:
		"""检查当前 ``root_dir`` 下的文件相对于给定基线的变化。

		返回包含三个键的字典：'modified', 'added', 'deleted'，其值均为
		相对路径（相对于 ``root_dir``）的字符串列表。

		如果基线文件不存在或无法解析，会记录警告并将当前所有文件
		视为新增（``added``）。遇到权限或读写错误时跳过受影响的文件
		并记录警告。
		"""
		root = Path(root_dir)
		baseline_path = Path(baseline_file)

		# 读取基线
		baseline: Dict[str, str] = {}
		if baseline_path.exists():
			try:
				baseline = json.loads(baseline_path.read_text())
			except (OSError, json.JSONDecodeError) as exc:
				logger.warning("Failed to read/parse baseline %s: %s",
							   baseline_path, exc)
				baseline = {}
		else:
			logger.warning("Baseline file not found: %s", baseline_path)

		current: Dict[str, str] = {}
		if not root.exists():
			logger.warning("Root directory does not exist: %s", root)
			# If root doesn't exist, everything in baseline is deleted
			deleted = sorted(baseline.keys())
			return {"modified": [], "added": [], "deleted": deleted}

		for path in root.rglob("*"):
			if not path.is_file():
				continue
			try:
				digest = cls._hash_file(path)
			except PermissionError:
				# 权限问题已由 _hash_file 记录，跳过
				continue
			except OSError as exc:
				logger.warning("OS error when hashing %s: %s", path, exc)
				continue

			try:
				rel_path = path.relative_to(root).as_posix()
			except Exception:
				rel_path = str(path)

			current[rel_path] = digest

		baseline_keys = set(baseline.keys())
		current_keys = set(current.keys())

		modified = [p for p in current_keys & baseline_keys
					if current[p] != baseline.get(p)]
		added = sorted(list(current_keys - baseline_keys))
		deleted = sorted(list(baseline_keys - current_keys))

		return {
			"modified": sorted(modified),
			"added": added,
			"deleted": deleted,
		}


__all__ = ["FileIntegrityMonitor"]

