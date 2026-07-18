import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@gula/ui-platform';
import { X, MapPin } from 'lucide-react';
import type { RegionData } from '../services/api';

const riskConfig = {
  low: { fill: 'fill-emerald-500/30', stroke: 'stroke-emerald-400', pulse: 'bg-emerald-400' },
  moderate: { fill: 'fill-amber-500/30', stroke: 'stroke-amber-400', pulse: 'bg-amber-400' },
  high: { fill: 'fill-rose-500/30', stroke: 'stroke-rose-400', pulse: 'bg-rose-400' },
  critical: { fill: 'fill-red-600/40', stroke: 'stroke-red-500', pulse: 'bg-red-500' },
};

const governorates = [
  { id: 'baghdad', name: 'بغداد', nameEn: 'Baghdad', path: 'M380,280 Q400,260 420,280 L430,320 Q410,340 390,330 Z', x: 405, y: 310 },
  { id: 'basrah', name: 'البصرة', nameEn: 'Basrah', path: 'M350,480 Q370,470 390,480 L400,520 Q380,540 360,530 Z', x: 375, y: 510 },
  { id: 'nineveh', name: 'نينوى', nameEn: 'Nineveh', path: 'M300,120 Q330,100 360,120 L370,160 Q340,180 310,170 Z', x: 335, y: 150 },
  { id: 'erbil', name: 'أربيل', nameEn: 'Erbil', path: 'M400,90 Q430,80 450,100 L440,140 Q410,150 390,140 Z', x: 420, y: 120 },
  { id: 'sulaymaniyah', name: 'السليمانية', nameEn: 'Sulaymaniyah', path: 'M460,110 Q490,100 510,120 L500,160 Q470,170 450,160 Z', x: 480, y: 145 },
  { id: 'duhok', name: 'دهوك', nameEn: 'Duhok', path: 'M350,70 Q370,60 390,70 L380,100 Q360,110 340,100 Z', x: 365, y: 90 },
  { id: 'kirkuk', name: 'كركوك', nameEn: 'Kirkuk', path: 'M420,180 Q440,170 460,180 L450,210 Q430,220 410,210 Z', x: 435, y: 200 },
  { id: 'najaf', name: 'النجف', nameEn: 'Najaf', path: 'M340,350 Q360,340 380,350 L370,390 Q350,400 330,390 Z', x: 355, y: 375 },
  { id: 'karbala', name: 'كربلاء', nameEn: 'Karbala', path: 'M320,290 Q340,280 360,290 L350,330 Q330,340 310,330 Z', x: 335, y: 315 },
  { id: 'wasit', name: 'واسط', nameEn: 'Wasit', path: 'M410,320 Q430,310 450,320 L440,360 Q420,370 400,360 Z', x: 425, y: 345 },
  { id: 'maysan', name: 'ميسان', nameEn: 'Maysan', path: 'M430,400 Q450,390 470,400 L460,440 Q440,450 420,440 Z', x: 445, y: 425 },
  { id: 'dhiqar', name: 'ذي قار', nameEn: 'Dhi Qar', path: 'M380,410 Q400,400 420,410 L410,450 Q390,460 370,450 Z', x: 395, y: 435 },
  { id: 'babil', name: 'بابل', nameEn: 'Babil', path: 'M360,250 Q380,240 400,250 L390,290 Q370,300 350,290 Z', x: 375, y: 275 },
  { id: 'diyala', name: 'ديالى', nameEn: 'Diyala', path: 'M440,190 Q460,180 480,190 L470,230 Q450,240 430,230 Z', x: 455, y: 215 },
  { id: 'anbar', name: 'الأنبار', nameEn: 'Anbar', path: 'M200,200 Q250,180 300,200 L290,260 Q240,280 190,260 Z', x: 245, y: 240 },
  { id: 'saladin', name: 'صلاح الدين', nameEn: 'Saladin', path: 'M360,180 Q390,170 410,180 L400,220 Q370,230 350,220 Z', x: 380, y: 205 },
  { id: 'muthanna', name: 'المثنى', nameEn: 'Muthanna', path: 'M330,420 Q360,410 380,420 L370,460 Q340,470 320,460 Z', x: 350, y: 445 },
  { id: 'qadisiyah', name: 'القادسية', nameEn: 'Al-Qadisiyah', path: 'M310,330 Q330,320 350,330 L340,370 Q320,380 300,370 Z', x: 325, y: 355 },
];

interface MapViewProps {
  regions: RegionData[];
  selectedRegion?: string | null;
  onRegionSelect?: (region: RegionData) => void;
  className?: string;
}

export function MapView({ regions, selectedRegion, onRegionSelect, className }: MapViewProps) {
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);
  const regionMap = new Map(regions.map(r => [r.governorate.toLowerCase(), r]));

  return (
    <div className={cn('relative', className)}>
      <svg viewBox="150 50 400 520" className="w-full h-full" role="img" aria-label="خريطة محافظات العراق">
        {governorates.map(gov => {
          const regionData = regionMap.get(gov.id);
          const risk = regionData?.riskLevel || 'low';
          const config = riskConfig[risk];
          const isActive = selectedRegion === gov.nameEn || hoveredRegion === gov.id;
          const isHovered = hoveredRegion === gov.id;

          return (
            <g
              key={gov.id}
              onMouseEnter={() => setHoveredRegion(gov.id)}
              onMouseLeave={() => setHoveredRegion(null)}
              onClick={() => regionData && onRegionSelect?.(regionData)}
              className="cursor-pointer"
            >
              <path
                d={gov.path}
                className={cn(
                  config.fill, config.stroke,
                  'stroke-2 transition-all duration-300',
                  isHovered && 'stroke-3 brightness-125',
                )}
                style={{ filter: isActive ? 'drop-shadow(0 0 8px rgba(99,102,241,0.5))' : undefined }}
              />
              <text
                x={gov.x}
                y={gov.y}
                textAnchor="middle"
                className={cn(
                  'text-[8px] font-bold fill-slate-300 pointer-events-none transition-opacity',
                  isHovered ? 'opacity-100' : 'opacity-60',
                )}
              >
                {gov.name}
              </text>
            </g>
          );
        })}
      </svg>

      <AnimatePresence>
        {hoveredRegion && regionMap.get(hoveredRegion) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-4 right-4 p-4 bg-slate-900/95 backdrop-blur-xl rounded-xl border border-white/10 shadow-2xl"
          >
            <p className="text-xs font-bold text-white">{regionMap.get(hoveredRegion)?.nameAr}</p>
            <div className="text-[10px] text-slate-400 mt-1 space-y-0.5">
              <p>عدد الحالات: {regionMap.get(hoveredRegion)?.casesToday}</p>
              <p>نسبة التطعيم: {regionMap.get(hoveredRegion)?.vaccinationRate}%</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
