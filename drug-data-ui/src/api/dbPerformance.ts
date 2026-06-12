import axiosInstance from "./axiosInstance";

export const getBenchmarkResults = async () => {
  const response = await axiosInstance.get("/database-performance");
  return response.data;
};

export const getGraphStats = async () => {
  const response = await axiosInstance.get("/database-performance/graph-stats");
  return response.data;
};

export const getScalabilityResults = async () => {
  const response = await axiosInstance.get("/database-performance/scalability");
  return response.data;
};

export const getQueryProfiles = async () => {
  const response = await axiosInstance.get("/database-performance/query-profiles");
  return response.data;
};
