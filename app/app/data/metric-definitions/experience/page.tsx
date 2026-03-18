import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Experience() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/metric-definitions/experience" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Experience Metrics' };
