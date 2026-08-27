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
    label: "Dados & Qualidade",
    href: "/dados-qualidade",
  },
  {
    label: "Predição",
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
