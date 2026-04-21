import axiosInstance from "./axiosInstance";

export const getBenchmarkResults = async () => {
  const response = await axiosInstance.get("/database-performance");
  return response.data;
};

export const getGraphStats = async () => {
  const response = await axiosInstance.get("/database-performance/graph-stats");
  return response.data;
};
