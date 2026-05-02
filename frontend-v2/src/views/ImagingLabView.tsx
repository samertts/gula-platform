import React, { useState, useRef } from 'react';
import { 
  Upload, 
  Image as ImageIcon, 
  Trash2, 
  Download, 
  Layers,
  History,
  FileImage,
  Sparkles,
  Search,
  Plus
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { ImageEditor } from '../components/ImageEditor';
import { cn } from '../lib/utils';
import { toast } from 'sonner';

interface HistoryItem {
  id: string;
  url: string;
  timestamp: Date;
  name: string;
}

export const ImagingLabView: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setSelectedImage(reader.result as string);
        toast.success("Image uploaded successfully");
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveEditedImage = (newImageUrl: string) => {
    const newItem: HistoryItem = {
      id: Math.random().toString(36).substr(2, 9),
      url: newImageUrl,
      timestamp: new Date(),
      name: `Edited_${new Date().toLocaleTimeString()}.jpg`
    };
    setHistory([newItem, ...history]);
    setSelectedImage(newImageUrl);
    setIsEditing(false);
    toast.success("Image processed and saved to history");
  };

  const downloadImage = (url: string, filename: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 mb-2">
            <Sparkles size={18} />
            <span className="text-xs font-black uppercase tracking-[0.2em]">Imaging Intelligence</span>
          </div>
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">Diagnostic Imaging Lab</h1>
          <p className="text-slate-500 mt-2 font-medium">Professional image manipulation for medical documentation and analysis.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            accept="image/*" 
            className="hidden" 
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="px-6 py-3 bg-white border border-slate-200 text-slate-700 rounded-xl font-bold flex items-center gap-2 hover:border-indigo-300 hover:text-indigo-600 transition-all shadow-sm"
          >
            <Upload size={18} />
            UPLOAD SCAN
          </button>
          <button 
            disabled={!selectedImage}
            onClick={() => setIsEditing(true)}
            className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold flex items-center gap-2 hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 disabled:opacity-50 disabled:shadow-none"
          >
            <Layers size={18} />
            OPEN EDITOR
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Preview */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm min-h-[400px] flex flex-col">
            <div className="p-4 border-bottom border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
                  <ImageIcon size={16} />
                </div>
                <span className="text-sm font-bold text-slate-700 uppercase tracking-wider">Active Workspace</span>
              </div>
              {selectedImage && (
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => downloadImage(selectedImage, 'diagnostics-scan.jpg')}
                    className="p-2 hover:bg-slate-200 rounded-lg text-slate-500 transition-colors"
                  >
                    <Download size={18} />
                  </button>
                  <button 
                    onClick={() => setSelectedImage(null)}
                    className="p-2 hover:bg-red-50 rounded-lg text-red-500 transition-colors"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              )}
            </div>
            
            <div className="flex-1 flex items-center justify-center p-8 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:20px_20px]">
              {selectedImage ? (
                <motion.div 
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="relative group"
                >
                  <img 
                    src={selectedImage} 
                    alt="Scan Preview" 
                    className="max-h-[500px] w-auto rounded-xl shadow-2xl border-4 border-white"
                  />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-xl backdrop-blur-sm">
                    <button 
                      onClick={() => setIsEditing(true)}
                      className="px-6 py-3 bg-white text-slate-900 rounded-full font-bold shadow-xl flex items-center gap-2 transform translate-y-4 group-hover:translate-y-0 transition-all duration-300"
                    >
                      <Layers size={18} />
                      Manage Image
                    </button>
                  </div>
                </motion.div>
              ) : (
                <div className="text-center space-y-4 max-w-sm">
                  <div className="w-20 h-20 bg-slate-100 rounded-3xl flex items-center justify-center text-slate-300 mx-auto animate-pulse">
                    <ImageIcon size={40} />
                  </div>
                  <h3 className="text-xl font-bold text-slate-400">No Image Selected</h3>
                  <p className="text-slate-400 text-sm">Upload a laboratory scan, patient X-ray, or clinical photograph to begin manipulation.</p>
                  <button 
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 text-indigo-600 font-bold hover:bg-indigo-50 rounded-lg transition-all"
                  >
                    Select Local File
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Quick Analysis (Decoration) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-6 bg-slate-900 rounded-2xl text-white flex items-center gap-6">
              <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
                <Sparkles size={24} className="text-indigo-400" />
              </div>
              <div>
                <div className="text-xs font-bold text-white/50 uppercase tracking-wider mb-1">AI Contrast Check</div>
                <div className="text-lg font-bold">Optimal Range Found</div>
              </div>
            </div>
            <div className="p-6 bg-indigo-600 rounded-2xl text-white flex items-center gap-6">
              <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
                <Search size={24} />
              </div>
              <div>
                <div className="text-xs font-bold text-white/50 uppercase tracking-wider mb-1">Metadata Extraction</div>
                <div className="text-lg font-bold">Encrypted Headers</div>
              </div>
            </div>
          </div>
        </div>

        {/* History Sidebar */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm flex flex-col h-full sticky top-8">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <History size={18} className="text-slate-500" />
                <span className="text-sm font-bold text-slate-700 uppercase tracking-wider">Session History</span>
              </div>
              <span className="px-2 py-1 bg-slate-100 rounded text-[10px] font-black text-slate-500">{history.length}</span>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px]">
              {history.length > 0 ? (
                history.map((item) => (
                  <motion.div 
                    layout
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    key={item.id}
                    className="group relative flex items-center gap-3 p-3 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/30 transition-all cursor-pointer"
                    onClick={() => setSelectedImage(item.url)}
                  >
                    <div className="w-14 h-14 rounded-lg bg-slate-100 overflow-hidden border border-slate-200 flex-shrink-0">
                      <img src={item.url} alt="History thumbnail" className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-slate-700 truncate group-hover:text-indigo-600 transition-colors">{item.name}</div>
                      <div className="text-[10px] text-slate-400 mt-1 uppercase font-bold tracking-tight">{item.timestamp.toLocaleTimeString()}</div>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        downloadImage(item.url, item.name);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-2 hover:bg-white rounded-lg text-slate-500 transition-all"
                    >
                      <Download size={14} />
                    </button>
                  </motion.div>
                ))
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-8">
                  <div className="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center text-slate-300 mb-4">
                    <FileImage size={24} />
                  </div>
                  <p className="text-sm text-slate-400 font-medium italic">Your editing history will appear here once you save changes.</p>
                </div>
              )}
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 text-center">
              <button 
                onClick={() => setHistory([])}
                className="text-xs font-bold text-slate-400 hover:text-red-500 uppercase tracking-widest transition-colors"
                disabled={history.length === 0}
              >
                Clear Session History
              </button>
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {isEditing && selectedImage && (
          <ImageEditor 
            image={selectedImage}
            onSave={handleSaveEditedImage}
            onCancel={() => setIsEditing(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default ImagingLabView;
