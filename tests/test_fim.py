import json
from src.fim import FileIntegrityMonitor


def test_modified_detection(tmp_path):
    root = tmp_path / "root"
    root.mkdir()

    f = root / "file.txt"
    f.write_text("original")

    baseline = tmp_path / "baseline.json"
    FileIntegrityMonitor.create_baseline(root, baseline)

    # 修改文件内容
    f.write_text("modified content")

    res = FileIntegrityMonitor.check_integrity(root, baseline)

    assert res["modified"] == ["file.txt"]
    assert res["added"] == []
    assert res["deleted"] == []


def test_deleted_detection(tmp_path):
    root = tmp_path / "root"
    root.mkdir()

    to_remove = root / "remove.me"
    to_remove.write_text("bye")

    keep = root / "keep.me"
    keep.write_text("stay")

    baseline = tmp_path / "baseline.json"
    FileIntegrityMonitor.create_baseline(root, baseline)

    # 删除一个文件
    to_remove.unlink()

    res = FileIntegrityMonitor.check_integrity(root, baseline)

    assert res["deleted"] == ["remove.me"]
    assert res["modified"] == []
    assert res["added"] == []


def test_added_detection(tmp_path):
    root = tmp_path / "root"
    root.mkdir()

    existing = root / "exists.txt"
    existing.write_text("here")

    baseline = tmp_path / "baseline.json"
    FileIntegrityMonitor.create_baseline(root, baseline)

    # 新增文件
    newf = root / "new.file"
    newf.write_text("new content")

    res = FileIntegrityMonitor.check_integrity(root, baseline)

    assert res["added"] == ["new.file"]
    assert res["modified"] == []
    assert res["deleted"] == []


def test_missing_baseline_is_handled(tmp_path):
    root = tmp_path / "root"
    root.mkdir()

    a = root / "a.txt"
    b = root / "sub" / "b.txt"
    (root / "sub").mkdir()
    a.write_text("a")
    b.write_text("b")

    # 不创建基线文件，直接调用 check_integrity
    missing_baseline = tmp_path / "does_not_exist.json"

    res = FileIntegrityMonitor.check_integrity(root, missing_baseline)

    # 当基线缺失时，所有当前文件应被视为新增
    added = sorted(res["added"])
    assert added == sorted(["a.txt", "sub/b.txt"]) or set(added) == {"a.txt", "sub/b.txt"}
    assert res["deleted"] == []
    assert res["modified"] == []
