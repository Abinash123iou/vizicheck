import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileQuestion, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] p-4">
      <div className="max-w-md w-full bg-white rounded-lg border border-slate-200 p-8 text-center shadow-xs">
        <div className="w-14 h-14 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mx-auto mb-4">
          <FileQuestion className="w-7 h-7" />
        </div>
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">404 Error</span>
        <h1 className="text-xl font-bold text-slate-900 mt-1">Page Not Found</h1>
        <p className="text-sm text-slate-500 mt-2">
          The page or route you are looking for does not exist or may have been moved.
        </p>
        <div className="mt-6">
          <Button
            variant="primary"
            onClick={() => navigate('/', { replace: true })}
            className="w-full gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Home</span>
          </Button>
        </div>
      </div>
    </div>
  );
};

