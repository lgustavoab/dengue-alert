export const navigationItems = [
  {
    label: "Início",
    href: "/",
  },
  {
    label: "Histórico",
    href: "/historico",
  },
  {
    label: "Dados e método",
    href: "/dados-qualidade",
  },
  {
    label: "Resultados",
    href: "/predicao",
  },
  {
    label: "Mapa",
    href: "/mapa",
  },
] as const;

export function isNavigationItemActive(
  pathname: string,
  href: (typeof navigationItems)[number]["href"],
): boolean {
  if (href === "/") {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}
