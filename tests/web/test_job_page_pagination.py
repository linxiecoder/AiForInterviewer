import re
from pathlib import Path


def test_job_page_size_changer_is_not_locked_to_static_page_size() -> None:
    source = Path("apps/web/src/pages/job/JobPage.tsx").read_text(encoding="utf-8")

    assert "showSizeChanger: true" in source
    assert "showTotal:" in source
    assert re.search(
        r"pagination=\{\{\s*pageSize:\s*10\s*,\s*showSizeChanger:\s*true\s*\}\}",
        source,
    ) is None


def test_job_page_header_copy_is_removed() -> None:
    source = Path("apps/web/src/pages/job/JobPage.tsx").read_text(encoding="utf-8")

    assert "岗位 / JD 管理" not in source
    assert "支持岗位列表、创建 / 编辑、详情查看、归档与简历绑定联调。" not in source


def test_job_page_has_local_search_input() -> None:
    source = Path("apps/web/src/pages/job/JobPage.tsx").read_text(encoding="utf-8")

    assert "jobSearchKeyword" in source
    assert "<Input.Search" in source
    assert "filteredJobs" in source
