import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useTranslation } from 'react-i18next';

export function LoginPage() {
  const { t } = useTranslation();
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || t('error'));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-on-surface">{t('signIn')}</h2>
        <p className="text-sm text-on-surface-variant mt-1">{t('welcome')}</p>
      </div>
      {error && (
        <div className="p-3 rounded-lg bg-error-container text-on-error-container text-sm">{error}</div>
      )}
      <Input
        label={t('email')}
        type="email"
        id="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        autoFocus
      />
      <Input
        label={t('password')}
        type="password"
        id="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <div className="flex items-center justify-between text-sm">
        <Link to="/forgot-password" className="text-primary hover:underline">
          {t('forgotPassword')}
        </Link>
      </div>
      <Button type="submit" className="w-full" isLoading={isLoading}>
        {t('signIn')}
      </Button>
      <p className="text-center text-sm text-on-surface-variant">
        {t('createAccount')}{' '}
        <Link to="/register" className="text-primary hover:underline">{t('register')}</Link>
      </p>
    </form>
  );
}
