import axiosInstance from "./axiosInstance";

export const getNlpStatistics = async () => {
  const response = await axiosInstance.get("/nlp-analysis");
  return response.data;
};
