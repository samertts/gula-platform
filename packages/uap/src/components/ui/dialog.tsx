import React, { useEffect, useRef } from 'react';
import { cn } from '../utils';
import { Button } from './button';
import { X } from 'lucide-react';

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  children: React.ReactNode;
  footer?: React.ReactNode;
  closable?: boolean;
  rtl?: boolean;
}

const sizeStyles = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-[90vw] max-h-[90vh]',
};

export const Dialog: React.FC<DialogProps> = ({
  open,
  onClose,
  title,
  description,
  size = 'md',
  children,
  footer,
  closable = true,
  rtl = false,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handler);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'dialog-title' : undefined}
    >
      <div
        ref={overlayRef}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={closable ? onClose : undefined}
      />
      <div
        className={cn(
          'relative w-full bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl',
          'max-h-[85vh] overflow-y-auto',
          'transform transition-all duration-200 scale-100 opacity-100',
          sizeStyles[size],
          rtl && 'text-right'
        )}
      >
        {(title || closable) && (
          <div className={cn('flex items-start justify-between p-6 pb-0', rtl && 'flex-row-reverse')}>
            <div className="flex-1 min-w-0">
              {title && (
                <h2 id="dialog-title" className="text-xl font-semibold text-neutral-900 dark:text-white">
                  {title}
                </h2>
              )}
              {description && (
                <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
                  {description}
                </p>
              )}
            </div>
            {closable && (
              <Button variant="ghost" size="sm" onClick={onClose} className="shrink-0 -mt-1 -mr-1" aria-label="Close">
                <X size={18} />
              </Button>
            )}
          </div>
        )}
        <div className="p-6">{children}</div>
        {footer && (
          <div className={cn('flex items-center justify-end gap-2 p-6 pt-0', rtl && 'flex-row-reverse')}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export const ConfirmDialog: React.FC<{
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'primary' | 'danger';
  loading?: boolean;
}> = ({ open, onClose, onConfirm, title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', variant = 'primary', loading }) => (
  <Dialog open={open} onClose={onClose} title={title} size="sm">
    <p className="text-neutral-600 dark:text-neutral-300">{message}</p>
    <div className="flex justify-end gap-2 mt-6">
      <Button variant="ghost" onClick={onClose}>{cancelLabel}</Button>
      <Button variant={variant === 'danger' ? 'danger' : 'primary'} onClick={onConfirm} loading={loading}>
        {confirmLabel}
      </Button>
    </div>
  </Dialog>
);
