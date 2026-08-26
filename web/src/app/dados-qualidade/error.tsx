"use client";

import { RouteErrorState } from "@/components/ui/route-error-state";
import { routeStateConfig } from "@/lib/route-state-config";

type DataQualityErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function DataQualityError({ reset }: DataQualityErrorProps) {
  return <RouteErrorState config={routeStateConfig.quality} onRetry={reset} />;
}
