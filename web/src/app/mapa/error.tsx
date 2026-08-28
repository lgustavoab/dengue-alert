"use client";

import { RouteErrorState } from "@/components/ui/route-error-state";
import { routeStateConfig } from "@/lib/route-state-config";

type MapErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function MapError({ reset }: MapErrorProps) {
  return <RouteErrorState config={routeStateConfig.map} onRetry={reset} />;
}
