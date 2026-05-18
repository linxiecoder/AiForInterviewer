import { AppstoreOutlined, FileTextOutlined, HomeOutlined, ReadOutlined, DashboardOutlined, SettingOutlined, AimOutlined } from "@ant-design/icons";
import { Avatar, Divider, Layout, Menu, Typography } from "antd";
import type { ReactNode } from "react";
import { useMemo } from "react";
import { useRoutePath } from "../../app/routes/router";
import { useAuth } from "../../app/providers/AuthProvider";
import { APP_SHELL_NAV_ITEMS, type AppShellIconKey } from "./model/navigation";
import { UserMenu } from "./UserMenu";
import styles from "./Sidebar.module.css";

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

  const selectedKeys = useMemo(() => {
    const target = APP_SHELL_NAV_ITEMS.find((item) => item.path === path && !item.disabled);
    return target ? [target.key] : ["dashboard"];
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

  return (
    <Layout.Sider width={240} theme="light" className={styles.sidebar}>
      <div className={styles.sidebarHeader}>
        <Typography.Text strong className={styles.productName}>
          AiForInterviewer
        </Typography.Text>
      </div>

      <Menu
        className={styles.navMenu}
        mode="inline"
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
