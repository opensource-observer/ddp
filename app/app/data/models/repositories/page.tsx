import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Repositories() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/models/repositories" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Repositories' };
