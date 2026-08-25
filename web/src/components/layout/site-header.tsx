import Link from "next/link";

import { navigationItems } from "@/lib/constants/navigation";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link href="/" className="brand" aria-label="Dengue Alert — Início">
          <span className="brand__mark" aria-hidden="true">
            DA
          </span>

          <span className="brand__text">
            <strong>Dengue Alert</strong>
            <span>Inteligência epidemiológica municipal</span>
          </span>
        </Link>

        <nav className="site-nav" aria-label="Navegação principal">
          {navigationItems.map((item) => (
            <Link key={item.href} href={item.href} className="site-nav__link">
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}