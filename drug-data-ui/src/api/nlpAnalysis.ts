import axiosInstance from "./axiosInstance";

export const getNlpStatistics = async () => {
  const response = await axiosInstance.get("/nlp-analysis");
  return response.data;
};

export const getNlpEvaluation = async () => {
  const response = await axiosInstance.get("/nlp-analysis/evaluation");
  return response.data;
};

export const getSeverityTypeMatrix = async () => {
  const response = await axiosInstance.get("/nlp-analysis/severity-type-matrix");
  return response.data;
};
