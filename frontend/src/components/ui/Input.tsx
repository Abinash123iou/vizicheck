import React, { useId, forwardRef } from 'react';
import { cn } from '@/utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leadingIcon?: React.ReactNode;
  trailingAction?: React.ReactNode;
  containerClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leadingIcon,
      trailingAction,
      containerClassName,
      id: customId,
      disabled,
      required,
      className,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = customId || generatedId;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    const hasError = Boolean(error);

    return (
      <div className={cn('w-full', containerClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold text-slate-700 mb-1.5"
          >
            {label}
            {required && <span className="text-red-500 ml-1" aria-hidden="true">*</span>}
          </label>
        )}

        <div className="relative flex items-center">
          {leadingIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              {leadingIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            required={required}
            disabled={disabled}
            aria-invalid={hasError ? 'true' : undefined}
            aria-describedby={
              hasError ? errorId : helperText ? helperId : undefined
            }
            className={cn(
              'w-full rounded-md border text-sm text-slate-900 bg-white placeholder-slate-400 transition-colors',
              'py-2.5',
              leadingIcon ? 'pl-10' : 'pl-3.5',
              trailingAction ? 'pr-10' : 'pr-3.5',
              hasError
                ? 'border-red-500 text-red-900 focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:outline-none'
                : 'border-slate-300 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20 focus:outline-none',
              disabled && 'bg-slate-50 text-slate-500 cursor-not-allowed border-slate-200',
              className
            )}
            {...props}
          />

          {trailingAction && (
            <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center">
              {trailingAction}
            </div>
          )}
        </div>

        {hasError && (
          <p id={errorId} role="alert" className="mt-1.5 text-xs font-medium text-red-600">
            {error}
          </p>
        )}

        {!hasError && helperText && (
          <p id={helperId} className="mt-1.5 text-xs text-slate-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

