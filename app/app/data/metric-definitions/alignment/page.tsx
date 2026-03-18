import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Alignment() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/metric-definitions/alignment" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Alignment Metrics' };
