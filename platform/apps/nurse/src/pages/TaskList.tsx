import { useEffect, useState } from 'react';
import { Select, LoadingSpinner, EmptyState } from '@gula/ui-platform';
import { TaskItem } from '../components/TaskItem';
import type { NursingTask as Task } from '@/utils/types';

const MOCK_TASKS: Task[] = [
  { id: '1', patientName: 'أحمد علي', patientId: 'P-001', bed: 'ICU-01', type: 'medication', description: 'إعطاء دواء', priority: 'urgent', status: 'pending', due: '2026-08-12T10:00:00', assignedTo: 'نور', createdAt: '2026-08-12T08:00:00' },
  { id: '2', patientName: 'مريم خالد', patientId: 'P-002', bed: 'Ward-12', type: 'vitals', description: 'قياس العلامات الحيوية', priority: 'high', status: 'in-progress', due: '2026-08-12T09:30:00', assignedTo: 'نور', createdAt: '2026-08-12T08:00:00' },
  { id: '3', patientName: 'حسن كريم', patientId: 'P-003', bed: 'Ward-08', type: 'dressing', description: 'تغيير الضماد', priority: 'medium', status: 'pending', due: '2026-08-12T11:00:00', assignedTo: 'نور', createdAt: '2026-08-12T08:00:00' },
  { id: '4', patientName: 'لمى سامر', patientId: 'P-004', bed: 'Ward-04', type: 'assessment', description: 'تحضير المريض للجراحة', priority: 'high', status: 'completed', due: '2026-08-12T08:00:00', assignedTo: 'نور', createdAt: '2026-08-12T07:00:00' },
];

export default function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    setTimeout(() => { setTasks(MOCK_TASKS); setLoading(false); }, 500);
  }, []);

  const filtered = filter === 'all' ? tasks : tasks.filter(t => t.status === filter);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">المهام التمريضية</h1>
          <p className="text-gray-500">قائمة المهام الموكلة للممرضين</p>
        </div>
        <Select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          options={[
            { value: 'all', label: 'جميع المهام' },
            { value: 'pending', label: 'معلق' },
            { value: 'in-progress', label: 'قيد التنفيذ' },
            { value: 'completed', label: 'مكتمل' },
          ]}
          className="w-40"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map(task => (
          <TaskItem key={task.id} task={task} />
        ))}
      </div>

      {filtered.length === 0 && (
        <EmptyState title="لا توجد مهام" description="لا توجد مهام تطابق معايير البحث" />
      )}
    </div>
  );
}
