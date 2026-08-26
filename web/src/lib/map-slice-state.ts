import type {
  PredictionMapContract,
  PredictionMapHorizon,
} from "@/lib/serving/prediction-map-types";

export type MapSliceStatus =
  | "loading"
  | "ready"
  | "error";

export type MapSliceState = {
  week: number | null;
  horizon: PredictionMapHorizon | null;
  status: MapSliceStatus;
  data: PredictionMapContract | null;
  error: string | null;
};

export function createMapSliceLoadingState(
  week: number,
  horizon: PredictionMapHorizon,
): MapSliceState {
  return {
    week,
    horizon,
    status: "loading",
    data: null,
    error: null,
  };
}

export function createMapSliceErrorState(
  week: number,
  horizon: PredictionMapHorizon,
  error: string,
): MapSliceState {
  return {
    week,
    horizon,
    status: "error",
    data: null,
    error,
  };
}

export function resolveCurrentMapSliceState(
  state: MapSliceState,
  week: number,
  horizon: PredictionMapHorizon,
): MapSliceState {
  if (
    state.week === week
    && state.horizon === horizon
  ) {
    return state;
  }

  return createMapSliceLoadingState(
    week,
    horizon,
  );
}

export function buildPredictionMapSliceUrl(
  week: number,
  horizon: PredictionMapHorizon,
): string {
  return `/api/serving/prediction/map/${horizon}/${week}`;
}
