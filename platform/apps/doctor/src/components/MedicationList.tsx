import { Card, CardHeader, CardBody, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';

interface Medication {
  id: string;
  name: string;
  nameAr: string;
  strength: string;
  form: string;
  dose: string;
  frequency: string;
  route: string;
  startDate: string;
  endDate?: string;
  status: 'active' | 'discontinued' | 'completed' | 'on_hold';
  prescribedBy: string;
  instructions?: string;
  instructionsAr?: string;
}

interface MedicationListProps {
  medications: Medication[];
  title?: string;
  onSelect?: (medication: Medication) => void;
}

const statusColors: Record<string, 'success' | 'warning' | 'danger' | 'default'> = {
  active: 'success',
  completed: 'default',
  discontinued: 'danger',
  on_hold: 'warning',
};

export function MedicationList({ medications, title, onSelect }: MedicationListProps) {
  const { isRtl } = useRTL();
  const defaultTitle = isRtl ? 'الأدوية الحالية' : 'Current Medications';
  const activeMeds = medications.filter(m => m.status === 'active');
  const otherMeds = medications.filter(m => m.status !== 'active');

  return (
    <Card>
      <CardHeader title={title || defaultTitle} subtitle={isRtl ? `${activeMeds.length} أدوية نشطة` : `${activeMeds.length} active medications`} />
      <CardBody>
        {medications.length === 0 ? (
          <p className="text-sm text-neutral-500 dark:text-neutral-400 text-center py-4">
            {isRtl ? 'لا توجد أدوية حالية' : 'No current medications'}
          </p>
        ) : (
          <div className="space-y-2">
            {activeMeds.map(med => (
              <div
                key={med.id}
                onClick={() => onSelect?.(med)}
                className="p-3 rounded-xl bg-success-50 dark:bg-success-900/10 border border-success-100 dark:border-success-900/20 cursor-pointer hover:bg-success-100 dark:hover:bg-success-900/20 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-neutral-900 dark:text-neutral-50">
                      {isRtl ? med.nameAr : med.name}
                    </p>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      {med.strength} | {med.dose} {med.frequency}
                    </p>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                      {med.route} | {med.form}
                    </p>
                    {med.instructions && (
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 italic">
                        {isRtl ? med.instructionsAr : med.instructions}
                      </p>
                    )}
                  </div>
                  <Badge variant="success" size="sm">
                    {isRtl ? 'نشط' : 'Active'}
                  </Badge>
                </div>
              </div>
            ))}

            {otherMeds.map(med => (
              <div
                key={med.id}
                onClick={() => onSelect?.(med)}
                className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800 cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-neutral-700 dark:text-neutral-300">
                      {isRtl ? med.nameAr : med.name}
                    </p>
                    <p className="text-sm text-neutral-500">{med.strength}</p>
                  </div>
                  <Badge variant={statusColors[med.status]} size="sm">
                    {med.status === 'completed' ? (isRtl ? 'مكتمل' : 'Completed') :
                     med.status === 'discontinued' ? (isRtl ? 'متوقف' : 'Discontinued') :
                     med.status === 'on_hold' ? (isRtl ? 'معلق' : 'On Hold') : med.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
