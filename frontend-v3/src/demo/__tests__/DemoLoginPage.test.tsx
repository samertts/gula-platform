import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import '@/i18n';
import { DemoLoginPage } from '@/demo/DemoLoginPage';
import { readDemoSession } from '@/demo/session';

vi.mock('@/demo/config', () => ({
  demoConfig: { enabled: true, enabledByEnv: true, expiresAt: '2099-01-01T00:00:00Z', reason: null },
}));

function renderSelector() {
  const router = createMemoryRouter(
    [
      { path: '/demo', element: <DemoLoginPage /> },
      { path: '/demo/:profile', element: <div>DASHBOARD_LOADED</div> },
      { path: '/login', element: <div>LOGIN_PAGE</div> },
    ],
    { initialEntries: ['/demo'] },
  );
  render(<RouterProvider router={router} />);
  return router;
}

describe('DemoLoginPage (demo profile selector)', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the five demo profiles based on existing roles', () => {
    renderSelector();
    expect(screen.getByRole('button', { name: /^مواطن/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^طبيب/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^موظف مختبر/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^ممرض/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^إدارة صحية/ })).toBeInTheDocument();
  });

  it('creates a demo session and navigates to the demo dashboard on selection', async () => {
    renderSelector();
    fireEvent.click(screen.getByRole('button', { name: /^طبيب/ }));
    await waitFor(() => expect(screen.getByText('DASHBOARD_LOADED')).toBeInTheDocument());
    const session = readDemoSession();
    expect(session?.demo).toBe(true);
    expect(session?.readOnly).toBe(true);
    expect(session?.profileId).toBe('doctor');
  });

  it('does not create a production credential when selecting a profile', () => {
    renderSelector();
    fireEvent.click(screen.getByRole('button', { name: /^مواطن/ }));
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
  });

  it('returns to the normal login page via the back button', async () => {
    renderSelector();
    fireEvent.click(screen.getByRole('button', { name: /رجوع/ }));
    await waitFor(() => expect(screen.getByText('LOGIN_PAGE')).toBeInTheDocument());
  });
});
