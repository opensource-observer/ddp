import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function GitHubArchive() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/data/sources/github-archive" />
    </div>
  );
}
export const metadata: Metadata = { title: 'GitHub Archive' };
