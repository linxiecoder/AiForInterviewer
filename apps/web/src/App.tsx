import { lazy, Suspense } from "react";

const LegacyMockPage = lazy(() =>
  import("./components/LegacyMockPage.js").then((module) => ({ default: module.LegacyMockPage })),
);
const TrustedTracePage = lazy(() =>
  import("./components/TrustedTracePage.js").then((module) => ({ default: module.TrustedTracePage })),
);
const WorkbenchHomePage = lazy(() =>
  import("./components/WorkbenchHomePage.js").then((module) => ({ default: module.WorkbenchHomePage })),
);

function getCurrentLocation() {
  if (typeof window === "undefined") {
    return {
      pathname: "/",
      search: "",
    };
  }

  return {
    pathname: window.location.pathname,
    search: window.location.search,
  };
}

export function App() {
  const { pathname, search } = getCurrentLocation();
  const params = new URLSearchParams(search);
  let page;

  if (pathname.startsWith("/interviews/")) {
    const sessionId = decodeURIComponent(pathname.replace(/^\/interviews\//, ""));
    const ownerId = params.get("owner_id") ?? "owner-local";

    page = <TrustedTracePage sessionId={sessionId} ownerId={ownerId} />;
  } else if (pathname === "/legacy-mock" || pathname === "/mock") {
    page = <LegacyMockPage />;
  } else {
    page = <WorkbenchHomePage ownerId={params.get("owner_id") ?? "owner-local"} />;
  }

  return <Suspense fallback={<main className="app-shell route-loading">正在加载工作台...</main>}>{page}</Suspense>;
}
