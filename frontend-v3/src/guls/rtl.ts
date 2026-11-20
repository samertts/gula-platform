/**
 * GULS RTL/LTR standard.
 *
 * Components must use logical CSS properties. Numeric and medical identifiers
 * are never transformed or visually reversed by application code.
 */
export const logicalDirectionStyles = {
  marginStart: 'margin-inline-start',
  marginEnd: 'margin-inline-end',
  paddingStart: 'padding-inline-start',
  paddingEnd: 'padding-inline-end',
  insetStart: 'inset-inline-start',
  textAlignStart: 'text-align: start',
  borderStart: 'border-inline-start',
} as const;

export const FORBIDDEN_PHYSICAL_PROPERTIES = [
  'margin-left',
  'margin-right',
  'padding-left',
  'padding-right',
  'left:',
  'right:',
] as const;

export function containerAttributes(direction: 'ltr' | 'rtl', languageId: string) {
  return {
    dir: direction,
    lang: languageId,
  } as const;
}
