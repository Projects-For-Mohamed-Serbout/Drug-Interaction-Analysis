import axios from "./axiosInstance";

export const getDashboardStats = async () => {
  const response = await axios.get("/dashboard/stats");
  return response.data;
};
