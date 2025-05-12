import { useTranslation } from 'react-i18next';

const DBPerformance = () => {
  const { t } = useTranslation();

  return (
      <h1 className="text-2xl font-bold">{t('DBPerformance.title')}</h1>
  );
};

export default DBPerformance;