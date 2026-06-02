import axios from "./axiosInstance";

export const getDashboardStats = async () => {
  const response = await axios.get("/dashboard/stats");
  return response.data;
};

export const getIntegrityReport = async () => {
  const response = await axios.get("/dashboard/integrity");
  return response.data;
};
