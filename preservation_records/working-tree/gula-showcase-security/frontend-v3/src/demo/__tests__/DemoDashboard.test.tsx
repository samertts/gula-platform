import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import '@/i18n';
import { DemoLayout } from '@/demo/DemoLayout';
import { DemoDashboardPage } from '@/demo/DemoDashboardPage';
import { enterDemo, isDemoSessionActive } from '@/demo/session';
import type { DemoProfileId } from '@/demo/profiles';

vi.mock('@/demo/control', () => ({
  getShowcaseControl: () => ({
    enabled: true,
    killSwitch: false,
    expiresAt: '2099-01-01T00:00:00Z',
    disableReason: null,
    configVersion: 'showcase-control-v1',
    checkedAt: '2026-08-10T00:00:00.000Z',
  }),
}));

function renderDashboard(profile: DemoProfileId) {
  const router = createMemoryRouter(
    [
      {
        path: '/demo/:profile',
        element: <DemoLayout />,
        children: [{ index: true, element: <DemoDashboardPage /> }],
      },
      { path: '/login', element: <div>LOGIN_PAGE</div> },
      { path: '/demo', element: <div>SELECTOR_PAGE</div> },
    ],
    { initialEntries: [`/demo/${profile}`] },
  );
  render(<RouterProvider router={router} />);
  return router;
}

const ENABLED = {
  enabled: true,
  killSwitch: false,
  expiresAt: '2099-01-01T00:00:00Z',
  disableReason: null as string | null,
  configVersion: 'showcase-control-v1',
  checkedAt: '2026-08-10T00:00:00.000Z',
};

describe('DemoLayout / DemoDashboardPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('shows a persistent DEMO banner and read-only indicators', () => {
    enterDemo('doctor', ENABLED);
    renderDashboard('doctor');
    const status = screen.getByRole('status');
    expect(status).toHaveTextContent('وضع العرض التجريبي');
    expect(screen.getAllByText('DEMO').length).toBeGreaterThan(0);
    expect(screen.getByText('قراءة فقط')).toBeInTheDocument();
  });

  it('shows only synthetic demo data for the lab profile', () => {
    enterDemo('lab_staff', ENABLED);
    renderDashboard('lab_staff');
    expect(screen.getByText('DEMO-ORD-001')).toBeInTheDocument();
    expect(screen.getByText(/عرض تجريبي للطلبات والعينات والنتائج/)).toBeInTheDocument();
    expect(screen.queryByText('مريض تجريبي 001')).not.toBeInTheDocument();
  });

  it('shows only synthetic demo data for the doctor profile', () => {
    enterDemo('doctor', ENABLED);
    renderDashboard('doctor');
    expect(screen.getByText('مريض تجريبي 001')).toBeInTheDocument();
    expect(screen.getByText(/Dr. Demo Physician/)).toBeInTheDocument();
  });

  it('does not expose mutation action buttons in demo mode', () => {
    enterDemo('doctor', ENABLED);
    renderDashboard('doctor');
    const mutationLabels = /إصدار نتيجة|اعتماد|رفض|صرف|إنشاء|تعديل|حذف|إدارة المستخدمين/;
    expect(screen.queryByRole('button', { name: mutationLabels })).toBeNull();
  });

  it('does not create a production credential during a demo session', () => {
    enterDemo('citizen', ENABLED);
    renderDashboard('citizen');
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  it('exits demo mode back to the login page and clears the session', async () => {
    enterDemo('nurse', ENABLED);
    renderDashboard('nurse');
    fireEvent.click(screen.getByRole('button', { name: /خروج من العرض التجريبي/ }));
    await waitFor(() => expect(screen.getByText('LOGIN_PAGE')).toBeInTheDocument());
    expect(isDemoSessionActive()).toBe(false);
  });

  it('redirects to the selector when the URL profile does not match the session', async () => {
    enterDemo('doctor', ENABLED);
    renderDashboard('citizen');
    await waitFor(() => expect(screen.getByText('SELECTOR_PAGE')).toBeInTheDocument());
  });
});
