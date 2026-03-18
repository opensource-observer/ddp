import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Ecosystems() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/models/ecosystems" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Ecosystems' };
