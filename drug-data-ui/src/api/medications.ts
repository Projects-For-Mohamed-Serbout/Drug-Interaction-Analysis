import type { Medication } from "../interfaces";
import axiosInstance from "./axiosInstance";

export const searchMedications = async (
  query: string
): Promise<Medication[]> => {
  const response = await axiosInstance.get<Medication[]>('/medications/search', {
    params: { q: query },
  });
  return response.data;
};
