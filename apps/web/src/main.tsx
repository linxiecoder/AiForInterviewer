import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

const root = document.getElementById("root");

if (root === null) {
  throw new Error("Root element #root was not found.");
}

createRoot(root).render(
  <StrictMode>
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
        color: "#172033",
        background: "#f7f8fb",
        fontFamily: "'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif",
      }}
    >
      <section style={{ maxWidth: 720, width: "100%" }}>
        <p style={{ margin: "0 0 8px", color: "#31558f", fontWeight: 700 }}>
          AI 模拟面试工作台级 MVP
        </p>
        <h1 style={{ margin: 0, fontSize: 32, lineHeight: 1.2 }}>AiForInterviewer</h1>
      </section>
    </main>
  </StrictMode>,
);
