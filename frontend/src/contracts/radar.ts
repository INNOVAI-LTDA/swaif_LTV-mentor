export type RadarAxisScoreDto = {
  axisKey: string;
  axisLabel: string;
  axisSub?: string;
  baseline: number;
  current: number;
  projected?: number | null;
  insight?: string | null;
};

export type RadarResponseDto = {
  studentId: string;
  axisScores: RadarAxisScoreDto[];
  avgBaseline: number;
  avgCurrent: number;
  avgProjected: number;
  context?: {
    mentorName?: string;
    mentorId?: string;
    protocolName?: string;
    protocolId?: string;
  };
};
