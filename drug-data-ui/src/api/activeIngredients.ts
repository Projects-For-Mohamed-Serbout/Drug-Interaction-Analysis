import axiosInstance from "./axiosInstance";

export const getActiveIngredients = async (
  page: number = 1,
  pageSize: number = 20,
  search?: string
) => {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (search) params.search = search;
  const response = await axiosInstance.get("/active-ingredients", { params });
  return response.data;
};
