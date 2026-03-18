import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function TimeseriesMetrics() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/models/timeseries-metrics" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Timeseries Metrics' };
