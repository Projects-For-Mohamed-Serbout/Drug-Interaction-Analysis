import type { MenuKey } from "./Constants";

export interface MenuItem {
  key: MenuKey;
  path: string;
  color: string;
  i18nKey: string;
}
export interface Medication {
  id: string;
  codigo_nacional: string;
  nombre: string;
  principio_activo: string;
  laboratorio: string;
  via_administracion: string;
  matched_by: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}