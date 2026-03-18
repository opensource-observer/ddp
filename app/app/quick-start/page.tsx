import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function QuickStart() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/quick-start" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Quick Start' };
