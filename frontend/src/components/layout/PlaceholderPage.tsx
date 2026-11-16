import React from 'react';
import { PageHeader } from './PageHeader';
import { Card } from '@/components/ui/Card';
import { Layers } from 'lucide-react';

interface PlaceholderPageProps {
  title: string;
  moduleName: string;
  allowedRoles?: string[];
  description?: string;
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  title,
  moduleName,
  allowedRoles = [],
  description,
}) => {
  return (
    <div>
      <PageHeader
        title={title}
        subtitle={description || `Operational module for ${moduleName}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/' },
          { label: title },
        ]}
      />

      <Card className="flex flex-col items-center justify-center p-12 text-center border-dashed border-slate-300">
        <div className="w-12 h-12 rounded-full bg-blue-50 text-[#2563EB] flex items-center justify-center mb-4">
          <Layers className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-semibold text-slate-800">{title} Module</h2>
        <p className="mt-1 text-sm text-slate-500 max-w-md">
          This feature module is scheduled for implementation in a subsequent stage. The route, layout, and RBAC authorization are active.
        </p>

        {allowedRoles.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center justify-center gap-1.5">
            <span className="text-xs text-slate-400 font-medium">Authorized Roles:</span>
            {allowedRoles.map((role) => (
              <span
                key={role}
                className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200"
              >
                {role}
              </span>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

