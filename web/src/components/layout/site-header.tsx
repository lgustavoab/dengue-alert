import Link from "next/link";

import { MainNavigation } from "@/components/layout/main-navigation";

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

        <MainNavigation />
      </div>
    </header>
  );
}
