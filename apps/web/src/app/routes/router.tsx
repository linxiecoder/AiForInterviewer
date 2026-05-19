import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useAuth } from "../providers/AuthProvider";
import { LoginPage } from "../../pages/login/LoginPage";
import { DashboardPage } from "../../pages/dashboard/DashboardPage";
import { JobPage } from "../../pages/job/JobPage";
import { ResumePage } from "../../pages/resume/ResumePage";
import { InterviewPage, InterviewWorkbenchPage } from "../../pages/interview/InterviewPage";
import { ErrorState } from "../../shared/ui/ErrorState";
import { LoadingState } from "../../shared/ui/LoadingState";

export type InterviewSessionPath = `/interview/${string}`;
export type RoutePath = "/login" | "/dashboard" | "/resume" | "/job" | "/interview" | InterviewSessionPath | "/";
type RouteAction = (path: string, options?: { replace?: boolean }) => void;

interface RouteContextValue {
  path: RoutePath;
  navigate: RouteAction;
}

const RouteContext = createContext<RouteContextValue | null>(null);

function isInterviewSessionPath(pathname: string): pathname is InterviewSessionPath {
  return /^\/interview\/[^/]+$/.test(pathname);
}

function normalizePath(pathname: string): RoutePath {
  if (
    pathname === "/dashboard" ||
    pathname === "/resume" ||
    pathname === "/job" ||
    pathname === "/interview" ||
    pathname === "/login" ||
    pathname === "/"
  ) {
    return pathname;
  }
  if (isInterviewSessionPath(pathname)) {
    return pathname;
  }
  return "/";
}

function parsePath(rawPath: string | null): RoutePath {
  return normalizePath(rawPath || window.location.pathname);
}

export function getInterviewSessionIdFromPath(path: string): string | null {
  if (!isInterviewSessionPath(path)) {
    return null;
  }
  return decodeURIComponent(path.slice("/interview/".length));
}

export function RouteProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState<RoutePath>(() => normalizePath(window.location.pathname));

  const navigate: RouteAction = useCallback((target, options = {}) => {
    if (!target.startsWith("/")) {
      target = `/${target}`;
    }
    const nextPath = target as RoutePath | "/";
    if (window.location.pathname !== nextPath) {
      if (options.replace) {
        window.history.replaceState({}, "", nextPath);
      } else {
        window.history.pushState({}, "", nextPath);
      }
    }
    setPath(nextPath);
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      setPath(normalizePath(parsePath(window.location.pathname)));
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  return (
    <RouteContext.Provider value={{ path, navigate }}>{children}</RouteContext.Provider>
  );
}

function useRoute(): RouteContextValue {
  const ctx = useContext(RouteContext);
  if (ctx === null) {
    throw new Error("useRoute 必须在 RouteProvider 内部使用");
  }
  return ctx;
}

export function AppRouter() {
  const { currentUser, loading } = useAuth();
  const { path, navigate } = useRoute();

  const redirectTo = useMemo(() => {
    if (path === "/") {
      return "/dashboard" as const;
    }

    if (path === "/dashboard" && currentUser === null) {
      return "/login" as const;
    }

    if (path === "/login" && currentUser !== null) {
      return "/dashboard" as const;
    }

    return null;
  }, [currentUser, path]);

  useEffect(() => {
    if (loading) {
      return;
    }

    if (redirectTo === null || redirectTo === path) {
      return;
    }

    navigate(redirectTo, { replace: true });
  }, [loading, path, redirectTo, navigate]);

  if (loading) {
    return <LoadingState message="初始化身份..." />;
  }

  if (redirectTo !== null) {
    return null;
  }

  if (path === "/login") {
    return <LoginPage />;
  }

  if (path === "/dashboard") {
    return <DashboardPage />;
  }

  if (path === "/resume") {
    return <ResumePage />;
  }

  if (path === "/job") {
    return <JobPage />;
  }

  if (path === "/interview") {
    return <InterviewPage />;
  }

  const interviewSessionId = getInterviewSessionIdFromPath(path);
  if (interviewSessionId !== null) {
    return <InterviewWorkbenchPage sessionId={interviewSessionId} />;
  }

  return (
    <ErrorState
      message="页面不存在"
      details={`当前路径: ${path}`}
      actionLabel={currentUser ? "进入工作台" : "返回登录"}
      onAction={() => navigate(currentUser ? "/dashboard" : "/login", { replace: true })}
    />
  );
}

export function useRoutePath() {
  return useRoute().path;
}

export function useRouteController() {
  return useRoute();
}
