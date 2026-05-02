import React, { useState, useCallback } from 'react';
import Cropper, { Area, Point } from 'react-easy-crop';
import { 
  RotateCw, 
  RotateCcw, 
  Crop as CropIcon, 
  Image as ImageIcon, 
  Eye, 
  Check, 
  X,
  Maximize,
  Minus,
  Plus,
  RefreshCw,
  Sun,
  Contrast,
  Aperture
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../lib/utils';

export interface ImageEditorProps {
  image: string;
  onSave: (editedImage: string) => void;
  onCancel: () => void;
}

const FILTERS = [
  { id: 'none', name: 'Original', filter: 'none' },
  { id: 'grayscale', name: 'Grayscale', filter: 'grayscale(100%)' },
  { id: 'sepia', name: 'Sepia', filter: 'sepia(100%)' },
  { id: 'invert', name: 'Invert', filter: 'invert(100%)' },
  { id: 'warm', name: 'Warm', filter: 'sepia(30%) saturate(140%)' },
  { id: 'cool', name: 'Cool', filter: 'hue-rotate(180deg) saturate(140%)' },
  { id: 'high-contrast', name: 'Dramatic', filter: 'contrast(150%) brightness(90%)' },
];

export const ImageEditor: React.FC<ImageEditorProps> = ({ image, onSave, onCancel }) => {
  const [crop, setCrop] = useState<Point>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [activeFilter, setActiveFilter] = useState('none');
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [isProcessing, setIsProcessing] = useState(false);

  const onCropComplete = useCallback((_croppedArea: Area, croppedAreaPixels: Area) => {
    setCroppedAreaPixels(croppedAreaPixels);
  }, []);

  const createImageUrl = async (imageSrc: string, crop: Area, rotation: number, filter: string, brightness: number, contrast: number): Promise<string> => {
    const image = new Image();
    image.src = imageSrc;
    image.crossOrigin = 'anonymous';
    
    await new Promise((resolve) => {
      image.onload = resolve;
    });

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) return '';

    const rotRad = (rotation * Math.PI) / 180;
    const { width: bWidth, height: bHeight } = getBoundingRect(image.width, image.height, rotation);

    canvas.width = bWidth;
    canvas.height = bHeight;

    ctx.translate(bWidth / 2, bHeight / 2);
    ctx.rotate(rotRad);
    ctx.translate(-image.width / 2, -image.height / 2);
    ctx.drawImage(image, 0, 0);

    const croppedCanvas = document.createElement('canvas');
    const croppedCtx = croppedCanvas.getContext('2d');

    if (!croppedCtx) return '';

    croppedCanvas.width = crop.width;
    croppedCanvas.height = crop.height;

    // Apply filters to context if supported, otherwise manually (limited)
    // CSS filter representation to Canvas Filter
    let filterString = FILTERS.find(f => f.id === activeFilter)?.filter || 'none';
    if (brightness !== 100) filterString += ` brightness(${brightness}%)`;
    if (contrast !== 100) filterString += ` contrast(${contrast}%)`;
    
    croppedCtx.filter = filterString;

    croppedCtx.drawImage(
      canvas,
      crop.x,
      crop.y,
      crop.width,
      crop.height,
      0,
      0,
      crop.width,
      crop.height
    );

    return new Promise((resolve) => {
      croppedCanvas.toBlob((blob) => {
        if (!blob) return;
        resolve(URL.createObjectURL(blob));
      }, 'image/jpeg');
    });
  };

  const getBoundingRect = (width: number, height: number, rotation: number) => {
    const rotRad = (rotation * Math.PI) / 180;
    return {
      width: Math.abs(Math.cos(rotRad) * width) + Math.abs(Math.sin(rotRad) * height),
      height: Math.abs(Math.sin(rotRad) * width) + Math.abs(Math.cos(rotRad) * height),
    };
  };

  const handleApply = async () => {
    if (!croppedAreaPixels) return;
    setIsProcessing(true);
    try {
      const result = await createImageUrl(image, croppedAreaPixels, rotation, activeFilter, brightness, contrast);
      onSave(result);
    } catch (e) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
  };

  const reset = () => {
    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setRotation(0);
    setActiveFilter('none');
    setBrightness(100);
    setContrast(100);
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[60] bg-slate-900/90 backdrop-blur-md flex flex-col items-center justify-center p-4 md:p-8"
    >
      <div className="bg-white w-full max-w-6xl h-full max-h-[90vh] rounded-2xl shadow-2xl flex flex-col md:flex-row overflow-hidden border border-slate-200">
        {/* Main Editor Area */}
        <div className="flex-1 relative bg-slate-100 flex flex-col">
          <div className="absolute top-4 left-4 z-10 flex gap-2">
            <button 
              onClick={onCancel}
              className="p-2 bg-white/80 backdrop-blur hover:bg-white rounded-full shadow-lg transition-all"
              title="Cancel"
            >
              <X size={20} className="text-slate-600" />
            </button>
            <button 
              onClick={reset}
              className="p-2 bg-white/80 backdrop-blur hover:bg-white rounded-full shadow-lg transition-all"
              title="Reset"
            >
              <RefreshCw size={20} className="text-slate-600" />
            </button>
          </div>

          <div className="flex-1 relative">
            <Cropper
              image={image}
              crop={crop}
              zoom={zoom}
              rotation={rotation}
              aspect={4 / 3}
              onCropChange={setCrop}
              onCropComplete={onCropComplete}
              onZoomChange={setZoom}
              onRotationChange={setRotation}
              style={{
                containerStyle: {
                  filter: `${FILTERS.find(f => f.id === activeFilter)?.filter || 'none'} brightness(${brightness}%) contrast(${contrast}%)`
                }
              }}
            />
          </div>

          <div className="p-4 bg-white border-t border-slate-100 flex items-center justify-center gap-6">
            <div className="flex items-center gap-4">
              <button onClick={() => setZoom(Math.max(1, zoom - 0.1))} className="p-2 hover:bg-slate-100 rounded-lg"><Minus size={18} /></button>
              <div className="w-32 h-1 bg-slate-100 rounded-full relative">
                <div 
                  className="absolute h-full bg-indigo-600 rounded-full" 
                  style={{ width: `${((zoom - 1) / 2) * 100}%` }}
                />
                <input 
                  type="range" 
                  min={1} 
                  max={3} 
                  step={0.1} 
                  value={zoom}
                  onChange={(e) => setZoom(Number(e.target.value))}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
              </div>
              <button onClick={() => setZoom(Math.min(3, zoom + 0.1))} className="p-2 hover:bg-slate-100 rounded-lg"><Plus size={18} /></button>
            </div>
            <div className="h-4 w-px bg-slate-200" />
            <div className="flex items-center gap-2">
              <button onClick={() => setRotation((prev) => (prev - 90) % 360)} className="p-2 hover:bg-slate-100 rounded-lg">
                <RotateCcw size={18} />
              </button>
              <span className="text-xs font-mono w-10 text-center">{rotation}°</span>
              <button onClick={() => setRotation((prev) => (prev + 90) % 360)} className="p-2 hover:bg-slate-100 rounded-lg">
                <RotateCw size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar Controls */}
        <div className="w-full md:w-80 bg-slate-50 border-l border-slate-200 flex flex-col p-6 overflow-y-auto">
          <div className="mb-8">
            <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2 uppercase tracking-tight">
              <Aperture size={16} className="text-indigo-600" />
              Presets & Effects
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {FILTERS.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setActiveFilter(f.id)}
                  className={cn(
                    "flex flex-col items-center gap-2 p-3 rounded-xl border transition-all truncate",
                    activeFilter === f.id 
                      ? "bg-indigo-600 border-indigo-600 text-white shadow-md shadow-indigo-200" 
                      : "bg-white border-slate-200 text-slate-600 hover:border-indigo-300"
                  )}
                >
                  <div 
                    className="w-10 h-10 rounded-lg bg-slate-200 overflow-hidden"
                    style={{ filter: f.filter }}
                  >
                    <div className="w-full h-full bg-gradient-to-br from-indigo-500 to-purple-600" />
                  </div>
                  <span className="text-[10px] font-medium uppercase tracking-wider">{f.name}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-6 flex-1">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Sun size={14} /> Brightness
                </label>
                <span className="text-[10px] font-mono text-slate-400">{brightness}%</span>
              </div>
              <input 
                type="range" 
                min={0} 
                max={200} 
                value={brightness}
                onChange={(e) => setBrightness(Number(e.target.value))}
                className="w-full h-1 bg-slate-200 rounded-full appearance-none cursor-pointer accent-indigo-600"
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Contrast size={14} /> Contrast
                </label>
                <span className="text-[10px] font-mono text-slate-400">{contrast}%</span>
              </div>
              <input 
                type="range" 
                min={0} 
                max={200} 
                value={contrast}
                onChange={(e) => setContrast(Number(e.target.value))}
                className="w-full h-1 bg-slate-200 rounded-full appearance-none cursor-pointer accent-indigo-600"
              />
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-200 flex flex-col gap-3">
            <button
              onClick={handleApply}
              disabled={isProcessing}
              className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-100 transition-all disabled:opacity-50"
            >
              {isProcessing ? (
                <RefreshCw size={20} className="animate-spin" />
              ) : (
                <>
                  <Check size={20} />
                  CONFIRM CHANGES
                </>
              )}
            </button>
            <button
              onClick={onCancel}
              className="w-full py-3 text-slate-500 hover:text-slate-800 text-sm font-medium transition-colors"
            >
              Cancel Edit
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
