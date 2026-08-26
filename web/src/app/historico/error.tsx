"use client";

import { RouteErrorState } from "@/components/ui/route-error-state";
import { routeStateConfig } from "@/lib/route-state-config";

type HistoricalErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function HistoricalError({ reset }: HistoricalErrorProps) {
  return <RouteErrorState config={routeStateConfig.historical} onRetry={reset} />;
}
