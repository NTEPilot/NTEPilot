import type { DetailedHTMLProps, HTMLAttributes } from 'react';

type MaterialElementProps<T extends HTMLElement = HTMLElement> = DetailedHTMLProps<HTMLAttributes<T>, T> & {
  activeTabIndex?: number;
  autoFocus?: boolean;
  checked?: boolean;
  disabled?: boolean;
  hasIcon?: boolean;
  icons?: boolean;
  label?: string;
  max?: string | number;
  min?: string | number;
  selected?: boolean;
  showOnlySelectedIcon?: boolean;
  step?: string | number;
  supportingText?: string;
  trailingIcon?: boolean;
  type?: string;
  value?: string;
};

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      'md-dialog': MaterialElementProps;
      'md-divider': MaterialElementProps;
      'md-elevated-button': MaterialElementProps;
      'md-filled-button': MaterialElementProps;
      'md-filled-tonal-button': MaterialElementProps;
      'md-icon-button': MaterialElementProps;
      'md-list': MaterialElementProps;
      'md-list-item': MaterialElementProps;
      'md-outlined-button': MaterialElementProps;
      'md-outlined-icon-button': MaterialElementProps;
      'md-outlined-text-field': MaterialElementProps;
      'md-primary-tab': MaterialElementProps;
      'md-switch': MaterialElementProps;
      'md-tabs': MaterialElementProps;
      'md-text-button': MaterialElementProps;
    }
  }
}
