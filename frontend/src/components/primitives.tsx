import { forwardRef, type ButtonHTMLAttributes, type HTMLAttributes, type InputHTMLAttributes, type LabelHTMLAttributes, type TextareaHTMLAttributes } from 'react'
import { LoaderCircleIcon } from 'lucide-react'
import { cx } from '@/lib/utils'

export function Button({ className, variant = 'primary', size = 'md', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'outline'; size?: 'md' | 'lg' }) { return <button className={cx('button', `button--${variant}`, `button--${size}`, className)} {...props} /> }
export function Badge({ className, variant = 'secondary', ...props }: HTMLAttributes<HTMLSpanElement> & { variant?: 'secondary' | 'outline' }) { return <span className={cx('badge', `badge--${variant}`, className)} {...props} /> }
export function Card({ className, ...props }: HTMLAttributes<HTMLElement>) { return <section className={cx('card', className)} {...props} /> }
export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={cx('card__header', className)} {...props} /> }
export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={cx('card__content', className)} {...props} /> }
export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) { return <h2 className={cx('card__title', className)} {...props} /> }
export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) { return <p className={cx('card__description', className)} {...props} /> }
export function Alert({ className, children, variant: _variant, ...props }: HTMLAttributes<HTMLDivElement> & { variant?: 'destructive' }) { return <div role="alert" className={cx('alert', className)} {...props}>{children}</div> }
export function AlertDescription({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={cx('alert__text', className)} {...props} /> }
export function Spinner({ className }: { className?: string }) { return <LoaderCircleIcon className={cx('spinner', className)} aria-label="Loading" /> }
export function Separator({ className }: { className?: string }) { return <hr className={cx('separator', className)} /> }
export function Progress({ value, className }: { value: number; className?: string }) { return <div className={cx('progress', className)}><div className="progress__bar" style={{ width: `${Math.max(0, Math.min(value, 100))}%` }} /></div> }
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(({ className, ...props }, ref) => <input ref={ref} className={cx('input', className)} {...props} />)
Input.displayName = 'Input'
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(({ className, ...props }, ref) => <textarea ref={ref} className={cx('textarea', className)} {...props} />)
Textarea.displayName = 'Textarea'
export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) { return <label className={cx('label', className)} {...props} /> }
