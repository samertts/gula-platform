import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToast, toast } from '../useToast';

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('starts with empty toasts', () => {
    const { result } = renderHook(() => useToast());
    expect(result.current.toasts).toEqual([]);
  });

  it('adds a toast', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      toast({ title: 'Test', variant: 'success' });
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]?.title).toBe('Test');
    expect(result.current.toasts[0]?.variant).toBe('success');
  });

  it('auto-dismisses after 5 seconds', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      toast({ title: 'Auto' });
    });
    expect(result.current.toasts).toHaveLength(1);

    act(() => { vi.advanceTimersByTime(5000); });
    expect(result.current.toasts).toHaveLength(0);
  });

  it('dismiss removes a toast', () => {
    const { result } = renderHook(() => useToast());
    let id = '';

    act(() => {
      id = toast({ title: 'Dismiss me' });
    });
    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      result.current.dismiss(id);
    });
    expect(result.current.toasts).toHaveLength(0);
  });

  it('handles multiple toasts', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      toast({ title: 'First' });
      toast({ title: 'Second' });
    });

    expect(result.current.toasts).toHaveLength(2);
    expect(result.current.toasts[0]?.title).toBe('First');
    expect(result.current.toasts[1]?.title).toBe('Second');
  });

  it('cleans up listener on unmount', () => {
    const first = renderHook(() => useToast());
    const second = renderHook(() => useToast());

    act(() => {
      toast({ title: 'Broadcast' });
    });
    expect(first.result.current.toasts).toHaveLength(1);
    expect(second.result.current.toasts).toHaveLength(1);

    first.unmount();

    act(() => {
      toast({ title: 'After unmount' });
    });

    expect(first.result.current.toasts).toHaveLength(1);
    expect(second.result.current.toasts).toHaveLength(2);
  });
});
