import { LogoutOutlined, SettingOutlined } from "@ant-design/icons";
import { Button, Dropdown, type MenuProps, Tooltip } from "antd";
import { type ReactNode, useMemo } from "react";

type UserMenuProps = {
  onLogout: () => Promise<void> | void;
  settingsDisabled?: boolean;
};

export function UserMenu({ onLogout, settingsDisabled = true }: UserMenuProps) {
  const items = useMemo<MenuProps["items"]>(
    () => [
      {
        key: "settings",
        label: <span>设置（待联调）</span> as ReactNode,
        icon: <SettingOutlined />,
        disabled: settingsDisabled,
      },
      {
        key: "logout",
        label: <span>退出登录</span> as ReactNode,
        icon: <LogoutOutlined />,
        danger: true,
      },
    ],
    [settingsDisabled],
  );

  return (
    <Dropdown
      menu={{
        items,
        onClick: ({ key }) => {
          if (key === "logout") {
            void onLogout();
          }
        },
      }}
      trigger={["click"]}
    >
      <Tooltip title="用户设置">
        <Button
          type="text"
          size="small"
          aria-label="用户设置"
          title="用户设置"
          icon={<SettingOutlined />}
        />
      </Tooltip>
    </Dropdown>
  );
}
