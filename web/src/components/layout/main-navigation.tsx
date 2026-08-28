"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

import {
  isNavigationItemActive,
  navigationItems,
} from "@/lib/constants/navigation";

const NAVIGATION_EDGE_GAP = 4;

export function MainNavigation() {
  const pathname = usePathname();
  const navigationRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const navigation = navigationRef.current;
    const activeLink = navigation?.querySelector<HTMLAnchorElement>(
      '[aria-current="page"]',
    );

    if (navigation === null || activeLink === undefined || activeLink === null) {
      return;
    }

    const keepActiveLinkVisible = () => {
      const navigationBounds = navigation.getBoundingClientRect();
      const activeBounds = activeLink.getBoundingClientRect();
      const visibleLeft = navigationBounds.left + NAVIGATION_EDGE_GAP;
      const visibleRight = navigationBounds.right - NAVIGATION_EDGE_GAP;

      if (activeBounds.left < visibleLeft) {
        navigation.scrollLeft -= visibleLeft - activeBounds.left;
      } else if (activeBounds.right > visibleRight) {
        navigation.scrollLeft += activeBounds.right - visibleRight;
      }
    };

    keepActiveLinkVisible();

    const resizeObserver = new ResizeObserver(keepActiveLinkVisible);
    resizeObserver.observe(navigation);
    resizeObserver.observe(activeLink);

    return () => resizeObserver.disconnect();
  }, [pathname]);

  return (
    <nav
      ref={navigationRef}
      className="site-nav"
      aria-label="Navegação principal"
    >
      {navigationItems.map((item) => {
        const isActive = isNavigationItemActive(pathname, item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`site-nav__link${isActive ? " site-nav__link--active" : ""}`}
            aria-current={isActive ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
