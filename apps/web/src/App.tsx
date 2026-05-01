import { LegacyMockPage } from "./components/LegacyMockPage.js";
import { TrustedTracePage } from "./components/TrustedTracePage.js";
import { WorkbenchHomePage } from "./components/WorkbenchHomePage.js";

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

  if (pathname.startsWith("/interviews/")) {
    const sessionId = decodeURIComponent(pathname.replace(/^\/interviews\//, ""));
    const ownerId = new URLSearchParams(search).get("owner_id") ?? "owner-local";

    return <TrustedTracePage sessionId={sessionId} ownerId={ownerId} />;
  }

  if (pathname === "/legacy-mock" || pathname === "/mock") {
    return <LegacyMockPage />;
  }

  return <WorkbenchHomePage />;
}
