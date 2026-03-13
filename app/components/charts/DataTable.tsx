'use client';

interface DataTableProps {
  columns: string[];
  rows: (string | number | null)[][];
  highlightRow?: (row: (string | number | null)[]) => boolean;
}

export default function DataTable({ columns, rows, highlightRow }: DataTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {rows.map((row, i) => {
            const highlighted = highlightRow?.(row) ?? false;
            return (
              <tr key={i} className={highlighted ? 'bg-indigo-50' : 'hover:bg-gray-50'}>
                {row.map((cell, j) => (
                  <td key={j} className="px-4 py-2 text-gray-700 whitespace-nowrap">
                    {cell ?? '—'}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
