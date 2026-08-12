import { useState, useEffect } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { getPaymentMethods, getTransactionHistory, removePaymentMethod, setDefaultPaymentMethod } from '../services/payments';
import type { PaymentMethod, PaymentTransaction } from '../types';

export function Payments() {
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [transactions, setTransactions] = useState<PaymentTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [view, setView] = useState<'methods' | 'history'>('history');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [methodsData, txData] = await Promise.all([
        getPaymentMethods(),
        getTransactionHistory(),
      ]);
      setMethods(methodsData);
      setTransactions(txData.transactions);
    } catch {} finally {
      setIsLoading(false);
    }
  }

  async function handleRemove(id: string) {
    try {
      await removePaymentMethod(id);
      setMethods(methods.filter((m) => m.id !== id));
    } catch {}
  }

  async function handleSetDefault(id: string) {
    try {
      await setDefaultPaymentMethod(id);
      setMethods(methods.map((m) => ({ ...m, isDefault: m.id === id })));
    } catch {}
  }

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-20 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="flex items-center gap-2 mb-6">
        {(['history', 'methods'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={cn(
              'px-4 py-2 rounded-xl text-xs font-bold transition-all',
              view === v
                ? 'bg-primary-500 text-white'
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-500',
            )}
          >
            {v === 'history' ? 'سجل المعاملات' : 'طرق الدفع'}
          </button>
        ))}
      </div>

      {view === 'history' ? (
        transactions.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-sm text-neutral-500">لا توجد معاملات</p>
          </div>
        ) : (
          <div className="space-y-3">
            {transactions.map((tx) => (
              <div key={tx.id} className="bg-white dark:bg-neutral-800 rounded-2xl p-4 border border-neutral-200 dark:border-neutral-700">
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50 truncate">
                      {tx.description}
                    </p>
                    <p className="text-[10px] text-neutral-500 mt-0.5">
                      {new Date(tx.createdAt).toLocaleDateString('ar-IQ')}
                    </p>
                  </div>
                  <div className="text-left shrink-0">
                    <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50">
                      {tx.amount.toLocaleString('ar-IQ')} {tx.currency}
                    </p>
                    <span className={cn(
                      'text-[10px] font-bold',
                      tx.status === 'completed' ? 'text-success-500' :
                      tx.status === 'failed' ? 'text-danger-500' :
                      tx.status === 'refunded' ? 'text-warning-500' : 'text-neutral-400',
                    )}>
                      {tx.status === 'completed' ? 'مكتمل' : tx.status === 'failed' ? 'فشل' : tx.status === 'refunded' ? 'مسترجع' : 'قيد التنفيذ'}
                    </span>
                  </div>
                </div>
                {tx.invoiceUrl && (
                  <button
                    onClick={() => window.open(tx.invoiceUrl, '_blank')}
                    className="mt-3 text-xs font-bold text-primary-600 dark:text-primary-400"
                  >
                    عرض الفاتورة
                  </button>
                )}
              </div>
            ))}
          </div>
        )
      ) : (
        <div className="space-y-4">
          {methods.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-sm text-neutral-500">لا توجد طرق دفع</p>
            </div>
          ) : (
            methods.map((method) => (
              <div key={method.id} className="bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-neutral-100 dark:bg-neutral-700 rounded-2xl flex items-center justify-center">
                      <svg className="w-6 h-6 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <rect x="2" y="5" width="20" height="14" rx="2" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2 10h20" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-bold text-neutral-900 dark:text-neutral-50 text-sm">{method.label}</p>
                      {method.last4 && (
                        <p className="text-xs text-neutral-500">**** {method.last4}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {method.isDefault && (
                      <span className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-lg text-[9px] font-bold">
                        رئيسي
                      </span>
                    )}
                    {!method.isDefault && (
                      <>
                        <button
                          onClick={() => handleSetDefault(method.id)}
                          className="text-[10px] font-bold text-primary-600 dark:text-primary-400"
                        >
                          تعيين كرئيسي
                        </button>
                        <button
                          onClick={() => handleRemove(method.id)}
                          className="text-[10px] font-bold text-danger-500"
                        >
                          حذف
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          <Button fullWidth variant="outline">
            إضافة طريقة دفع
          </Button>
        </div>
      )}
    </div>
  );
}
