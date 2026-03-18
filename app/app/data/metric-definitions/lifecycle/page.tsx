import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Lifecycle() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/metric-definitions/lifecycle" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Lifecycle Metrics' };
