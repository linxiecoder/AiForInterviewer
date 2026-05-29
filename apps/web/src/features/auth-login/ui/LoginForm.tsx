import { Button, Checkbox, Form, Input, Space, Typography } from "antd";
import { useEffect } from "react";
import { useAsyncAction } from "../../../shared/hooks/useAsyncAction";

type LoginFormValues = {
  identifier: string;
  password: string;
  rememberPassword?: boolean;
};

type LoginFormProps = {
  onSubmit: (values: LoginFormValues) => Promise<void>;
  submitting?: boolean;
  loadingText?: string;
  errorMessage?: string | null;
};

const defaultMessage = "邮箱或用户名";
const REMEMBERED_LOGIN_STORAGE_KEY = "aifi:auth-login:remembered-credentials";

type RememberedLoginCredentials = Pick<LoginFormValues, "identifier" | "password">;
type LoginStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

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

function readRememberedLoginCredentials(
  storage: Pick<LoginStorage, "getItem"> | undefined = getBrowserLocalStorage(),
): RememberedLoginCredentials | null {
  try {
    const rawValue = storage?.getItem(REMEMBERED_LOGIN_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<RememberedLoginCredentials>;
    if (typeof parsed.identifier === "string" && typeof parsed.password === "string") {
      return {
        identifier: parsed.identifier,
        password: parsed.password,
      };
    }
  } catch {
    return null;
  }

  return null;
}

function persistRememberedLoginCredentials(
  values: LoginFormValues,
  storage: Pick<LoginStorage, "setItem" | "removeItem"> | undefined = getBrowserLocalStorage(),
) {
  try {
    if (values.rememberPassword) {
      storage?.setItem(
        REMEMBERED_LOGIN_STORAGE_KEY,
        JSON.stringify({
          identifier: values.identifier,
          password: values.password,
        }),
      );
      return;
    }

    storage?.removeItem(REMEMBERED_LOGIN_STORAGE_KEY);
  } catch {
    // localStorage may be unavailable in constrained browser contexts.
  }
}

export function LoginForm({ onSubmit, submitting = false, loadingText, errorMessage }: LoginFormProps) {
  const [form] = Form.useForm<LoginFormValues>();
  const { execute, loading, error, clearError } = useAsyncAction(onSubmit);

  const isBusy = submitting || loading;

  useEffect(() => {
    const rememberedCredentials = readRememberedLoginCredentials();
    if (rememberedCredentials) {
      form.setFieldsValue({
        ...rememberedCredentials,
        rememberPassword: true,
      });
    }
  }, [form]);

  return (
    <Form<LoginFormValues>
      form={form}
      layout="vertical"
      initialValues={{ rememberPassword: false }}
      onFinish={async (values) => {
        clearError();
        try {
          await execute(values);
          persistRememberedLoginCredentials(values);
        } catch {
          // useAsyncAction has already surfaced the login error to the form.
        }
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

      <Form.Item name="rememberPassword" valuePropName="checked">
        <Checkbox disabled={isBusy}>记住密码</Checkbox>
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
