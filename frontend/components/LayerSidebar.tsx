'use client';

import { useState } from 'react';
import { Tooltip } from './Tooltip';

interface Layer {
  id: string;
  name: string;
  icon: string;
  description: string;
  active: boolean;
  badge?: number;
  color: string;
}

interface LayerSidebarProps {
  onLayerChange: (layerId: string) => void;
}

export default function LayerSidebar({ onLayerChange }: LayerSidebarProps) {
  const [layers, setLayers] = useState<Layer[]>([
    {
      id: 'judge',
      name: 'Judge',
      icon: '🏛️',
      description: 'Mathematical proof engine',
      active: true,
      color: 'bg-blue-600'
    },
    {
      id: 'architect',
      name: 'Architect',
      icon: '🤖',
      description: 'AI code generation',
      active: false,
      color: 'bg-green-600'
    },
    {
      id: 'sentinel',
      name: 'Sentinel',
      icon: '🛡️',
      description: 'Security monitoring',
      active: false,
      badge: 3,
      color: 'bg-red-600'
    },
    {
      id: 'ghost',
      name: 'Ghost',
      icon: '🎭',
      description: 'Zero-knowledge privacy',
      active: false,
      color: 'bg-purple-600'
    },
    {
      id: 'oracle',
      name: 'Oracle',
      icon: '🔮',
      description: 'External data sources',
      active: false,
      color: 'bg-amber-600'
    }
  ]);

  const handleLayerClick = (layerId: string) => {
    setLayers(layers.map(layer => ({
      ...layer,
      active: layer.id === layerId
    })));
    onLayerChange(layerId);
  };

  return (
    <div className="w-20 bg-gray-900 border-r border-gray-800 flex flex-col items-center py-6 space-y-4">
      {/* Logo */}
      <div className="mb-4">
        <div className="text-2xl font-bold text-white">Æ</div>
      </div>

      {/* Divider */}
      <div className="w-12 h-px bg-gray-700" />

      {/* Layer Icons */}
      {layers.map((layer) => (
        <Tooltip key={layer.id} content={layer.description}>
          <button
            onClick={() => handleLayerClick(layer.id)}
            className={`
              relative w-14 h-14 rounded-xl flex items-center justify-center
              transition-all duration-200 group
              ${layer.active 
                ? `${layer.color} shadow-lg scale-110` 
                : 'bg-gray-800 hover:bg-gray-700 hover:scale-105'
              }
            `}
          >
            {/* Icon */}
            <span className="text-2xl">{layer.icon}</span>

            {/* Badge */}
            {layer.badge && layer.badge > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                {layer.badge}
              </span>
            )}

            {/* Active Indicator */}
            {layer.active && (
              <div className="absolute -left-1 top-1/2 -translate-y-1/2 w-1 h-8 bg-white rounded-r" />
            )}

            {/* Hover Effect */}
            <div className={`
              absolute inset-0 rounded-xl opacity-0 group-hover:opacity-20
              transition-opacity duration-200
              ${layer.color}
            `} />
          </button>
        </Tooltip>
      ))}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Settings */}
      <Tooltip content="Settings">
        <button className="w-14 h-14 rounded-xl bg-gray-800 hover:bg-gray-700 flex items-center justify-center transition-colors">
          <span className="text-xl">⚙️</span>
        </button>
      </Tooltip>
    </div>
  );
}
