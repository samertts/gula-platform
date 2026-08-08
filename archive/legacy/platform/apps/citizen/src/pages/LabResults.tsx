import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { useLabResults } from '../hooks/useHealthData';
import { ResultCard } from '../components/ResultCard';

const categories = [
  { key: 'all', label: 'الكل' },
  { key: 'blood', label: 'دم' },
  { key: 'chemistry', label: 'كيمياء' },
  { key: 'hormones', label: 'هرمونات' },
  { key: 'microbiology', label: 'ميكروبيولوجي' },
  { key: 'urinalysis', label: 'بول' },
];

export function LabResults() {
  const { data: results, isLoading, error } = useLabResults();
  const [selectedCategory, setSelectedCategory] = useState('all');

  const filtered = selectedCategory === 'all'
    ? results
    : results.filter((r) => r.category === selectedCategory);

  const criticalResults = results.filter((r) => r.flag === 'C');
  const abnormalResults = results.filter((r) => r.flag === 'H' || r.flag === 'L');

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-32 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      {criticalResults.length > 0 && (
        <div className="mb-4 p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-2xl">
          <p className="text-xs font-bold text-danger-600 dark:text-danger-400 mb-1">
            نتائج حرجة ({criticalResults.length})
          </p>
          <p className="text-[10px] text-danger-500">
            هناك نتائج مختبر تحتاج إلى عناية فورية. يرجى الاتصال بمقدم الرعاية الصحية.
          </p>
        </div>
      )}

      {abnormalResults.length > 0 && !criticalResults.length && (
        <div className="mb-4 p-4 bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 rounded-2xl">
          <p className="text-xs font-bold text-warning-600 dark:text-warning-400 mb-1">
            نتائج غير طبيعية ({abnormalResults.length})
          </p>
          <p className="text-[10px] text-warning-500">
            بعض النتائج خارج النطاق الطبيعي.
          </p>
        </div>
      )}

      <div className="flex gap-2 mb-6 overflow-x-auto pb-2 -mx-4 px-4">
        {categories.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setSelectedCategory(cat.key)}
            className={cn(
              'shrink-0 px-4 py-2 rounded-xl text-xs font-bold transition-all',
              selectedCategory === cat.key
                ? 'bg-primary-500 text-white shadow-lg shadow-primary-200 dark:shadow-primary-900/30'
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400',
            )}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <p className="text-sm text-neutral-500 mb-2">لا توجد نتائج مختبر</p>
          <p className="text-[10px] text-neutral-400">سيتم عرض نتائج المختبر هنا عند توفرها</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((result) => (
            <ResultCard key={result.id} result={result} />
          ))}
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-2xl">
          <p className="text-xs text-danger-600 dark:text-danger-400">{error}</p>
        </div>
      )}
    </div>
  );
}
