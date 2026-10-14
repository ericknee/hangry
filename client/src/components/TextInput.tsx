import type { InputHTMLAttributes } from "react";

const VARIANT_CLASS = {
  /** Stands alone with its own border. */
  boxed: "input",
  /** Borderless, for use inside a `.card` that supplies the frame. */
  bare: "w-full bg-transparent text-lg text-ink placeholder:text-muted focus:outline-none",
} as const;

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  variant?: keyof typeof VARIANT_CLASS;
}

/** Themed text input; `className` adds layout utilities such as `text-center`. */
export default function TextInput({ variant = "boxed", className = "", ...props }: TextInputProps) {
  return <input className={`${VARIANT_CLASS[variant]} ${className}`.trim()} {...props} />;
}
