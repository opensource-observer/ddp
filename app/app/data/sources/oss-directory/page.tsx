import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function OSSDirectory() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/sources/oss-directory" />
    </div>
  );
}
export const metadata: Metadata = { title: 'OSS Directory' };
