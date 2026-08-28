import { RouteLoadingState } from "@/components/ui/route-loading-state";
import { routeStateConfig } from "@/lib/route-state-config";

export default function PredictionLoading() {
  return <RouteLoadingState config={routeStateConfig.prediction} />;
}
