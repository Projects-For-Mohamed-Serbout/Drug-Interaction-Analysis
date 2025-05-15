import type { MenuKey } from "./Constants";

export interface MenuItem {
  key: MenuKey;
  path: string;
  color: string;
  i18nKey: string;
}
