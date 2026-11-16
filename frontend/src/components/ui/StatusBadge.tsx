import React from 'react';
import { cn } from '@/utils/cn';

export type BadgeVariant = 
  | 'APPROVED' 
  | 'PENDING' 
  | 'REJECTED' 
  | 'CHECKED_IN' 
  | 'CHECKED_OUT' 
  | 'CANCELLED' 
  | 'ACTIVE' 
  | 'BLACKLISTED' 
  | 'COMPLETED';

interface StatusBadgeProps {
  status: BadgeVariant | string;
  className?: string;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className, label }) => {
  const normalized = status.toUpperCase();
  const displayLabel = label || normalized.replace('_', ' ');

  const getVariantStyles = (): string => {
    switch (normalized) {
      case 'APPROVED':
      case 'ACTIVE':
      case 'CHECKED_IN':
        return 'bg-green-50 text-brand-success border-green-200';

      case 'PENDING':
        return 'bg-amber-50 text-brand-warning border-amber-200';

      case 'REJECTED':
      case 'BLACKLISTED':
      case 'CANCELLED':
        return 'bg-red-50 text-brand-danger border-red-200';

      case 'CHECKED_OUT':
      case 'COMPLETED':
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border capitalize tracking-tight',
        getVariantStyles(),
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-80" />
      {displayLabel}
    </span>
  );
};

