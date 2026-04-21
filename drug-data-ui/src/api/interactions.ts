import axiosInstance from "./axiosInstance";

export const getInteractions = async (
  page: number = 1,
  pageSize: number = 20,
  severity?: string,
  type?: string
) => {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (severity) params.severity = severity;
  if (type) params.type = type;
  const response = await axiosInstance.get("/interactions", { params });
  return response.data;
};

export const getInteractionsForDrug = async (codNacion: string) => {
  const response = await axiosInstance.get(`/interactions/drug/${codNacion}`);
  return response.data;
};
