import {
  AimOutlined,
  AppstoreOutlined,
  DashboardOutlined,
  FileTextOutlined,
  HomeOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ReadOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Divider, Layout, Menu, Tooltip, Typography } from "antd";
import type { CSSProperties, ReactNode } from "react";
import { useMemo, useState } from "react";
import { useRoutePath } from "../../app/routes/router";
import { useAuth } from "../../app/providers/AuthProvider";
import { APP_SHELL_NAV_ITEMS, getActiveNavKey, type AppShellIconKey } from "./model/navigation";
import { UserMenu } from "./UserMenu";
import styles from "./Sidebar.module.css";

export const APP_SIDEBAR_COLLAPSE_CONFIG = {
  expandedWidth: 240,
  collapsedWidth: 72,
  defaultCollapsed: false,
  hoverLabel: "menu_item_title",
  persistence: "local_storage",
  storageKey: "aifi:app-shell:sidebar-collapsed",
  menuItemHeight: 40,
} as const;

const APP_SIDEBAR_COLLAPSE_LABEL = {
  collapse: "收起侧边栏",
  expand: "展开侧边栏",
} as const;

const SIDEBAR_COLLAPSED_STORAGE_VALUE = "collapsed";
const SIDEBAR_EXPANDED_STORAGE_VALUE = "expanded";

type SidebarCollapseStorageReader = Pick<Storage, "getItem">;
type SidebarCollapseStorageWriter = Pick<Storage, "setItem">;

function getBrowserLocalStorage(): Storage | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }

  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
}

export function getPersistedSidebarCollapsed(storage: SidebarCollapseStorageReader | undefined = getBrowserLocalStorage()): boolean {
  try {
    const value = storage?.getItem(APP_SIDEBAR_COLLAPSE_CONFIG.storageKey);
    if (value === SIDEBAR_COLLAPSED_STORAGE_VALUE) {
      return true;
    }
    if (value === SIDEBAR_EXPANDED_STORAGE_VALUE) {
      return false;
    }
  } catch {
    return APP_SIDEBAR_COLLAPSE_CONFIG.defaultCollapsed;
  }

  return APP_SIDEBAR_COLLAPSE_CONFIG.defaultCollapsed;
}

function persistSidebarCollapsed(collapsed: boolean, storage: SidebarCollapseStorageWriter | undefined = getBrowserLocalStorage()) {
  try {
    storage?.setItem(
      APP_SIDEBAR_COLLAPSE_CONFIG.storageKey,
      collapsed ? SIDEBAR_COLLAPSED_STORAGE_VALUE : SIDEBAR_EXPANDED_STORAGE_VALUE,
    );
  } catch {
    // localStorage may be unavailable in constrained browser contexts.
  }
}

function getMenuItemsWithModel() {
  const iconMap: Record<AppShellIconKey, ReactNode> = {
    home: <HomeOutlined />,
    resume: <FileTextOutlined />,
    target: <AimOutlined />,
    interview: <DashboardOutlined />,
    review: <AppstoreOutlined />,
    knowledge: <ReadOutlined />,
    growth: <SettingOutlined />,
  };

  return APP_SHELL_NAV_ITEMS.map((item) => ({
    key: item.key,
    icon: iconMap[item.icon],
    label: item.label,
    disabled: item.disabled,
    title: item.label,
  }));
}

export function Sidebar() {
  const path = useRoutePath();
  const { currentUser, logout } = useAuth();
  const [collapsed, setCollapsed] = useState<boolean>(() => getPersistedSidebarCollapsed());

  const selectedKeys = useMemo(() => {
    return [getActiveNavKey(path)];
  }, [path]);

  const userName = currentUser?.display_name || currentUser?.username || "王小明";
  const userRole = currentUser?.roles?.[0] || "产品经理";
  const userInitial = (userName || "王").slice(0, 1);

  function handleMenuClick({ key }: { key: string }) {
    const target = APP_SHELL_NAV_ITEMS.find((item) => item.key === key);
    if (!target || target.disabled) {
      return;
    }

    const nextPath = target.path;
    if (window.location.pathname !== nextPath) {
      window.history.pushState({}, "", nextPath);
      window.dispatchEvent(new PopStateEvent("popstate"));
    }
  }

  const navItems = getMenuItemsWithModel();

  const collapseLabel = collapsed ? APP_SIDEBAR_COLLAPSE_LABEL.expand : APP_SIDEBAR_COLLAPSE_LABEL.collapse;
  const sidebarStyle = {
    "--sidebar-menu-item-height": `${APP_SIDEBAR_COLLAPSE_CONFIG.menuItemHeight}px`,
  } as CSSProperties;

  function toggleCollapsed() {
    setCollapsed((current) => {
      const next = !current;
      persistSidebarCollapsed(next);
      return next;
    });
  }

  return (
    <Layout.Sider
      width={APP_SIDEBAR_COLLAPSE_CONFIG.expandedWidth}
      collapsedWidth={APP_SIDEBAR_COLLAPSE_CONFIG.collapsedWidth}
      collapsed={collapsed}
      theme="light"
      className={`${styles.sidebar} ${collapsed ? styles.sidebarCollapsed : ""}`}
      style={sidebarStyle}
    >
      <div className={styles.sidebarHeader}>
        {collapsed ? null : (
          <Typography.Text strong className={styles.productName}>
            AiForInterviewer
          </Typography.Text>
        )}
        <Tooltip title={collapseLabel} placement={collapsed ? "right" : "bottom"}>
          <Button
            type="text"
            size="small"
            className={styles.collapseButton}
            aria-label={collapseLabel}
            aria-expanded={!collapsed}
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={toggleCollapsed}
          />
        </Tooltip>
      </div>

      <Menu
        className={styles.navMenu}
        mode="inline"
        inlineCollapsed={collapsed}
        selectable
        selectedKeys={selectedKeys}
        onClick={handleMenuClick}
        items={navItems}
      />

      <div className={styles.footer}>
        <Divider className={styles.footerDivider} />
        <div className={styles.userInfoWrap}>
          <Avatar className={styles.userAvatar}>{userInitial}</Avatar>
          <div className={styles.userTextWrap}>
            <Typography.Text strong>{userName}</Typography.Text>
            <Typography.Text type="secondary" style={{ display: "block" }}>
              {userRole}
            </Typography.Text>
            {currentUser?.email ? <Typography.Text type="secondary">{currentUser.email}</Typography.Text> : null}
          </div>
          <UserMenu onLogout={logout} />
        </div>
      </div>
    </Layout.Sider>
  );
}
