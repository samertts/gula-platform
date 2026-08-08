import { useState, useEffect } from 'react';
import { Card, Button, Select, LoadingSpinner, EmptyState, Badge } from '@gula/ui-platform';
import { useNurse } from '../contexts/NurseContext';
import { TaskItem } from '../components/TaskItem';
import { getPriorityArabic, getStatusArabic } from '../utils/routes';

interface Task {
  id: string;
  title: string;
  patientName: string;
  patientId: string;
  priority: 'low' | 'medium' | 'high' | 'urgent' | 'stat';
  status: 'pending' | 'in-progress' | 'completed' | 'cancelled';
  dueTime: string;
  assignedTo: string;
  category: string;
}

const MOCK_TASKS: Task[] = [
  { id: '1', title: 'إعطاء دواء', patientName: 'أحمد علي', patientId: 'P-001', priority: 'urgent', status: 'pending', dueTime: '10:00', assignedTo: 'نور', category: 'أدوية' },
  { id: '2', title: 'قياس العلامات الحيوية', patientName: 'مريم خالد', patientId: 'P-002', priority: 'high', status: 'in-progress', dueTime: '09:30', assignedTo: 'نور', category: 'علامات حيوية' },
  { id: '3', title: 'تغيير الضماد', patientName: 'حسن كريم', patientId: 'P-003', priority: 'medium', status: 'pending', dueTime: '11:00', assignedTo: 'نور', category: 'عناية بالجروح' },
  { id: '4', title: 'تحضير المريض للجراحة', patientName: 'لمى سامر', patientId: 'P-004', priority: 'high', status: 'completed', dueTime: '08:00', assignedTo: 'نور', category: 'تحضير' },
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
