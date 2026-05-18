import { Button, Form, Input, Space, Typography } from "antd";
import { useAsyncAction } from "../../../shared/hooks/useAsyncAction";

type LoginFormValues = {
  identifier: string;
  password: string;
};

type LoginFormProps = {
  onSubmit: (values: LoginFormValues) => Promise<void>;
  submitting?: boolean;
  loadingText?: string;
  errorMessage?: string | null;
};

const defaultMessage = "邮箱或用户名";

export function LoginForm({ onSubmit, submitting = false, loadingText, errorMessage }: LoginFormProps) {
  const [form] = Form.useForm<LoginFormValues>();
  const { execute, loading, error, clearError } = useAsyncAction(onSubmit);

  const isBusy = submitting || loading;

  return (
    <Form<LoginFormValues>
      form={form}
      layout="vertical"
      onFinish={(values) => {
        clearError();
        void execute(values);
      }}
    >
      <Typography.Title level={3} style={{ marginBottom: 4 }}>
        登录
      </Typography.Title>
      <Typography.Text type="secondary" style={{ marginBottom: 16, display: "block" }}>
        使用邮箱或用户名 + 密码进行身份验证
      </Typography.Text>

      <Form.Item
        label="登录账号"
        name="identifier"
        rules={[{ required: true, message: "请输入邮箱或用户名" }]}
      >
        <Input placeholder={defaultMessage} size="large" autoComplete="username" />
      </Form.Item>

      <Form.Item
        label="密码"
        name="password"
        rules={[{ required: true, message: "请输入密码" }]}
      >
        <Input.Password placeholder="请输入密码" size="large" autoComplete="current-password" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" size="large" htmlType="submit" loading={isBusy} block>
          {loadingText ?? "登录"}
        </Button>
      </Form.Item>

      {errorMessage || error ? (
        <Typography.Text type="danger">{errorMessage ?? error}</Typography.Text>
      ) : null}

      <Form.Item style={{ marginBottom: 0 }}>
        <Space size="middle" orientation="vertical" style={{ width: "100%" }} />
      </Form.Item>
    </Form>
  );
}
