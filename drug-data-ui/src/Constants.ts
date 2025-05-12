import {
  AiOutlineHome,
  AiOutlineSetting,
} from 'react-icons/ai';
import {
  GiPill,
  GiChemicalDrop,
  GiBrain,
  GiFactory,
} from 'react-icons/gi';
import { RiFlowChart } from 'react-icons/ri';
import { MdBarChart } from 'react-icons/md';

import type { IconType } from 'react-icons';

interface MenuItem {
  key: string;
  path: string;
  icon: IconType;
  color: string;
  i18nKey: string;
}

export const MENU_ITEMS: MenuItem[] = [
  {
    key: 'dashboard',
    path: '/',
    icon: AiOutlineHome,
    color: '#3B82F6',
    i18nKey: 'dashboard.title',
  },
  {
    key: 'medications',
    path: '/medications',
    icon: GiPill,
    color: '#10B981',
    i18nKey: 'medications.title',
  },
  {
    key: 'interactions',
    path: '/interactions',
    icon: RiFlowChart,
    color: '#F59E0B',
    i18nKey: 'interactions.title',
  },
  {
    key: 'activeIngredients',
    path: '/active-ingredients',
    icon: GiChemicalDrop,
    color: '#8B5CF6',
    i18nKey: 'activeIngredients.title',
  },
  {
    key: 'laboratories',
    path: '/laboratories',
    icon: GiFactory,
    color: '#EC4899',
    i18nKey: 'laboratories.title',
  },
  {
    key: 'databasePerformance',
    path: '/database-performance',
    icon: MdBarChart,
    color: '#F43F5E',
    i18nKey: 'databasePerformance.title',
  },
  {
    key: 'nlpAnalysis',
    path: '/nlp-analysis',
    icon: GiBrain,
    color: '#0EA5E9',
    i18nKey: 'nlpAnalysis.title',
  },
  {
    key: 'settings',
    path: '/settings',
    icon: AiOutlineSetting,
    color: '#6B7280',
    i18nKey: 'settings.title',
  },
];
