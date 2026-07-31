import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable } from '../ui/DataTable';
import type { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<Record<string, unknown>, unknown>[] = [
  { accessorKey: 'id', header: 'ID' },
];

describe('DataTable', () => {
  it('renders rows', () => {
    render(<DataTable columns={columns} data={[{ id: 1 }, { id: 2 }]} />);
    expect(screen.getByText('1')).toBeTruthy();
    expect(screen.getByText('2')).toBeTruthy();
  });

  it('shows empty state when no data', () => {
    render(<DataTable columns={columns} data={[]} />);
    expect(screen.getByText('لا توجد بيانات')).toBeTruthy();
  });

  it('shows loading state', () => {
    render(<DataTable columns={columns} data={[]} loading />);
    expect(screen.getByText('جاري التحميل...')).toBeTruthy();
  });

  it('shows error state with retry action', () => {
    const onRetry = vi.fn();
    render(<DataTable columns={columns} data={[]} error={new Error('boom')} onRetry={onRetry} />);
    expect(screen.getByText('تعذر تحميل البيانات')).toBeTruthy();
    fireEvent.click(screen.getByText('إعادة المحاولة'));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders error state without retry when handler missing', () => {
    render(<DataTable columns={columns} data={[]} error={new Error('boom')} />);
    expect(screen.getByText('تعذر تحميل البيانات')).toBeTruthy();
    expect(screen.queryByText('إعادة المحاولة')).toBeNull();
  });
});
