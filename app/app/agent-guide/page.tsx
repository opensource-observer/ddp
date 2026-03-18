import type { Metadata } from 'next';
import MarimoIframe from '@/components/MarimoIframe';

export default function AgentGuide() {
  return (
    <div className="h-full w-full">
      <MarimoIframe notebookName="notebooks/agent-guide" />
    </div>
  );
}
export const metadata: Metadata = { title: 'Agent Guide' };
