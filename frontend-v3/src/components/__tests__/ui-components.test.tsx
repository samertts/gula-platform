import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../ui/Card';
import { Dialog } from '../ui/Dialog';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';

describe('Badge', () => {
  it('renders children', () => {
    render(<Badge>نشط</Badge>);
    expect(screen.getByText('نشط')).toBeTruthy();
  });

  it('applies default variant classes', () => {
    const { container } = render(<Badge>نشط</Badge>);
    expect(container.querySelector('span')?.className).toContain('bg-primary');
  });

  it('applies variant-specific classes', () => {
    const { container } = render(<Badge variant="destructive">حرج</Badge>);
    expect(container.querySelector('span')?.className).toContain('bg-destructive');
  });

  it('merges custom className', () => {
    const { container } = render(<Badge className="custom-x">نشط</Badge>);
    expect(container.querySelector('span')?.className).toContain('custom-x');
  });
});

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>حفظ</Button>);
    expect(screen.getByRole('button', { name: 'حفظ' })).toBeTruthy();
  });

  it('fires onClick', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>حفظ</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop set', () => {
    render(<Button disabled>حفظ</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('does not fire onClick when disabled', () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>حفظ</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('applies variant and size classes', () => {
    const { container } = render(<Button variant="destructive" size="lg">حفظ</Button>);
    const cls = container.querySelector('button')?.className ?? '';
    expect(cls).toContain('bg-destructive');
    expect(cls).toContain('h-10');
  });
});

describe('Card family', () => {
  it('renders all card parts together', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>العنوان</CardTitle>
          <CardDescription>الوصف</CardDescription>
        </CardHeader>
        <CardContent>المحتوى</CardContent>
        <CardFooter>القدم</CardFooter>
      </Card>,
    );
    expect(screen.getByText('العنوان')).toBeTruthy();
    expect(screen.getByText('الوصف')).toBeTruthy();
    expect(screen.getByText('المحتوى')).toBeTruthy();
    expect(screen.getByText('القدم')).toBeTruthy();
  });

  it('CardTitle renders as heading', () => {
    render(<CardTitle>العنوان</CardTitle>);
    expect(screen.getByRole('heading', { name: 'العنوان' })).toBeTruthy();
  });

  it('merges className on Card', () => {
    const { container } = render(<Card className="extra">x</Card>);
    expect(container.firstElementChild?.className).toContain('extra');
  });
});

describe('Dialog', () => {
  const noop = () => {};

  it('does not render content when closed', () => {
    render(
      <Dialog open={false} onClose={noop}>
        <span>المحتوى المخفي</span>
      </Dialog>,
    );
    expect(screen.queryByText('المحتوى المخفي')).toBeNull();
  });

  it('renders content, title and description when open', () => {
    render(
      <Dialog open onClose={noop} title="العنوان" description="الوصف">
        <span>المحتوى الظاهر</span>
      </Dialog>,
    );
    expect(screen.getByText('المحتوى الظاهر')).toBeTruthy();
    expect(screen.getByText('العنوان')).toBeTruthy();
    expect(screen.getByText('الوصف')).toBeTruthy();
  });

  it('calls onClose on Escape key', () => {
    const onClose = vi.fn();
    render(
      <Dialog open onClose={onClose}>
        <span>المحتوى</span>
      </Dialog>,
    );
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when overlay clicked', () => {
    const onClose = vi.fn();
    const { container } = render(
      <Dialog open onClose={onClose}>
        <span>المحتوى</span>
      </Dialog>,
    );
    fireEvent.click(container.firstElementChild as HTMLElement);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe('Input', () => {
  it('renders with placeholder', () => {
    render(<Input placeholder="البريد الإلكتروني" />);
    expect(screen.getByPlaceholderText('البريد الإلكتروني')).toBeTruthy();
  });

  it('updates value on change', () => {
    const onChange = vi.fn();
    render(<Input onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'abc' } });
    expect(onChange).toHaveBeenCalled();
  });

  it('passes disabled state', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });
});

describe('Select', () => {
  const options = [
    { value: 'a', label: 'خيار أ' },
    { value: 'b', label: 'خيار ب' },
  ];

  it('renders options', () => {
    render(<Select options={options} />);
    expect(screen.getByRole('combobox')).toBeTruthy();
    expect(screen.getByText('خيار أ')).toBeTruthy();
    expect(screen.getByText('خيار ب')).toBeTruthy();
  });

  it('fires change with selected value', () => {
    const onChange = vi.fn();
    render(<Select options={options} onChange={onChange} />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'b' } });
    expect(onChange).toHaveBeenCalled();
  });

  it('shows error text', () => {
    render(<Select options={options} error="حقل مطلوب" />);
    expect(screen.getByText('حقل مطلوب')).toBeTruthy();
  });
});

describe('Textarea', () => {
  it('renders with placeholder', () => {
    render(<Textarea placeholder="الملاحظات" />);
    expect(screen.getByPlaceholderText('الملاحظات')).toBeTruthy();
  });

  it('updates value on change', () => {
    const onChange = vi.fn();
    render(<Textarea onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'note' } });
    expect(onChange).toHaveBeenCalled();
  });
});
