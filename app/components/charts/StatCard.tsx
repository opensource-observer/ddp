interface StatCardProps {
  value: string;
  label: string;
  caption?: string;
}

export default function StatCard({ value, label, caption }: StatCardProps) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white flex flex-col gap-1 min-w-0">
      <div className="text-2xl font-bold text-gray-900 truncate">{value}</div>
      <div className="text-sm font-medium text-gray-700">{label}</div>
      {caption && <div className="text-xs text-gray-400">{caption}</div>}
    </div>
  );
}
