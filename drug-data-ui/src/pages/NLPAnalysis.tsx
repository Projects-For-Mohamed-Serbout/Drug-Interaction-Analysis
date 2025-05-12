import { useTranslation } from 'react-i18next';

const AnalisisNLP = () => {
  const { t } = useTranslation();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">{t('analisisNLP.title')}</h1>
    </div>
  );
};

export default AnalisisNLP;