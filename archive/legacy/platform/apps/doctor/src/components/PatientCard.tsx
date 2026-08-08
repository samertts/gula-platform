import { Card, CardBody, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { Patient } from '../services/patient';

interface PatientCardProps {
  patient: Patient;
  onClick?: () => void;
  compact?: boolean;
  showMpi?: boolean;
}

export function PatientCard({ patient, onClick, compact = false, showMpi = false }: PatientCardProps) {
  const { isRtl } = useRTL();

  const age = new Date().getFullYear() - new Date(patient.dateOfBirth).getFullYear();
  const genderLabel = patient.gender === 'male' ? (isRtl ? 'ذكر' : 'Male') : (isRtl ? 'أنثى' : 'Female');

  const criticalAllergies = patient.allergies?.filter(a => a.severity === 'severe') || [];

  return (
    <Card
      hover
      padding={compact ? 'sm' : 'md'}
      onClick={onClick}
      className={onClick ? 'cursor-pointer' : ''}
    >
      <CardBody>
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-bold text-lg shrink-0">
            {patient.nameAr?.charAt(0) || patient.name?.charAt(0)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-neutral-900 dark:text-neutral-50 truncate">
                {patient.nameAr || patient.name}
              </h3>
              {showMpi && patient.mpiScore && patient.mpiScore > 0.8 && (
                <Badge variant="info" size="xs">MPI</Badge>
              )}
            </div>
            <p className="text-sm text-neutral-500 dark:text-neutral-400">
              {genderLabel} / {age} {isRtl ? 'سنة' : 'years'}
            </p>
            {patient.nationalId && (
              <p className="text-xs text-neutral-400 dark:text-neutral-500 font-mono mt-0.5">
                {patient.nationalId}
              </p>
            )}
          </div>
          {!compact && (
            <div className="text-left rtl:text-right">
              {patient.bloodType && (
                <Badge variant="default" size="sm">{patient.bloodType}</Badge>
              )}
              {patient.chronicConditions?.length > 0 && (
                <p className="text-xs text-warning-600 dark:text-warning-400 mt-1">
                  {patient.chronicConditions.length} {isRtl ? 'حالة مزمنة' : 'chronic'}
                </p>
              )}
            </div>
          )}
        </div>

        {!compact && (
          <div className="mt-3 flex flex-wrap gap-2">
            {criticalAllergies.length > 0 && (
              <Badge variant="danger" size="sm">
                {isRtl ? 'حساسية شديدة' : 'Severe Allergy'} {criticalAllergies.length > 1 ? `(${criticalAllergies.length})` : ''}
              </Badge>
            )}
            {patient.chronicConditions?.slice(0, 2).map(cond => (
              <Badge key={cond} variant="warning" size="sm">{cond}</Badge>
            ))}
          </div>
        )}

        {compact && criticalAllergies.length > 0 && (
          <div className="mt-2">
            <Badge variant="danger" size="xs">
              {isRtl ? 'حساسية' : 'Allergy'}!
            </Badge>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
