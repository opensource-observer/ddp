'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';

const CAROUSEL_IMAGES = [
  '/assets/carousel-1.png',
  '/assets/carousel-2.png',
  '/assets/carousel-3.png',
  '/assets/carousel-4.png',
  '/assets/carousel-5.png',
];

function Carousel() {
  const [current, setCurrent] = useState(0);
  const [prev, setPrev] = useState<number | null>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrent((c) => {
        setPrev(c);
        return (c + 1) % CAROUSEL_IMAGES.length;
      });
    }, 3500);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      className="relative w-full rounded-xl overflow-hidden border border-gray-200 shadow-sm"
      style={{ aspectRatio: '2/1' }}
    >
      {prev !== null && (
        <Image
          key={`prev-${prev}`}
          src={CAROUSEL_IMAGES[prev]}
          alt=""
          fill
          className="object-cover animate-fadeOut"
          sizes="50vw"
        />
      )}
      <Image
        key={`cur-${current}`}
        src={CAROUSEL_IMAGES[current]}
        alt={`Screenshot ${current + 1}`}
        fill
        className="object-cover animate-fadeIn"
        sizes="50vw"
        priority
      />
      <div className="absolute bottom-3 left-0 right-0 flex justify-center">
        <div className="flex gap-2 bg-black/20 rounded-full px-2.5 py-1.5 backdrop-blur-sm">
          {CAROUSEL_IMAGES.map((_, i) => (
            <button
              key={i}
              onClick={() => { setPrev(current); setCurrent(i); }}
              aria-label={`Go to screenshot ${i + 1}`}
              className={`w-2 h-2 rounded-full transition-all ${
                i === current ? 'bg-white scale-125' : 'bg-white/50 hover:bg-white/75'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <div className="h-full w-full overflow-y-auto">
      <div className="px-5 py-8 md:px-10 md:py-10 max-w-5xl flex flex-col gap-12">

        {/* Hero */}
        <div className="flex flex-col gap-3">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900">
            Developer Data Portal
          </h1>
          <p className="text-gray-600 text-base leading-relaxed max-w-xl">
            Open-source developer analytics across Ethereum and beyond.
            Unified data from{' '}
            <a href="https://opendevdata.org/" target="_blank" rel="noopener noreferrer" className="text-gray-800 underline underline-offset-2 decoration-gray-300 hover:decoration-gray-600 transition-colors">Open Dev Data</a>,{' '}
            <a href="https://www.gharchive.org/" target="_blank" rel="noopener noreferrer" className="text-gray-800 underline underline-offset-2 decoration-gray-300 hover:decoration-gray-600 transition-colors">GitHub Archive</a>, and{' '}
            <a href="https://www.oso.xyz" target="_blank" rel="noopener noreferrer" className="text-gray-800 underline underline-offset-2 decoration-gray-300 hover:decoration-gray-600 transition-colors">OSO</a>.
            Explore it in the browser, query via a single API, or just hand it to your agent.
          </p>
        </div>

        {/* Two-column: features left, carousel right */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 items-center">
          <div className="flex flex-col gap-7">
            <div>
              <p className="text-[13px] font-semibold uppercase tracking-widest text-gray-400 mb-2">Why DDP</p>
              <h2 className="text-sm font-semibold text-gray-900 mb-1.5">Stop plumbing. Start visualizing.</h2>
              <p className="text-gray-500 text-sm leading-relaxed">
                Cross-source data pipelines are hard to build and harder to maintain.
                DDP handles the messy middle so you can go straight to doing cool things.
              </p>
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-900 mb-1.5">Open. Traceable. Forkable.</h2>
              <p className="text-gray-500 text-sm leading-relaxed">
                Every model you see here is a Python notebook — built on{' '}
                <a href="https://marimo.io/" target="_blank" rel="noopener noreferrer" className="text-gray-700 underline underline-offset-2 decoration-gray-300 hover:decoration-gray-600 transition-colors">marimo</a>
                {' '}— that you can inspect, replicate, or{' '}
                <a href="https://github.com/opensource-observer/ddp" target="_blank" rel="noopener noreferrer" className="text-gray-700 underline underline-offset-2 decoration-gray-300 hover:decoration-gray-600 transition-colors">fork</a>
                {' '}and run in your own environment.
              </p>
            </div>
          </div>
          <Carousel />
        </div>

        {/* Divider */}
        <hr className="border-gray-100" />

        {/* Get started */}
        <div className="flex flex-col gap-4">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400">Get started</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Link
              href="/quick-start"
              className="group flex flex-col gap-2 p-5 border border-gray-200 rounded-xl hover:border-gray-900 hover:bg-gray-50 transition-all duration-150"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-900">Quick Start</span>
                <span className="text-gray-400 group-hover:text-gray-900 group-hover:translate-x-0.5 transition-all duration-150">→</span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                For analysts and researchers. Run live queries against the OSO data lake directly in your browser.
              </p>
            </Link>
            <Link
              href="/agent-guide"
              className="group flex flex-col gap-2 p-5 border border-gray-200 rounded-xl hover:border-gray-900 hover:bg-gray-50 transition-all duration-150"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-900">Agent Guide</span>
                <span className="text-gray-400 group-hover:text-gray-900 group-hover:translate-x-0.5 transition-all duration-150">→</span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                For AI agents. One-prompt setup to start querying with <code className="font-mono text-gray-600">pyoso</code> in any environment.
              </p>
            </Link>
          </div>
        </div>

        {/* Ethereum Foundation */}
        <div className="flex items-center gap-2.5 self-start text-xs text-gray-400">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1920" width="16" height="16" className="shrink-0 opacity-50">
            <path d="m959.8 730.9-539.8 245.4 539.8 319.1 539.9-319.1z" opacity=".6" />
            <path d="m420.2 976.3 539.8 319.1v-564.5-650.3z" opacity=".45" />
            <path d="m960 80.6v650.3 564.5l539.8-319.1z" opacity=".8" />
            <path d="m420 1078.7 539.8 760.7v-441.8z" opacity=".45" />
            <path d="m959.8 1397.6v441.8l540.2-760.7z" opacity=".8" />
          </svg>
          <span>
            Sponsored by the{' '}
            <a
              href="https://ethereum.foundation"
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 decoration-gray-300 hover:text-gray-600 hover:decoration-gray-500 transition-colors"
            >
              Ethereum Foundation
            </a>
          </span>
        </div>

      </div>
    </div>
  );
}
