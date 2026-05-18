import { Card, Layout } from "antd";
import { useAuth } from "../../app/providers/AuthProvider";
import { LoginForm } from "../../features/auth-login/ui/LoginForm";

export function LoginPage() {
  const { login } = useAuth();

  return (
    <Layout
      style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#f5f7fa" }}
    >
      <Card style={{ width: 420 }} variant="borderless">
        <LoginForm
          onSubmit={async ({ identifier, password }) => {
            await login(identifier, password);
          }}
          loadingText="登录中"
        />
      </Card>
    </Layout>
  );
}
