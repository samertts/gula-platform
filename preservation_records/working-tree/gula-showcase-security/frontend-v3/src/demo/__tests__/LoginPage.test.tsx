import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import '@/i18n';
import { LoginPage } from '@/pages/auth/LoginPage';
import { AuthProvider } from '@/contexts/AuthContext';

const mockState = vi.hoisted(() => ({ enabled: false }));

vi.mock('@/demo/control', () => ({
  getShowcaseControl: () => ({
    enabled: mockState.enabled,
    killSwitch: false,
    expiresAt: null,
    disableReason: mockState.enabled ? null : 'disabled_by_config',
    configVersion: 'showcase-control-v1',
    checkedAt: '2026-08-10T00:00:00.000Z',
  }),
}));

function renderLoginPage() {
  const router = createMemoryRouter(
    [
      { path: '/login', element: <LoginPage /> },
      { path: '/demo', element: <div>DEMO_SELECTOR</div> },
    ],
    { initialEntries: ['/login'] },
  );
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  );
}

describe('LoginPage demo entry point', () => {
  beforeEach(() => {
    mockState.enabled = false;
  });

  it('renders the demo entry button when demo mode is enabled by config', () => {
    mockState.enabled = true;
    renderLoginPage();
    expect(screen.getByRole('button', { name: /الدخول التجريبي/ })).toBeInTheDocument();
  });

  it('renders the demo entry button disabled when demo mode is off', () => {
    renderLoginPage();
    expect(screen.getByRole('button', { name: /الدخول التجريبي/ })).toBeDisabled();
  });

  it('does not replace the production login form', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/البريد الإلكتروني/)).toBeInTheDocument();
    expect(screen.getByLabelText(/كلمة المرور/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'تسجيل الدخول' })).toBeInTheDocument();
  });

  it('navigates to the demo selector when the enabled demo button is clicked', async () => {
    mockState.enabled = true;
    renderLoginPage();
    fireEvent.click(screen.getByRole('button', { name: /الدخول التجريبي/ }));
    await waitFor(() => expect(screen.getByText('DEMO_SELECTOR')).toBeInTheDocument());
  });
});
