import axiosInstance from "./axiosInstance";

export const getNlpStatistics = async () => {
  const response = await axiosInstance.get("/nlp-analysis");
  return response.data;
};

export const getNlpEvaluation = async () => {
  const response = await axiosInstance.get("/nlp-analysis/evaluation");
  return response.data;
};
