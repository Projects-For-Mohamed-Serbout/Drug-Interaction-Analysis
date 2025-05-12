import { useTranslation } from 'react-i18next';

const Laboratories = () => {
  const { t } = useTranslation();

  return (
      <h1 className="text-2xl font-bold">{t('laboratorios.title')}</h1>
  );
};

export default Laboratories;