import { useAutoAnimate } from '@formkit/auto-animate/react';

const MOTION = {
  duration: 320,
  easing: 'cubic-bezier(0.2, 0, 0, 1)',
};

export function useMotionParent<T extends Element>() {
  return useAutoAnimate<T>(MOTION);
}
