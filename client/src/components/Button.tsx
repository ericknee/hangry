import type { ButtonHTMLAttributes } from "react";

const VARIANT_CLASS = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  icon: "btn-icon",
} as const;

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANT_CLASS;
}

/** Themed button. Defaults to a non-submitting primary button; `className` adds layout utilities. */
export default function Button({ variant = "primary", type = "button", className = "", ...props }: ButtonProps) {
  return <button type={type} className={`${VARIANT_CLASS[variant]} ${className}`.trim()} {...props} />;
}
