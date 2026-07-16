import React from 'react';
import { cn } from '../utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'elevated' | 'outlined' | 'filled' | 'flat';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const variantStyles = {
  elevated: 'bg-white dark:bg-neutral-800 shadow-md border border-neutral-200 dark:border-neutral-700',
  outlined: 'bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700',
  filled: 'bg-neutral-50 dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800',
  flat: 'bg-transparent',
};

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4 md:p-6',
  lg: 'p-6 md:p-8',
};

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'elevated', padding = 'md', className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-xl transition-shadow duration-200',
        variantStyles[variant],
        paddingStyles[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);
Card.displayName = 'Card';

export const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn('flex items-center justify-between mb-4', className)} {...props}>
      {children}
    </div>
  )
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, children, ...props }, ref) => (
    <h3 ref={ref} className={cn('text-lg font-semibold text-neutral-900 dark:text-white', className)} {...props}>
      {children}
    </h3>
  )
);
CardTitle.displayName = 'CardTitle';

export const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => (
    <p ref={ref} className={cn('text-sm text-neutral-500 dark:text-neutral-400', className)} {...props}>
      {children}
    </p>
  )
);
CardDescription.displayName = 'CardDescription';

export const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn(className)} {...props}>
      {children}
    </div>
  )
);
CardContent.displayName = 'CardContent';

export const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn('flex items-center justify-end gap-2 mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-700', className)} {...props}>
      {children}
    </div>
  )
);
CardFooter.displayName = 'CardFooter';
