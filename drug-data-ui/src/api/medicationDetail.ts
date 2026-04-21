import axiosInstance from "./axiosInstance";

export const getMedications = async (
  page: number = 1,
  pageSize: number = 20,
  sortBy: string = "nombre_comercial",
  sortOrder: string = "asc"
) => {
  const response = await axiosInstance.get("/medications", {
    params: { page, page_size: pageSize, sort_by: sortBy, sort_order: sortOrder },
  });
  return response.data;
};

export const getMedicationById = async (codNacion: string) => {
  const response = await axiosInstance.get(`/medications/${codNacion}`);
  return response.data;
};
