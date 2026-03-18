import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Developers() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/models/developers" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Developers' };
