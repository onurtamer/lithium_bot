import Image from 'next/image';
import Link from 'next/link';

interface LogoProps {
    size?: 'sm' | 'md' | 'lg' | 'xl';
    showText?: boolean;
    animated?: boolean;
    className?: string;
}

const sizes = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
};

export function Logo({
    size = 'md',
    showText = true,
    animated = false,
    className = ''
}: LogoProps) {
    return (
        <Link href="/" className={`flex items-center gap-3 group ${className}`}>
            <div className={`relative ${sizes[size]} rounded-xl overflow-hidden ${animated ? 'glow-lithium-strong' : 'glow-lithium'} group-hover:scale-105 transition-transform`}>
                <Image
                    src="/logo.jpg"
                    alt="Lithium"
                    fill
                    className="object-cover"
                />
            </div>
            {showText && (
                <span className="font-bold text-xl gradient-text-lithium">Lithium</span>
            )}
        </Link>
    );
}
