import { useState, useEffect } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { apiRequest } from '../services/api';
import { ConsentToggle } from '../components/ConsentToggle';
import type { Consent } from '../types';

export function ConsentManagement() {
  const [consents, setConsents] = useState<Consent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadConsents();
  }, []);

  async function loadConsents() {
    try {
      const response = await apiRequest<{ consents: Consent[] }>('/citizen/consent');
      setConsents(response.consents);
    } catch {} finally {
      setIsLoading(false);
    }
  }

  async function handleRevoke(id: string) {
    try {
      await apiRequest(`/citizen/consent/${id}/revoke`, { method: 'POST' });
      setConsents((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: 'revoked' as const } : c)),
      );
    } catch {}
  }

  async function handleExtend(id: string) {
    try {
      await apiRequest(`/citizen/consent/${id}/extend`, { method: 'POST' });
      loadConsents();
    } catch {}
  }

  const activeConsents = consents.filter((c) => c.status === 'active');
  const inactiveConsents = consents.filter((c) => c.status !== 'active');

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-40 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="bg-primary-50 dark:bg-primary-900/20 rounded-2xl p-4 border border-primary-100 dark:border-primary-800 mb-6">
        <div className="flex items-center gap-2 mb-1">
          <svg className="w-4 h-4 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <p className="text-xs font-bold text-primary-700 dark:text-primary-400">الموافقات النشطة: {activeConsents.length}</p>
        </div>
        <p className="text-[11px] text-primary-600 dark:text-primary-500">
          يمكنك التحكم في من يمكنه الوصول إلى بياناتك الصحية ومتى.
        </p>
      </div>

      {consents.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <rect x="3" y="11" width="18" height="11" rx="2" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 11V7a5 5 0 0110 0v4" />
          </svg>
          <p className="text-sm text-neutral-500 mb-2">لا توجد موافقات</p>
          <p className="text-[10px] text-neutral-400">سيتم عرض الموافقات على مشاركة البيانات هنا</p>
        </div>
      ) : (
        <div className="space-y-4">
          {activeConsents.map((consent) => (
            <ConsentToggle
              key={consent.id}
              consent={consent}
              onRevoke={handleRevoke}
              onExtend={handleExtend}
            />
          ))}
          {inactiveConsents.length > 0 && (
            <div className="mt-6">
              <h3 className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3">المنتهية والملغية</h3>
              <div className="space-y-4">
                {inactiveConsents.map((consent) => (
                  <ConsentToggle key={consent.id} consent={consent} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
