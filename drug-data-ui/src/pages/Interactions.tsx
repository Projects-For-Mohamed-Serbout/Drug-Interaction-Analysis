import { useTranslation } from 'react-i18next';

const Interactions = () => {
  const { t } = useTranslation();

  return (
      <h1 className="text-2xl font-bold">{t('interacciones.title')}</h1>
  );
};

export default Interactions;