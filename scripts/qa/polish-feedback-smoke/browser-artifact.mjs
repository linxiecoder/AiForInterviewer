import { spawnSync } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import path from "node:path";

export async function captureBrowserArtifact(context) {
  const screenshotPath = path.join(context.evidenceDir, "task-6-browser.png");
  rmSync(screenshotPath, { force: true });
  const sessionName = `task-6-${process.pid}`;
  const cookieValue = context.cookie.split("=", 2)[1];
  const statements = [
    `await page.context().addCookies([{name:"aifi_session",value:${JSON.stringify(cookieValue)},domain:"127.0.0.1",path:"/"}]);`,
    "await page.setViewportSize({width:1440,height:900});",
    `await page.goto(${JSON.stringify(`${context.webBase}/interview/${encodeURIComponent(context.sessionId)}`)},{waitUntil:"networkidle"});`,
    `const answerMarker=${JSON.stringify(context.answerText)};`,
    `const expectedPanelText=${JSON.stringify(context.expectedPanelText)};`,
    `const qaMarker=${JSON.stringify(context.qaMarker)};`,
    "await page.getByText(answerMarker,{exact:false}).last().click({timeout:30000}).catch(()=>{});",
    "const panel=page.getByTestId('interview-workbench-feedback-sheet');",
    "await panel.waitFor({state:'visible',timeout:30000});",
    "const panelText=await panel.textContent();",
    "if(!panelText||!panelText.includes(expectedPanelText)){throw new Error(`feedback panel missing expected terminal text ${expectedPanelText}: ${panelText}`);}",
    "await panel.evaluate((element,qaMarker)=>{const marker=document.createElement('div');marker.setAttribute('data-qa-marker','task-6-correlation');marker.style.cssText='margin:8px 10px;padding:8px;border:1px solid #1677ff;border-radius:6px;background:#e6f4ff;color:#003a8c;font:12px/1.4 monospace;word-break:break-all';marker.textContent=`QA marker ${qaMarker}`;element.prepend(marker);},qaMarker);",
    `await panel.screenshot({path:${JSON.stringify(screenshotPath)}});`,
  ].join("");
  const code = `async () => {${statements}}`;
  runPlaywrightCli({
    context,
    args: ["--session", sessionName, "open", "about:blank"],
    timeout: 120_000,
  });
  let runCodeResult = null;
  try {
    runCodeResult = runPlaywrightCli({
      context,
      args: ["--session", sessionName, "run-code", code],
      timeout: 120_000,
    });
  } finally {
    runPlaywrightCli({
      context,
      args: ["--session", sessionName, "close"],
      timeout: 30_000,
      allowFailure: true,
    });
  }
  if (!existsSync(screenshotPath)) {
    throw new Error(
      "browser screenshot artifact should exist"
      + `\nrun-code stdout:\n${runCodeResult?.stdout ?? ""}`
      + `\nrun-code stderr:\n${runCodeResult?.stderr ?? ""}`,
    );
  }
}

function runPlaywrightCli(command) {
  const env = {
    ...process.env,
    npm_config_cache: path.join(command.context.tempDir, "npm-cache"),
    LOCALAPPDATA: path.join(command.context.tempDir, "localappdata"),
    PLAYWRIGHT_BROWSERS_PATH: path.join(command.context.tempDir, "ms-playwright"),
  };
  const cliArgs = ["npx.cmd", "--yes", "--package", "@playwright/cli", "playwright-cli", ...command.args];
  const result = spawnSync("cmd.exe", ["/d", "/c", ...cliArgs], {
    cwd: command.context.rootDir,
    env,
    encoding: "utf8",
    timeout: command.timeout,
  });
  if (!command.allowFailure && result.status !== 0) {
    throw new Error(
      `playwright-cli ${command.args.join(" ")} failed`
      + `\nstatus: ${result.status} signal: ${result.signal} error: ${result.error?.message ?? ""}`
      + `\nstdout:\n${result.stdout ?? ""}\nstderr:\n${result.stderr ?? ""}`,
    );
  }
  return result;
}
