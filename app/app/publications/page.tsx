import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function Publications() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/publications" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Publications' };
