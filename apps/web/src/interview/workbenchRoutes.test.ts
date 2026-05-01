import assert from "node:assert/strict";
import test from "node:test";

import { workbenchHomeText } from "../appContent.js";

test("workbench primary actions use real routes instead of anchor targets", () => {
  const expectedRoutes = new Map([
    ["发起模拟面试", "/interviews/new"],
    ["历史记录", "/interviews"],
    ["岗位管理", "/jobs"],
    ["简历管理", "/resumes"],
    ["复盘", "/reviews"],
  ]);

  for (const [title, href] of expectedRoutes) {
    const action = workbenchHomeText.primaryActions.find((item) => item.title === title);
    assert.ok(action, `missing primary action: ${title}`);
    assert.equal(action.href, href);
    assert.equal(action.href.startsWith("#"), false);
  }
});
