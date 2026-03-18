import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Commits() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/models/commits" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Commits' };
