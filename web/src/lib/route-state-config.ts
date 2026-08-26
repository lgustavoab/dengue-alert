export const routeStateConfig = {
  home: {
    area: "Visão geral",
    errorTitle: "Não foi possível carregar a visão geral.",
    errorDescription: "A página inicial está temporariamente indisponível.",
  },
  historical: {
    area: "Histórico",
    errorTitle: "Não foi possível carregar o panorama histórico.",
    errorDescription: "Os dados históricos não puderam ser preparados neste momento.",
    loadingTitle: "Preparando o panorama histórico",
    loadingDescription: "Carregando os contratos e indicadores históricos.",
  },
  quality: {
    area: "Dados & Qualidade",
    errorTitle: "Não foi possível carregar os indicadores de qualidade.",
    errorDescription: "Os dados de rastreabilidade e cobertura não puderam ser preparados neste momento.",
    loadingTitle: "Preparando os indicadores de qualidade",
    loadingDescription: "Carregando os contratos auditados de cobertura e preparação dos dados.",
  },
  prediction: {
    area: "Predição",
    errorTitle: "Não foi possível carregar o dashboard de predição.",
    errorDescription: "A avaliação preditiva retrospectiva não pôde ser preparada neste momento.",
    loadingTitle: "Preparando o dashboard de predição",
    loadingDescription: "Carregando os contratos da avaliação retrospectiva.",
  },
  map: {
    area: "Mapa preditivo",
    errorTitle: "Não foi possível carregar o mapa de predição.",
    errorDescription: "A área do mapa não pôde ser apresentada neste momento.",
  },
} as const;

export type RouteErrorConfig = {
  area: string;
  errorTitle: string;
  errorDescription: string;
};

export type RouteLoadingConfig = {
  area: string;
  loadingTitle: string;
  loadingDescription: string;
};
