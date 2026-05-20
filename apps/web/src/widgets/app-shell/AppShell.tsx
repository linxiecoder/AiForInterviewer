import { Layout } from "antd";
import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import styles from "./AppShell.module.css";

export const APP_DOCUMENT_VIEWPORT_POLICY = {
  htmlOverflow: "hidden",
  bodyOverflow: "hidden",
  rootOverflow: "hidden",
  shellOverflow: "hidden",
  mainContentOverflow: "auto",
} as const;

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <Layout className={styles.shell}>
      <Sidebar />
      <Layout>
        <Topbar />
        <Layout.Content className={styles.mainContent}>
          <section className={styles.contentSurface}>{children}</section>
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
