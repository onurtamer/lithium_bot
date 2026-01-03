import Link from 'next/link';
import Image from 'next/image';
import { Logo } from '@/components/shared/Logo';
import {
  Shield,
  Zap,
  Users,
  BarChart3,
  ArrowRight,
  Check,
  Star,
  ChevronRight,
  Command,
  Sparkles,
  Lock,
  Globe
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const features = [
  {
    icon: Shield,
    title: 'Gelişmiş Güvenlik',
    description: 'AutoMod, Anti-Raid, Jail sistemi ve daha fazlası ile sunucunuzu koruyun.',
    color: 'from-green-500 to-emerald-500'
  },
  {
    icon: Users,
    title: 'Topluluk Araçları',
    description: 'Seviye sistemi, çekilişler, doğum günleri ve tepki rolleri.',
    color: 'from-cyan-500 to-teal-500'
  },
  {
    icon: BarChart3,
    title: 'Detaylı Analytics',
    description: 'Sunucu aktivitesini takip edin, trendleri keşfedin.',
    color: 'from-lime-500 to-green-500'
  },
  {
    icon: Zap,
    title: 'Anında Senkronizasyon',
    description: 'Panel değişiklikleri anında bota yansır.',
    color: 'from-yellow-500 to-lime-500'
  },
];

const benefits = [
  'Sınırsız modül aktivasyonu',
  'Gerçek zamanlı dashboard',
  'Konfigürasyon versiyonlama',
  'Detaylı denetim kayıtları',
  'Öncelikli destek',
  '99.9% uptime garantisi',
];

const stats = [
  { value: '500+', label: 'Aktif Sunucu' },
  { value: '50K+', label: 'Kullanıcı' },
  { value: '99.9%', label: 'Uptime' },
  { value: '24/7', label: 'Destek' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-grid-lithium opacity-30" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] gradient-radial-lithium" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] gradient-radial-lithium opacity-50" />
      </div>

      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 glass">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Logo size="md" />

          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-sm text-muted-foreground hover:text-primary transition-colors">
              Özellikler
            </Link>
            <Link href="#benefits" className="text-sm text-muted-foreground hover:text-primary transition-colors">
              Avantajlar
            </Link>
            <Link href="/docs" className="text-sm text-muted-foreground hover:text-primary transition-colors">
              Dokümantasyon
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild className="text-muted-foreground hover:text-primary">
              <Link href="/login">Giriş Yap</Link>
            </Button>
            <Button asChild className="btn-lithium gap-2">
              <Link href="/login">
                Dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 min-h-screen flex items-center">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left - Content */}
            <div className="text-center lg:text-left">
              <Badge variant="outline" className="mb-6 px-4 py-1.5 text-sm border-primary/30 bg-primary/5 animate-neon-border">
                <Sparkles className="h-3 w-3 mr-2 text-primary" />
                Premium Discord Bot Management
              </Badge>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6 leading-tight">
                Discord Sunucunuzu
                <br />
                <span className="gradient-text-lithium glow-lithium-text">Profesyonelce Yönetin</span>
              </h1>

              <p className="text-lg text-muted-foreground max-w-xl mb-8">
                MEE6 ve Dyno kalitesinde, Türkçe destekli, kolay kullanımlı kontrol paneli.
                Moderasyon, seviye sistemi, çekilişler ve daha fazlası.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start mb-8">
                <Button size="lg" asChild className="btn-lithium gap-2 text-lg px-8 py-6">
                  <Link href="/login">
                    Ücretsiz Başla
                    <ArrowRight className="h-5 w-5" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild className="text-lg px-8 py-6 border-primary/30 hover:bg-primary/10 hover:border-primary/50">
                  <Link href="#features">
                    Özellikleri Keşfet
                  </Link>
                </Button>
              </div>

              <div className="flex items-center gap-6 justify-center lg:justify-start text-sm text-muted-foreground">
                <span className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-primary" />
                  Kredi kartı gerekmez
                </span>
                <span className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-primary" />
                  5 dakikada kurulum
                </span>
              </div>
            </div>

            {/* Right - Logo/Visual */}
            <div className="hidden lg:flex justify-center items-center">
              <div className="relative">
                {/* Atomic orbits */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-80 h-80 border border-primary/20 rounded-full animate-spin" style={{ animationDuration: '20s' }} />
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-60 h-60 border border-primary/30 rounded-full animate-spin" style={{ animationDuration: '15s', animationDirection: 'reverse' }} />
                </div>

                {/* Electrons */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-4 h-4 bg-primary rounded-full animate-pulse-glow" />
                <div className="absolute bottom-0 right-0 w-3 h-3 bg-primary rounded-full animate-pulse-glow" style={{ animationDelay: '0.5s' }} />
                <div className="absolute top-1/2 left-0 w-3 h-3 bg-primary rounded-full animate-pulse-glow" style={{ animationDelay: '1s' }} />

                {/* Center Logo */}
                <div className="relative w-48 h-48 rounded-2xl overflow-hidden glow-lithium-strong">
                  <Image
                    src="/logo.jpg"
                    alt="Lithium Bot"
                    fill
                    className="object-cover"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-border/50 glass">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl md:text-4xl font-bold gradient-text-lithium mb-1">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <Badge variant="outline" className="mb-4 border-primary/30">
              <Command className="h-3 w-3 mr-2" />
              Özellikler
            </Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Her İhtiyacınız İçin <span className="gradient-text-lithium">Güçlü Modüller</span>
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              15+ modül, 40+ komut ve sınırsız özelleştirme seçeneği ile sunucunuzu kontrol altına alın.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card
                key={feature.title}
                className="glass-card card-hover group"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <CardContent className="pt-6">
                  <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${feature.color} p-0.5 mb-4 group-hover:glow-lithium transition-all`}>
                    <div className="h-full w-full rounded-xl bg-background flex items-center justify-center">
                      <feature.icon className="h-6 w-6 text-primary" />
                    </div>
                  </div>
                  <h3 className="font-semibold text-lg mb-2 group-hover:text-primary transition-colors">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section id="benefits" className="py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent" />
        <div className="container mx-auto px-4 relative">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <Badge variant="outline" className="mb-4 border-primary/30">
                <Lock className="h-3 w-3 mr-2" />
                Avantajlar
              </Badge>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">
                Rakiplerden <span className="gradient-text-lithium">Bir Adım Önde</span>
              </h2>
              <p className="text-muted-foreground mb-8">
                Lithium, modern web teknolojileri ve Discord API&apos;nin en son özellikleri ile geliştirilmiştir.
                Kullanıcı deneyimini ön planda tutarak tasarlandı.
              </p>

              <ul className="space-y-4">
                {benefits.map((benefit, index) => (
                  <li
                    key={benefit}
                    className="flex items-center gap-3 animate-fadeIn"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center glow-lithium">
                      <Check className="h-4 w-4 text-primary" />
                    </div>
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Dashboard Preview */}
            <div className="relative">
              <div className="glass-card rounded-xl overflow-hidden">
                <div className="p-4 border-b border-border/50 flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-destructive/50" />
                  <div className="h-3 w-3 rounded-full bg-warning/50" />
                  <div className="h-3 w-3 rounded-full bg-success/50" />
                  <span className="ml-4 text-xs text-muted-foreground">lithiumbot.xyz/dashboard</span>
                </div>
                <div className="p-6 space-y-4">
                  <div className="h-8 bg-primary/10 rounded-lg w-2/3" />
                  <div className="grid grid-cols-3 gap-4">
                    <div className="aspect-square bg-primary/5 rounded-lg border border-primary/20 animate-pulse-glow" />
                    <div className="aspect-square bg-primary/5 rounded-lg border border-primary/20" />
                    <div className="aspect-square bg-primary/5 rounded-lg border border-primary/20" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-4 bg-muted rounded w-full" />
                    <div className="h-4 bg-muted rounded w-4/5" />
                    <div className="h-4 bg-muted rounded w-3/5" />
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-4 -right-4 -z-10 w-full h-full rounded-xl bg-gradient-to-br from-primary/20 to-transparent blur-xl" />
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="container mx-auto px-4">
          <Card className="relative overflow-hidden glass-card border-primary/20">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-primary/5" />
            <CardContent className="py-16 text-center relative">
              <Globe className="h-12 w-12 mx-auto mb-6 text-primary animate-pulse-glow" />
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Hemen <span className="gradient-text-lithium">Başlayın</span>
              </h2>
              <p className="text-muted-foreground max-w-xl mx-auto mb-8">
                Discord hesabınızla giriş yapın veya sunucunuzdan aldığınız anahtar ile
                saniyeler içinde sunucunuzu yönetmeye başlayın.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" asChild className="btn-lithium gap-2">
                  <Link href="/login">
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                    </svg>
                    Discord ile Giriş Yap
                    <ChevronRight className="h-5 w-5" />
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-12 glass">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <Logo size="sm" showText={true} />
            </div>

            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <Link href="#features" className="hover:text-primary transition-colors">Özellikler</Link>
              <Link href="/docs" className="hover:text-primary transition-colors">Dokümantasyon</Link>
              <Link href="/privacy" className="hover:text-primary transition-colors">Gizlilik</Link>
              <Link href="/terms" className="hover:text-primary transition-colors">Kullanım Koşulları</Link>
            </div>

            <p className="text-sm text-muted-foreground">
              © 2026 Lithium. Tüm hakları saklıdır.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
