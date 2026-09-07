import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { SparklesIcon } from 'lucide-react'
import { cx } from '@/lib/utils'

export function Brand() { return <Link to="/" className="brand" aria-label="Interview Trainer home"><span className="brand__mark"><SparklesIcon size={17} /></span><span>Interview<span>Trainer</span></span></Link> }
export function AppShell({ children, className }: { children: ReactNode; className?: string }) { return <div className="app"><header className="app__header"><div className="app__header-inner"><Brand /><p className="app__status"><i />AI practice workspace</p></div></header><main className={cx('app__main', className)}>{children}</main></div> }
