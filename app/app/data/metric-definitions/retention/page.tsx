import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Retention() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/metric-definitions/retention" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Retention Metrics' };
