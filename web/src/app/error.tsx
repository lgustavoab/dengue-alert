"use client";

import { RouteErrorState } from "@/components/ui/route-error-state";
import { routeStateConfig } from "@/lib/route-state-config";

type HomeErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function HomeError({ reset }: HomeErrorProps) {
  return <RouteErrorState config={routeStateConfig.home} onRetry={reset} />;
}
