import { Button, Typography } from "antd";

import { workbenchNavigation } from "../appContent.js";

const { Text } = Typography;

function currentPathname() {
  return typeof window === "undefined" ? "/" : window.location.pathname;
}

export function hrefWithCurrentOwner(href: string): string {
  if (typeof window === "undefined") {
    return href;
  }
  const ownerId = new URLSearchParams(window.location.search).get("owner_id");
  if (!ownerId) {
    return href;
  }
  const params = new URLSearchParams({ owner_id: ownerId });
  return `${href}?${params}`;
}

export function WorkbenchNav() {
  const pathname = currentPathname();

  return (
    <nav className="workbench-nav" aria-label="工作台一级导航">
      <a className="workbench-nav-brand" href="/">
        <Text strong>AI 模拟面试工作台</Text>
      </a>
      <div className="workbench-nav-links">
        {workbenchNavigation.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Button
              className="workbench-nav-link"
              href={hrefWithCurrentOwner(item.href)}
              key={item.href}
              type={isActive ? "primary" : "text"}
            >
              {item.label}
            </Button>
          );
        })}
      </div>
    </nav>
  );
}
