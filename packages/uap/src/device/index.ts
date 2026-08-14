import { create } from 'zustand';

export interface RequestDeviceOptions {
  acceptAllDevices?: boolean;
  filters?: Array<Record<string, unknown>>;
  optionalServices?: string[];
}

export interface BluetoothDevice {
  id: string;
  name?: string | null;
  gatt?: unknown;
}

export interface NDEFReader {
  scan: () => Promise<void>;
}

interface NavigatorWithBluetooth extends Navigator {
  bluetooth?: {
    requestDevice: (options: RequestDeviceOptions) => Promise<BluetoothDevice>;
  };
}

interface WindowWithNDEFReader extends Window {
  NDEFReader?: new () => NDEFReader;
}

export interface DeviceInfo {
  id: string;
  name: string;
  type: 'scanner' | 'printer' | 'camera' | 'gps' | 'bluetooth' | 'biometric' | 'nfc' | 'analyzer' | 'monitor';
  manufacturer?: string;
  model?: string;
  serial?: string;
  firmware?: string;
  connected: boolean;
  trusted: boolean;
  certificateThumbprint?: string;
  lastSeen?: number;
  battery?: number;
  health?: 'good' | 'degraded' | 'critical';
  metadata?: Record<string, unknown>;
}

interface DeviceState {
  devices: Map<string, DeviceInfo>;
  registerDevice: (device: DeviceInfo) => void;
  updateDevice: (id: string, updates: Partial<DeviceInfo>) => void;
  removeDevice: (id: string) => void;
  getDevice: (id: string) => DeviceInfo | undefined;
  getConnected: () => DeviceInfo[];
  getByType: (type: DeviceInfo['type']) => DeviceInfo[];
  isTrusted: (id: string) => boolean;
  setTrust: (id: string, trusted: boolean) => void;
}

export const useDeviceRegistry = create<DeviceState>((set, get) => ({
  devices: new Map(),

  registerDevice: (device) => {
    set((state) => {
      const next = new Map(state.devices);
      next.set(device.id, { ...device, lastSeen: Date.now() });
      return { devices: next };
    });
  },

  updateDevice: (id, updates) => {
    set((state) => {
      const next = new Map(state.devices);
      const existing = next.get(id);
      if (existing) {
        next.set(id, { ...existing, ...updates, lastSeen: Date.now() });
      }
      return { devices: next };
    });
  },

  removeDevice: (id) => {
    set((state) => {
      const next = new Map(state.devices);
      next.delete(id);
      return { devices: next };
    });
  },

  getDevice: (id) => get().devices.get(id),
  getConnected: () => Array.from(get().devices.values()).filter((d) => d.connected),
  getByType: (type) => Array.from(get().devices.values()).filter((d) => d.type === type),
  isTrusted: (id) => get().devices.get(id)?.trusted ?? false,
  setTrust: (id, trusted) => get().updateDevice(id, { trusted }),
}));

export const requestCamera = async (constraints?: MediaTrackConstraints): Promise<MediaStream> => {
  return navigator.mediaDevices.getUserMedia({
    video: constraints || { facingMode: 'environment' },
  });
};

export const requestGPS = (): Promise<GeolocationPosition> => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not available'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 30000,
    });
  });
};

export const scanBarcode = async (): Promise<string> => {
  if (typeof window === 'undefined') throw new Error('Not in browser');
  await requestCamera();
  const stream = await requestCamera();
  stream.getTracks().forEach((t) => t.stop());
  return 'barcode-data';
};

export const requestBluetooth = async (options?: RequestDeviceOptions): Promise<BluetoothDevice> => {
  const bluetooth = (navigator as NavigatorWithBluetooth).bluetooth;
  if (!bluetooth) throw new Error('Bluetooth not available');
  return bluetooth.requestDevice(options || { acceptAllDevices: true });
};

export const requestNFC = async (): Promise<NDEFReader> => {
  const nfcWindow = window as WindowWithNDEFReader;
  if (!nfcWindow.NDEFReader) throw new Error('NFC not available');
  const reader = new nfcWindow.NDEFReader();
  await reader.scan();
  return reader;
};

export const checkBiometricAvailability = async (): Promise<{
  fingerprint: boolean;
  face: boolean;
  iris: boolean;
  platform: string;
}> => {
  const platform = navigator.platform || '';
  const hasWebAuthn = typeof PublicKeyCredential !== 'undefined';
  return {
    fingerprint: hasWebAuthn && !!PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable?.() || false,
    face: platform.includes('iPhone') || platform.includes('iPad'),
    iris: false,
    platform,
  };
};

export const authenticateBiometric = async (challenge?: string): Promise<boolean> => {
  if (!window.PublicKeyCredential) return false;
  try {
    const credential = await navigator.credentials.get({
      publicKey: {
        challenge: new TextEncoder().encode(challenge || 'gula-auth'),
        rpId: window.location.hostname,
        userVerification: 'required',
        timeout: 60000,
      },
    });
    return !!credential;
  } catch {
    return false;
  }
};
