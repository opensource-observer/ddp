import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="h-full w-full flex items-center justify-center">
      <div className="flex flex-col items-center gap-4 text-center px-6">
        <h1 className="text-6xl font-bold tracking-tight text-gray-900">404</h1>
        <p className="text-gray-500 text-base">Page not found</p>
        <Link
          href="/"
          className="mt-2 inline-flex items-center gap-1.5 text-sm font-semibold text-gray-900 border border-gray-200 rounded-xl px-5 py-2.5 hover:border-gray-900 hover:bg-gray-50 transition-all duration-150"
        >
          Back to home
          <span className="text-gray-400">→</span>
        </Link>
      </div>
    </div>
  );
}
