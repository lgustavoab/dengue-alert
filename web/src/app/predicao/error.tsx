"use client";

import { RouteErrorState } from "@/components/ui/route-error-state";
import { routeStateConfig } from "@/lib/route-state-config";

type PredictionErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function PredictionError({ reset }: PredictionErrorProps) {
  return <RouteErrorState config={routeStateConfig.prediction} onRetry={reset} />;
}
