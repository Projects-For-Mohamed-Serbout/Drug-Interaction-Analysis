import { useTranslation } from 'react-i18next';

const Dashboard = () => {
  const { t } = useTranslation();

  return (
    <div className="p-6 bg-background-light dark:bg-background-dark min-h-screen text-text-light dark:text-text-dark transition-colors duration-300">
      <h1 className="text-2xl font-bold mb-6">{t('dashboard.title')}</h1>
    </div>
  );
};

export default Dashboard;
