import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Activity() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/metric-definitions/activity" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Activity Metrics' };
