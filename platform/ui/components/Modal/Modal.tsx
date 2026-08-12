import { useEffect, useRef, type ReactNode, type MouseEvent, useCallback } from 'react';
import { cn } from '../../utils/cn';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

export interface ModalProps {
  open?: boolean;
  isOpen?: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: ModalSize;
  closeOnOverlay?: boolean;
  closeOnEsc?: boolean;
  showCloseButton?: boolean;
  className?: string;
}

const sizeStyles: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-3xl',
};

export function Modal({
  open,
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  size = 'md',
  closeOnOverlay = true,
  closeOnEsc = true,
  showCloseButton = true,
  className,
}: ModalProps) {
  const visible = open ?? isOpen ?? false;
  const overlayRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<Element | null>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (closeOnEsc && e.key === 'Escape') onClose();
      if (e.key === 'Tab' && contentRef.current) {
        const focusable = contentRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [closeOnEsc, onClose],
  );

  useEffect(() => {
    if (visible) {
      previousActiveElement.current = document.activeElement;
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', handleKeyDown);
      setTimeout(() => contentRef.current?.focus(), 50);
    } else {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeyDown);
      if (previousActiveElement.current instanceof HTMLElement) {
        previousActiveElement.current.focus();
      }
    }
    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [visible, handleKeyDown]);

  const handleOverlayClick = (e: MouseEvent) => {
    if (closeOnOverlay && e.target === overlayRef.current) onClose();
  };

  if (!visible) return null;

  return (
    <div
      ref={overlayRef}
      role="dialog"
      aria-modal="true"
      aria-label={title || 'Modal'}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
    >
      <div
        ref={contentRef}
        tabIndex={-1}
        className={cn(
          'w-full bg-white dark:bg-neutral-800 rounded-3xl shadow-2xl',
          'flex flex-col max-h-[90vh]',
          'animate-in zoom-in-95 duration-200',
          sizeStyles[size],
          className,
        )}
      >
        {(title || showCloseButton) && (
          <div className="flex items-start justify-between px-6 pt-6 pb-4 border-b border-neutral-100 dark:border-neutral-700">
            <div className="min-w-0 flex-1">
              {title && (
                <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-50 truncate">
                  {title}
                </h2>
              )}
              {subtitle && (
                <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
                  {subtitle}
                </p>
              )}
            </div>
            {showCloseButton && (
              <button
                type="button"
                onClick={onClose}
                className="shrink-0 ml-4 rtl:ml-0 rtl:mr-4 p-2 rounded-xl text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
                aria-label="Close modal"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            )}
          </div>
        )}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {children}
        </div>
        {footer && (
          <div className="px-6 py-4 border-t border-neutral-100 dark:border-neutral-700 flex items-center justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
