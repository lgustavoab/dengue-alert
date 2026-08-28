import { RouteLoadingState } from "@/components/ui/route-loading-state";
import { routeStateConfig } from "@/lib/route-state-config";

export default function HistoricalLoading() {
  return <RouteLoadingState config={routeStateConfig.historical} />;
}
