import { Avatar, Space, Typography } from "antd";
import { User } from "../model/types";

type UserBadgeProps = {
  user: User | null;
};

export function UserBadge({ user }: UserBadgeProps) {
  if (user === null) {
    return <Typography.Text type="secondary">未登录</Typography.Text>;
  }

  const displayName = user.display_name || user.username;
  const roleFromData = user.roles?.[0];
  const roleLabel = roleFromData ?? "候选人（TODO：角色字段待核验）";

  return (
    <Space size={8} align="center">
      <Avatar>{displayName.slice(0, 1)}</Avatar>
      <div>
        <div>
          <Typography.Text strong>{displayName}</Typography.Text>
        </div>
        <Typography.Text type="secondary">{user.email}</Typography.Text>
        <br />
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          {roleLabel}
        </Typography.Text>
      </div>
    </Space>
  );
}
