import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Events() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/models/events" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Events' };
