import { useEffect, useState } from 'react';
import { Button, Select, LoadingSpinner, EmptyState } from '@gula/ui-platform';
import { TaskItem } from '../components/TaskItem';
import { tasksService } from '../services/tasks';
import type { NursingTask as Task } from '@/utils/types';

export default function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('all');

  async function loadTasks(active = true) {
    setLoading(true);
    setError(null);
    try {
      const nextTasks = await tasksService.getList();
      if (active) setTasks(nextTasks);
    } catch (cause) {
      if (active) setError(cause instanceof Error ? cause.message : 'تعذر تحميل المهام من الخادم');
    } finally {
      if (active) setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    void loadTasks(active);
    return () => {
      active = false;
    };
  }, []);

  const filtered = filter === 'all' ? tasks : tasks.filter((task) => task.status === filter);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">المهام التمريضية</h1>
          <p className="text-gray-500">قائمة المهام الموكلة للممرضين من نظام GULA</p>
        </div>
        <Select
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          options={[
            { value: 'all', label: 'جميع المهام' },
            { value: 'pending', label: 'معلق' },
            { value: 'in-progress', label: 'قيد التنفيذ' },
            { value: 'completed', label: 'مكتمل' },
          ]}
          className="w-40"
        />
      </div>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
          <span>{error}</span>
          <Button variant="outline" onClick={() => void loadTasks(true)}>إعادة المحاولة</Button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((task) => (
          <TaskItem key={task.id} task={task} />
        ))}
      </div>

      {filtered.length === 0 && !error && (
        <EmptyState title="لا توجد مهام" description="لا توجد مهام مسجلة أو لا توجد مهام تطابق معايير البحث" />
      )}
    </div>
  );
}
