'use client';

import { ReactNode, useState } from 'react';

interface TooltipProps {
  content: string;
  children: ReactNode;
  position?: 'top' | 'right' | 'bottom' | 'left';
}

export function Tooltip({ content, children, position = 'right' }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2'
  };

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className={`
          absolute z-50 px-3 py-2 text-sm font-medium text-white
          bg-gray-900 rounded-lg shadow-lg whitespace-nowrap
          ${positionClasses[position]}
          animate-in fade-in duration-200
        `}>
          {content}
          {/* Arrow */}
          <div className={`
            absolute w-2 h-2 bg-gray-900 rotate-45
            ${position === 'right' ? '-left-1 top-1/2 -translate-y-1/2' : ''}
            ${position === 'left' ? '-right-1 top-1/2 -translate-y-1/2' : ''}
            ${position === 'top' ? 'left-1/2 -translate-x-1/2 -bottom-1' : ''}
            ${position === 'bottom' ? 'left-1/2 -translate-x-1/2 -top-1' : ''}
          `} />
        </div>
      )}
    </div>
  );
}
